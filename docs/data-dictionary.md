# Data Dictionary

Every chunk stored in ChromaDB is `{id, text, metadata, embedding}`. `id` follows the scheme `{source_type}:{key}:{chunk_index}` (e.g. `food:F-0276-2017:0`), guaranteeing uniqueness and idempotent re-ingestion. `chunk_index` is added by the chunking step and present in every document's metadata regardless of source.

## Regulations (`regulations` collection)

Source: eCFR API, Title 21, Parts 7, 117, 211, 820.

| Field | Type | Example | Notes |
|---|---|---|---|
| `source_type` | string | `"regulation"` | |
| `cfr_part` | int | `117` | |
| `subpart` | string | `"C"` | |
| `section_number` | string | `"117.135"` | |
| `heading` | string | `"§ 117.135 Preventive controls."` | |
| `citation` | string | `"21 CFR § 117.135"` | Used directly in generation prompts and answer citations |
| `effective_date` | string | `"2026-08-06"` | The eCFR "as of" date the section was fetched for, not a per-section effective date (the raw XML doesn't expose one cleanly) |
| `chunk_index` | int | `0` | Added at chunking time |

## Recalls (`food_recalls` / `drug_recalls` / `device_recalls` collections)

Source: openFDA enforcement API (food, drug, device endpoints — same schema across all three).

| Field | Type | Example | Notes |
|---|---|---|---|
| `source_type` | string | `"food"` / `"drug"` / `"device"` | |
| `recall_number` | string | `"F-0276-2017"` | openFDA's unique identifier; used directly in generation prompts and answer citations |
| `event_id` | string | `"75272"` | |
| `classification` | string | `"Class II"` | Risk grade, governed by 21 CFR § 7.41 |
| `recalling_firm` | string | `"Pharmatech LLC"` | |
| `status` | string | `"Terminated"` | |
| `distribution_pattern` | string | `"FL, MI, MS, and OH."` | Free text, not a clean structured list — formatting is inconsistent across records (see design-decisions.md) |
| `recall_initiation_date` | string | `"20160808"` | `YYYYMMDD`, no separators |
| `chunk_index` | int | `0` | Added at chunking time |
