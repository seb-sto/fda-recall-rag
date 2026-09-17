# Design Decisions

## Why eCFR + openFDA over synthetic data
Every document traces back to a real regulation or a real recall record — no fabricated data anywhere in the vector store. This was a deliberate, explicit project constraint from the start, not an afterthought, and it's the reason the Week 6 evaluation test set could be hand-verified against real, checkable source text rather than invented "ground truth."

## Why the project pivoted from FMCSA/MCMIS to openFDA
The original plan used FMCSA carrier-safety data, but MCMIS bulk crash/inspection data turned out to require a FOIA request (up to 20 business days) rather than being freely downloadable. openFDA's food/drug/device enforcement endpoints are clean, bulk-friendly, and require no authentication for basic access — a better fit for a project with a tight, self-funded timeline.

## Why local embeddings (`all-MiniLM-L6-v2`) over OpenAI
Keeps the project's cost target near $0/month — no per-embedding API cost for ~97,500 chunks — and runs entirely offline once the model weights are cached. The trade-off is a smaller, lower-capacity model than a hosted alternative; the Week 6 RAGAS-style evaluation exists specifically to give a measured answer on whether that trade-off costs real retrieval quality, rather than assuming it either way.

## Why Claude Haiku by default, Sonnet configurable
Haiku keeps per-query generation cost low for a system meant to be queried repeatedly during development and demos. `LLM_MODEL` is fully configurable via environment variable, so switching to Sonnet for higher-stakes use is a config change, not a code change.

## Why four Chroma collections instead of one
`regulations`, `food_recalls`, `drug_recalls`, `device_recalls` are separate collections rather than one combined store, so that metadata pre-filtering (Week 4) and reranking (Week 5) have a meaningful "sourced from where" dimension to work with — a core part of demonstrating filtered multi-source retrieval rather than a single undifferentiated document pile. Three vs. four was an explicit decision point: two would have understated the architecture, three (merging drug+device) would have saved some engineering effort — four was chosen since drug and device turned out to need genuinely separate ingestor runs anyway once built.

## Why cross-encoder reranking (`ms-marco-MiniLM-L-6-v2`) over Cohere
Free, local, and requires no additional API key — consistent with the project's cost target. Week 6's evaluation showed its actual effect concentrated exactly where expected: context precision and recall improved measurably, while faithfulness and answer relevancy (governed more by the generation-layer system prompt) stayed flat.

## Why hand-rolled RAG components instead of LangChain's higher-level abstractions
Retrieval, reranking, and conversation memory are all plain Python functions calling Chroma/Anthropic SDKs directly, rather than LangChain's retriever/memory abstractions. This was deliberate from the start (to keep every mechanism inspectable for a learning project) and was reinforced by real friction encountered along the way: `langchain.memory`'s classes no longer exist in the installed `langchain` version, and `langchain_text_splitters` had to be added as a separate package after a similar surprise — both symptoms of `langchain`'s fast-moving, frequently-restructured API surface.

## Why the RAGAS-style evaluation is hand-rolled rather than using the `ragas` package
The `ragas` package pulls in a large `langchain-community`/`datasets` dependency tree, and the installed version had a hard-coded top-level import (`ChatVertexAI`) that no longer exists in current `langchain-community` (which is itself being sunset). Rather than fight version pins likely to cascade further, the four standard metrics (faithfulness, answer relevancy, context precision, context recall) were reimplemented directly against the `anthropic` SDK, using Claude's tool-use feature for schema-enforced structured judge output — deliberately using Sonnet as judge rather than the Haiku default used for generation, to avoid self-preference bias.
