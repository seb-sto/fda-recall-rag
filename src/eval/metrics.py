import json
import os

import anthropic

_JUDGE_MODEL = "claude-sonnet-5"


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))


def _extract_list(raw, key: str) -> list:
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return []
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict) and isinstance(parsed.get(key), list):
            return parsed[key]
    return []


def _as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "1"}
    return bool(value)


def _judge(prompt: str, schema: dict, tool_name: str) -> dict:
    message = _client().messages.create(
        model=_JUDGE_MODEL,
        max_tokens=1024,
        tools=[{"name": tool_name, "description": "Submit the judgment.", "input_schema": schema}],
        tool_choice={"type": "tool", "name": tool_name},
        messages=[{"role": "user", "content": prompt}],
    )
    tool_use = next(block for block in message.content if block.type == "tool_use")
    return tool_use.input


def faithfulness(answer: str, context: str) -> float:
    prompt = f"""Break the ANSWER into individual factual claims. For each claim, decide if it is directly supported by the CONTEXT.

CONTEXT:
{context}

ANSWER:
{answer}"""
    schema = {
        "type": "object",
        "properties": {
            "claims": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "claim": {"type": "string"},
                        "supported": {"type": "boolean"},
                    },
                    "required": ["claim", "supported"],
                },
            }
        },
        "required": ["claims"],
    }
    claims = _extract_list(_judge(prompt, schema, "submit_faithfulness")["claims"], "claims")
    valid = [c for c in claims if isinstance(c, dict) and "supported" in c]
    if len(valid) < len(claims):
        print(f"WARNING: faithfulness judge returned {len(claims) - len(valid)} malformed claim(s), ignoring")
    return sum(_as_bool(c["supported"]) for c in valid) / len(valid) if valid else 1.0


def answer_relevancy(question: str, answer: str) -> float:
    prompt = f"""Rate how directly the ANSWER addresses the QUESTION, from 0.0 (irrelevant) to 1.0 (fully addresses it). A correct refusal ("the context doesn't contain this") counts as fully relevant if the question is genuinely unanswerable from context.

QUESTION: {question}
ANSWER: {answer}"""
    schema = {
        "type": "object",
        "properties": {"score": {"type": "number"}},
        "required": ["score"],
    }
    return float(_judge(prompt, schema, "submit_relevancy")["score"])


def context_precision(question: str, chunks: list[str]) -> float:
    if not chunks:
        return 0.0
    prompt = f"""For each CONTEXT CHUNK, decide if it is relevant to the QUESTION.

QUESTION: {question}
CHUNKS: {json.dumps(chunks)}

Return one boolean per chunk, in order."""
    schema = {
        "type": "object",
        "properties": {"relevant": {"type": "array", "items": {"type": "boolean"}}},
        "required": ["relevant"],
    }
    relevant = _extract_list(_judge(prompt, schema, "submit_precision")["relevant"], "relevant")
    if not relevant:
        return 0.0
    return sum(_as_bool(v) for v in relevant) / len(relevant)


def context_recall(ground_truth: str, chunks: list[str]) -> float:
    context = "\n\n".join(chunks)
    prompt = f"""Does the CONTEXT contain enough information to derive the GROUND TRUTH? Score 0.0 (none of it) to 1.0 (fully supports it).

GROUND TRUTH: {ground_truth}
CONTEXT: {context}"""
    schema = {
        "type": "object",
        "properties": {"score": {"type": "number"}},
        "required": ["score"],
    }
    return float(_judge(prompt, schema, "submit_recall")["score"])
