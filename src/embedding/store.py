import chromadb

def get_client() -> chromadb.HttpClient:
    return chromadb.HttpClient(host="localhost", port=8001)

def upsert_chunks(collection_name: str, chunks: list[dict]) -> None:
    client = get_client()
    collection = client.get_or_create_collection(collection_name)
    batch_size = client.get_max_batch_size()

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        collection.upsert(
            ids=[c["id"] for c in batch],
            embeddings=[c["embedding"] for c in batch],
            documents=[c["text"] for c in batch],
            metadatas=[c["metadata"] for c in batch],
        )
