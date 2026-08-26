import xml.etree.ElementTree as ET
import requests
from src.ingestion.base import IngestorBase


class ECFRIngestor(IngestorBase):
    def __init__(self, part_number: int, as_of_date: str):
        self.part_number = part_number
        self.as_of_date = as_of_date  # e.g. "2026-08-06"

    def fetch(self) -> str:
        url = f"https://www.ecfr.gov/api/versioner/v1/full/{self.as_of_date}/title-21.xml"
        resp = requests.get(url, params={"part": self.part_number})
        resp.raise_for_status()
        return resp.text

    def parse(self, raw: str) -> list[dict]:
        root = ET.fromstring(raw)
        records = []
        for subpart in root.iter("DIV6"):
            subpart_id = subpart.get("N")
            for section in subpart.iter("DIV8"):
                section_number = section.get("N")
                heading = section.findtext("HEAD", default="").strip()
                text = "\n".join(
                    "".join(p.itertext()).strip() for p in section.iter("P")
                )
                records.append({
                    "subpart": subpart_id,
                    "section_number": section_number,
                    "heading": heading,
                    "text": text,
                })
        return records

    def to_documents(self, records: list[dict]) -> list[dict]:
        docs = []
        for r in records:
            text = f"{r['heading']}\n{r['text']}"
            metadata = {
                "source_type": "regulation",
                "cfr_part": self.part_number,
                "subpart": r["subpart"],
                "section_number": r["section_number"],
                "heading": r["heading"],
                "citation": f"21 CFR § {r['section_number']}",
                "effective_date": self.as_of_date,
            }
            docs.append({"text": text, "metadata": metadata})
        return docs
