import json
import os
from pathlib import Path

from dotenv import load_dotenv

from src.ingestion.ecfr import ECFRIngestor
from src.ingestion.openfda import OpenFDAEnforcementIngestor

load_dotenv()

OUT_DIR = Path("data/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def write_jsonl(path: Path, docs: list[dict]) -> None:
    with path.open("w") as f:
        for doc in docs:
            f.write(json.dumps(doc) + "\n")


def main():
    as_of_date = "2026-08-06"
    api_key = os.getenv("OPENFDA_API_KEY")

    regulation_docs = []
    for part in [7, 117, 211, 820]:
        regulation_docs.extend(ECFRIngestor(part, as_of_date).run())
    write_jsonl(OUT_DIR / "regulations.jsonl", regulation_docs)
    print("regulations:", len(regulation_docs))

    sources = [
        ("https://api.fda.gov/food/enforcement.json", "food", "food_recalls.jsonl"),
        ("https://api.fda.gov/drug/enforcement.json", "drug", "drug_recalls.jsonl"),
        ("https://api.fda.gov/device/enforcement.json", "device", "device_recalls.jsonl"),
    ]
    for url, product_type, filename in sources:
        docs = OpenFDAEnforcementIngestor(url, product_type, api_key=api_key).run()
        write_jsonl(OUT_DIR / filename, docs)
        print(product_type, len(docs))


if __name__ == "__main__":
    main()
