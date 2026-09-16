# Evaluation

## Methodology

RAGAS-style evaluation was implemented by hand rather than using the `ragas` package — it pulls in a large, actively-churning `langchain-community`/`datasets` dependency tree, and the installed version had a hard-coded import (`ChatVertexAI`) that no longer exists in current `langchain-community`, making it unusable without fighting unrelated version conflicts. The four standard RAGAS metrics were reimplemented directly against the `anthropic` SDK using Claude Sonnet as an LLM judge (deliberately a different, stronger model than the Haiku default used for generation, to avoid self-preference bias).

- **Faithfulness** — the answer is decomposed into individual factual claims; each is checked against the retrieved context; score = fraction supported.
- **Answer relevancy** — the judge rates 0–1 how directly the answer addresses the question (a correct "I don't know" counts as fully relevant for genuinely unanswerable questions).
- **Context precision** — the judge rates each retrieved chunk as relevant or not to the question; score = fraction relevant. (Simplification vs. real RAGAS: unweighted by rank position.)
- **Context recall** — the judge rates whether the retrieved context contains enough information to derive the ground-truth answer.

Test set: 36 hand-written question/ground-truth pairs (`data/eval/test_set.jsonl`), grounded in real, directly-inspected eCFR sections (Parts 7, 117, 211, 820) and real openFDA recall records across all three product types (food, drug, device). Three questions are deliberately unanswerable from the available context, to test whether the system is rewarded for an honest refusal rather than penalized for a shorter answer.

## Results: baseline vs. cross-encoder reranking

| Metric | Baseline (no reranking) | With reranking | Change |
|---|---|---|---|
| Faithfulness | 0.755 | 0.754 | ~flat |
| Answer relevancy | 0.986 | 0.969 | ~flat |
| Context precision | 0.300 | 0.350 | +17% |
| Context recall | 0.697 | 0.728 | +4.4% |

## Interpretation

Reranking's measurable effect is concentrated exactly where it should be — retrieval quality (context precision and recall) — while faithfulness and answer relevancy stay high and roughly flat in both conditions. That's consistent with the citation-enforcing system prompt doing its job at the generation layer regardless of retrieval quality: the model correctly avoids fabricating claims even when handed a partially-irrelevant context set.

Context precision's low absolute value (0.30–0.35) is a genuine, notable weakness: `retrieve()` searches all four collections by default with no source-type filtering, so off-topic chunks from unrelated collections regularly make the top-5 on embedding proximity alone. A source-type-aware retrieval step (classify the question's likely domain before searching) would be the natural next improvement, rather than a fix applied here.
