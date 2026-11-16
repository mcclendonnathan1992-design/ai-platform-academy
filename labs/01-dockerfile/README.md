# Lab 01 · Write a Dockerfile from scratch

**Why it matters:** every app you deploy to AKS starts as an image. A good Dockerfile is small, reproducible, and does not run as root.

## Task
The app is in `given/` (`app.py`, `requirements.txt`). In `work/` write:
1. `Dockerfile`
2. `.dockerignore`

Copy the two given files into `work/` as your build context, then build from there:
```
cp labs/01-dockerfile/given/* labs/01-dockerfile/work/
cd labs/01-dockerfile/work && docker build -t lab01:dev . && docker run --rm -p 8080:8080 lab01:dev
```

## Your Dockerfile must
- use a **pinned** base image tag (never `latest`), and be **multi-stage**
- copy `requirements.txt` and install **before** copying the code (layer cache)
- run as a **non-root numeric user** (`USER 10001:10001`)
- declare `EXPOSE 8080` and a `HEALTHCHECK`
- use **exec form** for `CMD` (`["python", "app.py"]`)
- not use `ADD` for URLs

## Check
```
make lab-check LAB=01
```

## Think about
- Why numeric UID? (Kubernetes `runAsNonRoot` can't verify a name.)
- What is in each layer? `docker history lab01:dev`
- Reference answer: `solution/`. Write yours first.

## Stretch
Make the final image smaller. Try `python:3.12-slim` vs `python:3.12-alpine` and say what you gave up.
