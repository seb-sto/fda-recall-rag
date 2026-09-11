from dotenv import load_dotenv

load_dotenv()

from fastapi import Depends, FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.api.auth import verify_api_key
from src.api.schemas import DocumentCounts, QueryRequest, QueryResponse, SourceChunk
from src.embedding.store import get_client
from src.rag.generate import generate_answer
from src.rag.memory import add_turn, get_history
from src.rag.rerank import rerank
from src.rag.retrieve import ALL_COLLECTIONS, retrieve

app = FastAPI(title="FDA Recall RAG")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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

    chunks = retrieve(
        body.question,
        collection_names=collection_names,
        n_results=fetch_n,
        where=where,
    )

    if body.filters and body.filters.state:
        state = body.filters.state.upper()
        chunks = [
            c for c in chunks
            if state in c["metadata"].get("distribution_pattern", "").upper()
        ]

    chunks = rerank(body.question, chunks, top_k=body.n_results)

    history = get_history(body.session_id) if body.session_id else None
    answer = generate_answer(body.question, chunks, history=history)

    if body.session_id:
        add_turn(body.session_id, body.question, answer)

    return QueryResponse(answer=answer, sources=[SourceChunk(**c) for c in chunks])


@app.get("/documents", response_model=DocumentCounts, dependencies=[Depends(verify_api_key)])
def documents() -> DocumentCounts:
    client = get_client()
    counts = {name: client.get_collection(name).count() for name in ALL_COLLECTIONS}
    return DocumentCounts(counts=counts)
