from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
import requests
from src.ingestion.base import IngestorBase

class OpenFDAEnforcementIngestor(IngestorBase):
    PAGE_SIZE = 1000

    def __init__(self, endpoint_url: str, product_type: str, api_key: str | None = None):
        self.endpoint_url = endpoint_url
        self.product_type = product_type  # "food" | "drug" | "device"
        self.api_key = api_key

    def _with_api_key(self, url: str) -> str:
        if not self.api_key:
            return url
        parts = urlsplit(url)
        query = dict(parse_qsl(parts.query))
        query["api_key"] = self.api_key
        return urlunsplit(parts._replace(query=urlencode(query)))

    def fetch(self) -> list[dict]:
        results = []
        params = {"limit": self.PAGE_SIZE}
        if self.api_key:
            params["api_key"] = self.api_key

        resp = requests.get(self.endpoint_url, params=params)
        resp.raise_for_status()
        results.extend(resp.json()["results"])

        next_url = resp.links.get("next", {}).get("url")
        while next_url:
            resp = requests.get(self._with_api_key(next_url))
            resp.raise_for_status()
            results.extend(resp.json()["results"])
            next_url = resp.links.get("next", {}).get("url")

        return results

    def parse(self, raw: list[dict]) -> list[dict]:
        return raw  # openFDA records are already flat JSON — nothing to reshape here

    def to_documents(self, records: list[dict]) -> list[dict]:
        docs = []
        for r in records:
            text = f"{r.get('product_description', '')}\nReason for recall: {r.get('reason_for_recall', '')}"
            metadata = {
                "source_type": self.product_type,
                "recall_number": r.get("recall_number"),
                "event_id": r.get("event_id"),
                "classification": r.get("classification"),
                "recalling_firm": r.get("recalling_firm"),
                "status": r.get("status"),
                "distribution_pattern": r.get("distribution_pattern"),
                "recall_initiation_date": r.get("recall_initiation_date"),
            }
            docs.append({"text": text, "metadata": metadata})
        return docs
