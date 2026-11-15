from fastapi import FastAPI

app = FastAPI(title="__NAME__")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
