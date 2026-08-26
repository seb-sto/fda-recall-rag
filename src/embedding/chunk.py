from langchain_text_splitters import RecursiveCharacterTextSplitter


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
            chunks.append({"text": piece, "metadata": metadata})
    return chunks
