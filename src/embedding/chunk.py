from langchain_text_splitters import RecursiveCharacterTextSplitter

def _make_chunk_id(metadata: dict, chunk_index: int) -> str:
    key = metadata.get("section_number") or metadata.get("recall_number")
    return f"{metadata['source_type']}:{key}:{chunk_index}"


def chunk_documents(
    docs: list[dict], chunk_size: int = 800, chunk_overlap: int = 100
) -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = []
    for doc in docs:
        pieces = splitter.split_text(doc["text"])
        for i, piece in enumerate(pieces):
            metadata = dict(doc["metadata"])
            metadata["chunk_index"] = i
            chunk_id = _make_chunk_id(metadata, i)
            chunks.append({"id": chunk_id, "text": piece, "metadata": metadata})
    return chunks
