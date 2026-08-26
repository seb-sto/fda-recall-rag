from abc import ABC, abstractmethod
from typing import Any


class IngestorBase(ABC):
    @abstractmethod
    def fetch(self) -> Any:
        """Pull raw data from the source (HTTP call, file read, etc.)."""

    @abstractmethod
    def parse(self, raw: Any) -> list[dict]:
        """Turn raw payload into structured records (one dict per record)."""

    @abstractmethod
    def to_documents(self, records: list[dict]) -> list[dict]:
        """Turn structured records into {"text": ..., "metadata": {...}} documents."""

    def run(self) -> list[dict]:
        raw = self.fetch()
        records = self.parse(raw)
        return self.to_documents(records)
