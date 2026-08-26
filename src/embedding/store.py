import chromadb


def get_client() -> chromadb.HttpClient:
    return chromadb.HttpClient(host="localhost", port=8001)


def upsert_chunks(collection_name: str, chunks: list[dict]) -> None:
    client = get_client()
    collection = client.get_or_create_collection(collection_name)
    collection.upsert(
        ids=[c["id"] for c in chunks],
        embeddings=[c["embedding"] for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[c["metadata"] for c in chunks],
    )
