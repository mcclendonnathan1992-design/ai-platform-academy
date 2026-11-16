FROM python:3.12 AS build
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim
WORKDIR /srv
COPY --from=build /install /usr/local
COPY app.py .
USER 10001
HEALTHCHECK --interval=30s CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8080/healthz')"
CMD ["python", "app.py"]
