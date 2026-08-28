from src.embedding.embed import embed_query
from src.embedding.store import get_client

ALL_COLLECTIONS = ["regulations", "food_recalls", "drug_recalls", "device_recalls"]


def retrieve(
    query: str,
    collection_names: list[str] = ALL_COLLECTIONS,
    n_results: int = 5,
    where: dict | None = None,
) -> list[dict]:
    client = get_client()
    query_embedding = embed_query(query)

    results = []
    for name in collection_names:
        collection = client.get_collection(name)
        res = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
        )
        for doc, meta, dist in zip(
            res["documents"][0], res["metadatas"][0], res["distances"][0]
        ):
            results.append({"text": doc, "metadata": meta, "distance": dist})

    results.sort(key=lambda r: r["distance"])
    return results[:n_results]
