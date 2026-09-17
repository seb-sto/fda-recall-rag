from src.embedding.chunk import chunk_documents


def test_short_document_stays_one_chunk():
    docs = [{"text": "Short text.", "metadata": {"source_type": "food", "recall_number": "F-0001-2020"}}]
    chunks = chunk_documents(docs, chunk_size=800)
    assert len(chunks) == 1


def test_long_document_splits_into_multiple_chunks():
    long_text = " ".join(f"Sentence number {i}." for i in range(200))
    docs = [{"text": long_text, "metadata": {"source_type": "regulation", "section_number": "7.99"}}]
    chunks = chunk_documents(docs, chunk_size=200, chunk_overlap=20)
    assert len(chunks) > 1
    assert all(len(c["text"]) <= 200 for c in chunks)


def test_chunk_ids_are_stable_and_unique():
    docs = [{"text": "A " * 300, "metadata": {"source_type": "food", "recall_number": "F-0002-2020"}}]
    ids_run1 = [c["id"] for c in chunk_documents(docs, chunk_size=100)]
    ids_run2 = [c["id"] for c in chunk_documents(docs, chunk_size=100)]
    assert ids_run1 == ids_run2
    assert len(ids_run1) == len(set(ids_run1))
