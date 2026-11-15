"""The gateway: a small, observable HTTP front door for a local LLM (Ollama).

Concepts composed here (see docs/design/traceability.md):
  RateLimit -> PromptGuard -> ResponseCache -> ModelRuntime
"""

from __future__ import annotations

import math
import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)
from pydantic import BaseModel, Field

from .cache import LRUCache, make_key
from .guard import GuardError, check_prompt
from .ratelimit import RateLimiter
from .settings import Settings


class ChatRequest(BaseModel):
    prompt: str = Field(min_length=1)
    max_tokens: int = Field(default=256, ge=1, le=1024)


class ChatResponse(BaseModel):
    response: str
    model: str
    cached: bool
    latency_ms: int


def create_app(
    settings: Settings | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> FastAPI:
    """Build the app. `transport` lets tests fake Ollama without a network."""
    settings = settings or Settings.from_env()
    client = httpx.AsyncClient(
        base_url=settings.ollama_url,
        timeout=settings.request_timeout_s,
        transport=transport,
    )
    limiter = RateLimiter(settings.rate_limit_per_min)
    cache = LRUCache(settings.cache_size)

    # A registry per app instance keeps tests independent of each other.
    registry = CollectorRegistry()
    outcomes = Counter(
        "gateway_chat_requests_total",
        "Chat requests by outcome.",
        ["outcome"],
        registry=registry,
    )
    cache_hits = Counter("gateway_cache_hits_total", "Cache hits.", registry=registry)
    cache_misses = Counter("gateway_cache_misses_total", "Cache misses.", registry=registry)
    latency = Histogram(
        "gateway_chat_seconds",
        "End-to-end chat latency in seconds.",
        buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 30, 60, 120),
        registry=registry,
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield
        await client.aclose()

    app = FastAPI(title="AI Gateway", version="0.1.0", lifespan=lifespan)

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        """Liveness: the process is up. Never checks dependencies."""
        return {"status": "ok"}

    @app.get("/readyz")
    async def readyz(response: Response) -> dict[str, object]:
        """Readiness: the model is actually available to serve traffic."""
        try:
            r = await client.get("/api/tags", timeout=3.0)
            r.raise_for_status()
            models = r.json().get("models", [])
        except (httpx.HTTPError, ValueError):
            response.status_code = 503
            return {"status": "unavailable", "reason": "ollama unreachable"}
        names = {m.get("name") for m in models} | {m.get("model") for m in models}
        wanted = {settings.model}
        if ":" not in settings.model:
            wanted.add(f"{settings.model}:latest")
        if names & wanted:
            return {"status": "ready", "model": settings.model}
        response.status_code = 503
        return {"status": "unavailable", "reason": f"model {settings.model} not pulled yet"}

    @app.get("/metrics")
    async def metrics() -> Response:
        return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)

    @app.post("/v1/chat", response_model=ChatResponse)
    async def chat(body: ChatRequest, request: Request) -> ChatResponse:
        started = time.perf_counter()
        client_key = request.client.host if request.client else "unknown"

        allowed, retry_after = limiter.allow(client_key)
        if not allowed:
            outcomes.labels("rate_limited").inc()
            raise HTTPException(
                status_code=429,
                detail={"code": "rate_limited", "message": "Too many requests."},
                headers={"Retry-After": str(max(1, math.ceil(retry_after)))},
            )

        try:
            prompt = check_prompt(body.prompt, settings.max_prompt_chars)
        except GuardError as exc:
            outcomes.labels("rejected").inc()
            raise HTTPException(
                status_code=400, detail={"code": exc.code, "message": exc.message}
            ) from exc

        key = make_key(settings.model, prompt, body.max_tokens)
        hit = cache.lookup(key)
        if hit is not None:
            cache_hits.inc()
            outcomes.labels("cached").inc()
            elapsed = time.perf_counter() - started
            latency.observe(elapsed)
            return ChatResponse(
                response=hit,
                model=settings.model,
                cached=True,
                latency_ms=int(elapsed * 1000),
            )
        cache_misses.inc()

        try:
            upstream = await client.post(
                "/api/generate",
                json={
                    "model": settings.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": body.max_tokens},
                },
            )
            upstream.raise_for_status()
            text = upstream.json()["response"]
        except httpx.TimeoutException as exc:
            outcomes.labels("upstream_timeout").inc()
            raise HTTPException(
                status_code=504,
                detail={"code": "upstream_timeout", "message": "Model timed out."},
            ) from exc
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            outcomes.labels("upstream_error").inc()
            raise HTTPException(
                status_code=502,
                detail={"code": "upstream_error", "message": "Model backend failed."},
            ) from exc

        cache.store(key, text)
        outcomes.labels("ok").inc()
        elapsed = time.perf_counter() - started
        latency.observe(elapsed)
        return ChatResponse(
            response=text,
            model=settings.model,
            cached=False,
            latency_ms=int(elapsed * 1000),
        )

    return app


app = create_app()
