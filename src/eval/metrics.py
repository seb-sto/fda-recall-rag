import json
import os

import anthropic

_client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))
_JUDGE_MODEL = "claude-sonnet-5"


def _judge(prompt: str) -> dict:
    message = _client.messages.create(
        model=_JUDGE_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    text = message.content[0].text.replace("```json", "").replace("```", "")
    start, end = text.find("{"), text.rfind("}") + 1
    return json.loads(text[start:end])


def faithfulness(answer: str, context: str) -> float:
    prompt = f"""Break the ANSWER into individual factual claims. For each claim, decide if it is directly supported by the CONTEXT.

CONTEXT:
{context}

ANSWER:
{answer}

Respond with only JSON: {{"claims": [{{"claim": "...", "supported": true}}]}}"""
    claims = _judge(prompt)["claims"]
    return sum(c["supported"] for c in claims) / len(claims) if claims else 1.0


def answer_relevancy(question: str, answer: str) -> float:
    prompt = f"""Rate how directly the ANSWER addresses the QUESTION, from 0.0 (irrelevant) to 1.0 (fully addresses it). A correct refusal ("the context doesn't contain this") counts as fully relevant if the question is genuinely unanswerable from context.

QUESTION: {question}
ANSWER: {answer}

Respond with only JSON: {{"score": 0.0}}"""
    return float(_judge(prompt)["score"])


def context_precision(question: str, chunks: list[str]) -> float:
    if not chunks:
        return 0.0
    prompt = f"""For each CONTEXT CHUNK, decide if it is relevant to the QUESTION.

QUESTION: {question}
CHUNKS: {json.dumps(chunks)}

Respond with only JSON: {{"relevant": [true, false]}} — one entry per chunk, in order."""
    relevant = _judge(prompt)["relevant"]
    return sum(relevant) / len(relevant)


def context_recall(ground_truth: str, chunks: list[str]) -> float:
    context = "\n\n".join(chunks)
    prompt = f"""Does the CONTEXT contain enough information to derive the GROUND TRUTH? Score 0.0 (none of it) to 1.0 (fully supports it).

GROUND TRUTH: {ground_truth}
CONTEXT: {context}

Respond with only JSON: {{"score": 0.0}}"""
    return float(_judge(prompt)["score"])
