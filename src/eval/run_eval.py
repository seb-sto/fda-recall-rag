import json

from src.eval.metrics import answer_relevancy, context_precision, context_recall, faithfulness
from src.rag.generate import generate_answer
from src.rag.rerank import rerank
from src.rag.retrieve import retrieve

TEST_SET_PATH = "data/eval/test_set.jsonl"


def load_test_set() -> list[dict]:
    with open(TEST_SET_PATH) as f:
        return [json.loads(line) for line in f]


def run_one(item: dict, use_reranking: bool) -> dict:
    question = item["question"]
    chunks = retrieve(question, n_results=10 if use_reranking else 5)
    if use_reranking:
        chunks = rerank(question, chunks, top_k=5)

    answer = generate_answer(question, chunks)
    texts = [c["text"] for c in chunks]

    return {
        "faithfulness": faithfulness(answer, "\n\n".join(texts)),
        "answer_relevancy": answer_relevancy(question, answer),
        "context_precision": context_precision(question, texts),
        "context_recall": context_recall(item["ground_truth"], texts),
    }


def run_eval(use_reranking: bool) -> dict:
    test_set = load_test_set()
    totals = {"faithfulness": 0.0, "answer_relevancy": 0.0, "context_precision": 0.0, "context_recall": 0.0}

    for i, item in enumerate(test_set):
        scores = run_one(item, use_reranking)
        for k, v in scores.items():
            totals[k] += v
        print(f"[{i + 1}/{len(test_set)}] {item['question'][:60]}")

    n = len(test_set)
    return {k: round(v / n, 3) for k, v in totals.items()}


if __name__ == "__main__":
    print("Running baseline (no reranking)...")
    baseline = run_eval(use_reranking=False)

    print("\nRunning with reranking...")
    reranked = run_eval(use_reranking=True)

    print("\n=== Results ===")
    print(f"{'Metric':<20}{'Baseline':<12}{'Reranked':<12}")
    for k in baseline:
        print(f"{k:<20}{baseline[k]:<12}{reranked[k]:<12}")
