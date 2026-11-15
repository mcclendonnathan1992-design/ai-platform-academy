# Traceability: concept → code → deployment

| Concept (Module 01) | Purpose | Real code | Where it lives at runtime |
|---|---|---|---|
| RateLimit | share model time fairly | `app/gateway/ratelimit.py` | gateway pod (per replica) · `RATE_LIMIT_PER_MIN` in `k8s/base/configmap.yaml` |
| PromptGuard | keep unsafe input from the model | `app/gateway/guard.py` | gateway pod · `MAX_PROMPT_CHARS` |
| ResponseCache | don't pay twice | `app/gateway/cache.py` | gateway pod memory (per replica) · `CACHE_SIZE` |
| ModelRuntime | prompt → text | Ollama via `app/gateway/main.py` | `k8s/base/ollama.yaml` + PVC |

## Things the system must refuse to do
- Send empty, oversized or suspicious prompts to the model.
- Cache a refused prompt.
- Serve traffic before the model is pulled (`/readyz` = 503).
- Let one client starve the others.

## Tradeoffs to write down (Module 02)
- Rate limit and cache are **per pod**: with N replicas the real limit is N × the setting, and cache hit rate drops. A shared store (Redis) fixes it but adds a dependency.
- The deny-list guard is weak by design: see `app/tests/test_guard_bypasses.py`.
