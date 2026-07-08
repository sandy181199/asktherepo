from fastapi import FastAPI

app = FastAPI(title="AskTheRepo Dashboard")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
