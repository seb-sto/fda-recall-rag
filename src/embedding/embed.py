from sentence_transformers import SentenceTransformer

_model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_query(text: str) -> list[float]:
    return _model.encode([text])[0].tolist()

def embed_documents(chunks: list[dict], batch_size: int = 64) -> list[dict]:
    texts = [c["text"] for c in chunks]
    embeddings = _model.encode(texts, batch_size=batch_size, show_progress_bar=True)
    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding.tolist()
    return chunks
