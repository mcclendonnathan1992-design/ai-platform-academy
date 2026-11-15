# 03 · Containerize the gateway

**Goal:** package the gateway as a hardened image and run the stack with Compose.

## Ideas
Multi-stage builds, non-root numeric UID, `HEALTHCHECK`, liveness vs readiness, why `/readyz` waits for the model.

## Lab
1. `docker build -t ai-gateway:dev app`
2. `docker compose up -d --build` then `docker compose exec ollama ollama pull llama3.2:1b`
3. `curl localhost:8080/readyz` (503 until the model is there), then:
   `curl -X POST localhost:8080/v1/chat -H 'content-type: application/json' -d '{"prompt":"Hi"}'`
4. `docker run --rm ai-gateway:dev id` → confirm it is not root.
5. Repeat the same prompt twice; check `"cached"` and `/metrics`.

## Checkpoint
`make verify-03`

## Stretch
Shrink the image. What did you remove and what did it cost?
