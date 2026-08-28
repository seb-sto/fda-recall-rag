import os
import anthropic

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


def generate_answer(question: str, context_chunks: list[dict], model: str | None = None) -> str:
    model = model or os.getenv("LLM_MODEL", "claude-haiku-4-5-20251001")
    context = _format_context(context_chunks)

    message = _client().messages.create(
        model=model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}],
    )
    return message.content[0].text
