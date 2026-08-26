import json
from src.embedding.chunk import chunk_documents
from src.embedding.embed import embed_documents
from src.embedding.store import upsert_chunks

SOURCES = [
    ("data/processed/regulations.jsonl", "regulations"),
    ("data/processed/food_recalls.jsonl", "food_recalls"),
    ("data/processed/drug_recalls.jsonl", "drug_recalls"),
    ("data/processed/device_recalls.jsonl", "device_recalls"),
]

def main():
    for path, collection_name in SOURCES:
        docs = [json.loads(line) for line in open(path)]
        chunks = chunk_documents(docs)
        chunks = embed_documents(chunks)
        upsert_chunks(collection_name, chunks)
        print(f"{collection_name}: {len(chunks)} chunks upserted")

if __name__ == "__main__":
    main()
