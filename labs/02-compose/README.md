# Lab 02 · Docker Compose from scratch

**Why it matters:** Compose is the fastest way to prove a multi-service design before you write Kubernetes manifests.

## Task
Write `work/docker-compose.yml` for two services:
- **api**: built from your Lab 01 image (`build:` path), port 8080, env var `REDIS_HOST=cache`, secrets from an `env_file`
- **cache**: `redis` with a **pinned tag**, data in a **named volume**, and a **healthcheck**

The api must wait until cache is **healthy** (`depends_on` with `condition: service_healthy`), and both must share a **user-defined network**.

Also create `work/.env` with one fake value (never real secrets, and `.env` stays out of Git).

## Check
```
make lab-check LAB=02
docker compose -f labs/02-compose/work/docker-compose.yml config   # validates syntax
```

## Think about
- What happens to the data when you run `docker compose down`? And `down -v`?
- Why is `depends_on` alone not enough?

## Stretch
Add a second network so only the api can reach `cache`, and publish only the api's port.
