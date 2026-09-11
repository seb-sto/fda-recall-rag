from dotenv import load_dotenv
import time
import uuid

from fastapi import Depends, FastAPI, Request, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
import structlog
from starlette.middleware.base import BaseHTTPMiddleware

from src.api.auth import verify_api_key
from src.api.schemas import DocumentCounts, QueryRequest, QueryResponse, SourceChunk
from src.embedding.store import get_client
from src.rag.generate import generate_answer
from src.rag.memory import add_turn, get_history
from src.rag.rerank import rerank
from src.rag.retrieve import ALL_COLLECTIONS, retrieve
from src.api.logging_config import configure_logging, logger

load_dotenv()
configure_logging()

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())
        structlog.contextvars.bind_contextvars(request_id=request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

app = FastAPI(title="FDA Recall RAG")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(RequestIDMiddleware)


SOURCE_TYPE_TO_COLLECTION = {
    "regulation": "regulations",
    "food": "food_recalls",
    "drug": "drug_recalls",
    "device": "device_recalls",
}

RERANK_CANDIDATE_MULTIPLIER = 2
MIN_RERANK_CANDIDATES = 10


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse, dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
def query(request: Request, body: QueryRequest) -> QueryResponse:
    collection_names = ALL_COLLECTIONS
    where = None
    fetch_n = max(body.n_results * RERANK_CANDIDATE_MULTIPLIER, MIN_RERANK_CANDIDATES)

    if body.filters:
        if body.filters.source_type:
            collection_names = [SOURCE_TYPE_TO_COLLECTION[body.filters.source_type]]
        if body.filters.cfr_part:
            where = {"cfr_part": body.filters.cfr_part}
        if body.filters.state:
            fetch_n *= 5

    t0 = time.perf_counter()
    chunks = retrieve(
        body.question,
        collection_names=collection_names,
        n_results=fetch_n,
        where=where,
    )
    retrieval_latency_ms = round((time.perf_counter() - t0) * 1000, 1)

    if body.filters and body.filters.state:
        state = body.filters.state.upper()
        chunks = [
            c for c in chunks
            if state in c["metadata"].get("distribution_pattern", "").upper()
        ]

    chunks = rerank(body.question, chunks, top_k=body.n_results)

    history = get_history(body.session_id) if body.session_id else None
    t0 = time.perf_counter()
    answer = generate_answer(body.question, chunks, history=history)
    generation_latency_ms = round((time.perf_counter() - t0) * 1000, 1)

    logger.info(
        "query_processed",
        question=body.question,
        filters=body.filters.model_dump() if body.filters else None,
        retrieval_latency_ms=retrieval_latency_ms,
        generation_latency_ms=generation_latency_ms,
    )

    if body.session_id:
        add_turn(body.session_id, body.question, answer)

    return QueryResponse(answer=answer, sources=[SourceChunk(**c) for c in chunks])


@app.get("/documents", response_model=DocumentCounts, dependencies=[Depends(verify_api_key)])
def documents() -> DocumentCounts:
    client = get_client()
    counts = {name: client.get_collection(name).count() for name in ALL_COLLECTIONS}
    return DocumentCounts(counts=counts)

@app.delete("/documents/{document_id}", dependencies=[Depends(verify_api_key)])
def delete_document(document_id: str) -> dict[str, str]:
    source_type = document_id.split(":", 1)[0]
    collection_name = SOURCE_TYPE_TO_COLLECTION.get(source_type)
    if not collection_name:
        raise HTTPException(status_code=404, detail="Document not found")

    client = get_client()
    collection = client.get_collection(collection_name)
    existing = collection.get(ids=[document_id])
    if not existing["ids"]:
        raise HTTPException(status_code=404, detail="Document not found")

    collection.delete(ids=[document_id])
    return {"status": "deleted", "id": document_id}

