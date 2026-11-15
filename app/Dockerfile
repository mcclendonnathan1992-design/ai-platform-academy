# Module 03: containerize the gateway.
#
# Two stages: dependencies are installed in a throwaway builder image, then
# copied into a clean runtime image. Result: smaller image, no build tools,
# and no root user at runtime (Kubernetes' runAsNonRoot needs a numeric UID).

FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /srv
COPY --from=builder /install /usr/local
COPY gateway ./gateway
USER 10001:10001
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=2)"
CMD ["uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "8080"]
