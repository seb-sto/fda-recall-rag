from fastapi import FastAPI

app = FastAPI(title="FDA Recall RAG")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}