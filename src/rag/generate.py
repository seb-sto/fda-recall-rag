import os

import anthropic
from anthropic.types import MessageParam

SYSTEM_PROMPT = """You are an FDA regulatory and recall compliance assistant.
Answer only using the provided context. If the context does not contain
enough information to answer, say so explicitly rather than guessing.

Cite every claim using the source's citation, in this format:
[21 CFR § 117.135] for regulations, or [Recall F-0276-2017] for recalls.
"""


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))


def _format_context(chunks: list[dict]) -> str:
    parts = []
    for c in chunks:
        citation = c["metadata"].get("citation") or f"Recall {c['metadata'].get('recall_number')}"
        parts.append(f"[{citation}] {c['text']}")
    return "\n\n".join(parts)


def generate_answer(
    question: str,
    context_chunks: list[dict],
    history: list[tuple[str, str]] | None = None,
    model: str | None = None,
) -> str:
    resolved_model = model if model is not None else os.getenv("LLM_MODEL", "claude-haiku-4-5-20251001")
    context = _format_context(context_chunks)

    messages: list[MessageParam] = []
    for past_question, past_answer in history or []:
        messages.append({"role": "user", "content": past_question})
        messages.append({"role": "assistant", "content": past_answer})
    messages.append({"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"})

    message = _client().messages.create(
        model=resolved_model, max_tokens=1024, system=SYSTEM_PROMPT, messages=messages
    )
    return next(block.text for block in message.content if block.type == "text")