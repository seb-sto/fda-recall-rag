from dotenv import load_dotenv
from fastapi import FastAPI
from src.api.schemas import DocumentCounts, QueryRequest, QueryResponse, SourceChunk
from src.embedding.store import get_client
from src.rag.generate import generate_answer
from src.rag.retrieve import ALL_COLLECTIONS, retrieve

load_dotenv()

app = FastAPI(title="FDA Recall RAG")

SOURCE_TYPE_TO_COLLECTION = {
    "regulation": "regulations",
    "food": "food_recalls",
    "drug": "drug_recalls",
    "device": "device_recalls",
}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    collection_names = ALL_COLLECTIONS
    where = None
    fetch_n = request.n_results

    if request.filters:
        if request.filters.source_type:
            collection_names = [SOURCE_TYPE_TO_COLLECTION[request.filters.source_type]]
        if request.filters.cfr_part:
            where = {"cfr_part": request.filters.cfr_part}
        if request.filters.state:
            fetch_n = request.n_results * 5  # over-fetch; state is filtered after retrieval

    chunks = retrieve(
        request.question,
        collection_names=collection_names,
        n_results=fetch_n,
        where=where,
    )

    if request.filters and request.filters.state:
        state = request.filters.state.upper()
        chunks = [
            c for c in chunks
            if state in c["metadata"].get("distribution_pattern", "").upper()
        ][: request.n_results]

    answer = generate_answer(request.question, chunks)
    return QueryResponse(answer=answer, sources=[SourceChunk(**c) for c in chunks])


@app.get("/documents", response_model=DocumentCounts)
def documents() -> DocumentCounts:
    client = get_client()
    counts = {name: client.get_collection(name).count() for name in ALL_COLLECTIONS}
    return DocumentCounts(counts=counts)
