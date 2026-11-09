"""Answer generation.

ClaudeAnswerer streams a grounded answer from Claude using the retrieved documents as
numbered context. OfflineAnswerer is used when no ANTHROPIC_API_KEY is configured: it
composes a readable answer from the top-ranked documents so the product still works for
demos and so retrieval quality can be inspected on its own.
"""
from __future__ import annotations

import re
from typing import AsyncIterator, Iterable

from ..config import Settings
from .documents import Document

SYSTEM_PROMPT = """You are SawalSetu, the business intelligence assistant for {company}, an Indian distributor whose
accounting data lives in MargBooks (GST billing, inventory and accounting software).

You answer questions from the owner and their accounts team using ONLY the context passages supplied with each
question. The passages are extracted from MargBooks: sales invoices, purchase bills, orders, party ledgers, item
masters and pre-computed monthly / customer / supplier / receivables summaries.

How to answer:
- Lead with the number or fact asked for, then the supporting detail. Be concise and use plain business language;
  Hinglish terms like udhaar (receivables), bikri (sales) and kharid (purchases) are fine to mirror if the user uses them.
- Amounts are in Indian rupees. Write them like ₹4,52,300 or ₹12.4 L / ₹1.2 Cr for large figures.
- Cite the passage you used after each fact with its number in square brackets, e.g. [3]. Only cite passages that
  actually support the statement.
- Prefer the summary passages (monthly, customer, supplier, receivables, snapshot) for totals and rankings; use
  individual invoices for specifics such as bill numbers and dates.
- If the context does not contain what is needed, say exactly what is missing and suggest the closest thing you can
  answer. Never invent figures, bill numbers, dates or party names.
- When a question asks for advice (who to chase for payment, which items to push), ground every recommendation in the
  numbers from the context and say why.
- Use short Markdown: a lead sentence, then bullets or a small table when comparing several parties or months.
  No headings larger than ###."""


def format_context(docs: Iterable[Document]) -> str:
    lines = []
    for i, d in enumerate(docs, start=1):
        lines.append(f"[{i}] ({d.title}) {d.text}")
    return "\n\n".join(lines)


class ClaudeAnswerer:
    name = "claude"

    def __init__(self, settings: Settings):
        import anthropic

        self._anthropic = anthropic
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model
        self.effort = settings.claude_effort
        self.company = settings.company_name

    async def stream(self, question: str, docs: list[Document], history: list[dict]) -> AsyncIterator[dict]:
        messages = [{"role": m["role"], "content": m["content"]} for m in history[-8:] if m.get("content")]
        messages.append({
            "role": "user",
            "content": f"Context passages from MargBooks:\n\n{format_context(docs)}\n\nQuestion: {question}",
        })
        kwargs: dict = dict(
            model=self.model,
            max_tokens=4000,
            system=[{"type": "text", "text": SYSTEM_PROMPT.format(company=self.company),
                     "cache_control": {"type": "ephemeral"}}],
            messages=messages,
            output_config={"effort": self.effort},
        )
        usage = None
        try:
            async with self.client.beta.messages.stream(
                betas=["server-side-fallback-2026-07-01"], fallbacks="default", **kwargs
            ) as stream:
                async for text in stream.text_stream:
                    yield {"type": "token", "text": text}
                final = await stream.get_final_message()
                usage = final.usage
                if final.stop_reason == "refusal":
                    yield {"type": "token", "text": "\n\n_The model declined to answer this request._"}
        except self._anthropic.BadRequestError:
            # Older SDK / platform without server-side fallbacks: retry on the plain endpoint.
            async with self.client.messages.stream(**kwargs) as stream:
                async for text in stream.text_stream:
                    yield {"type": "token", "text": text}
                final = await stream.get_final_message()
                usage = final.usage
        yield {
            "type": "done",
            "model": self.model,
            "usage": {
                "input_tokens": getattr(usage, "input_tokens", None),
                "output_tokens": getattr(usage, "output_tokens", None),
                "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", None),
            } if usage else None,
        }


class OfflineAnswerer:
    """Extractive fallback: no LLM, just the best passages written up as an answer."""

    name = "offline"

    def __init__(self, settings: Settings):
        self.company = settings.company_name

    async def stream(self, question: str, docs: list[Document], history: list[dict]) -> AsyncIterator[dict]:
        if not docs:
            yield {"type": "token", "text": "I could not find anything in the synced MargBooks data for that question. "
                                            "Try syncing first, or ask about sales, purchases, customers, suppliers or receivables."}
            yield {"type": "done", "model": "offline", "usage": None}
            return
        analytics = [d for d in docs if d.kind == "analytics"][:3]
        records = [d for d in docs if d.kind != "analytics"][:4]
        chunks: list[str] = []
        chunks.append("_Offline mode (no ANTHROPIC_API_KEY set) – showing the most relevant passages from your MargBooks data instead of a generated answer._\n\n")
        if analytics:
            chunks.append("**From the summaries:**\n\n")
            for d in analytics:
                idx = docs.index(d) + 1
                chunks.append(f"- {_first_sentences(d.text, 3)} [{idx}]\n")
            chunks.append("\n")
        if records:
            chunks.append("**Matching records:**\n\n")
            for d in records:
                idx = docs.index(d) + 1
                chunks.append(f"- {_first_sentences(d.text, 2)} [{idx}]\n")
        for c in chunks:
            yield {"type": "token", "text": c}
        yield {"type": "done", "model": "offline", "usage": None}


def _first_sentences(text: str, n: int) -> str:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return " ".join(parts[:n])


def build_answerer(settings: Settings):
    if settings.llm_available:
        return ClaudeAnswerer(settings)
    return OfflineAnswerer(settings)
