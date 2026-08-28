from typing import Literal
from pydantic import BaseModel


class QueryFilters(BaseModel):
    source_type: Literal["regulation", "food", "drug", "device"] | None = None
    cfr_part: int | None = None
    state: str | None = None


class QueryRequest(BaseModel):
    question: str
    filters: QueryFilters | None = None
    n_results: int = 5


class SourceChunk(BaseModel):
    text: str
    metadata: dict
    distance: float


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]


class DocumentCounts(BaseModel):
    counts: dict[str, int]
