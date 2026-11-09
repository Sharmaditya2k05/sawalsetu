"""Query understanding: resolve relative time phrases into the month labels used in documents."""
from __future__ import annotations

import re
from datetime import date

from .documents import MONTHS, fy_label


def _shift(d: date, months: int) -> date:
    y, m = d.year, d.month + months
    while m <= 0:
        m += 12
        y -= 1
    while m > 12:
        m -= 12
        y += 1
    return date(y, m, 1)


def _label(d: date) -> str:
    return f"{MONTHS[d.month - 1]} {d.year}"


def expand_time_phrases(question: str, today: date | None = None) -> str:
    """Append explicit month / year labels for relative phrases so BM25 can match them.

    "sales last month vs the month before" -> "... October 2026 September 2026"
    """
    today = today or date.today()
    q = question.lower()
    extra: list[str] = []
    this_month = today.replace(day=1)

    if re.search(r"\b(this|current) month\b|\bmtd\b|month to date", q):
        extra.append(_label(this_month))
    if re.search(r"\b(last|previous|past) month\b|\bpichle mahine\b", q):
        extra.append(_label(_shift(this_month, -1)))
    if re.search(r"month before( that| last)?\b|two months ago|\b2 months ago", q):
        extra.append(_label(_shift(this_month, -2)))
    if re.search(r"last (three|3) months|past (three|3) months|last quarter|past quarter", q):
        extra.extend(_label(_shift(this_month, -i)) for i in range(1, 4))
    if re.search(r"last (six|6) months|past (six|6) months|half year", q):
        extra.extend(_label(_shift(this_month, -i)) for i in range(1, 7))
    if re.search(r"\bthis year\b|\bytd\b|year to date|\bthis fy\b|current financial year", q):
        extra.append(fy_label(today))
        extra.append(str(today.year))
    if re.search(r"\blast year\b|previous year|\blast fy\b", q):
        extra.append(fy_label(date(today.year - 1, today.month, 1)))
        extra.append(str(today.year - 1))
    if re.search(r"\b(today|yesterday|this week|last week|recent|recently|latest)\b", q):
        extra.append(_label(this_month))
        extra.append(_label(_shift(this_month, -1)))

    return question if not extra else f"{question} {' '.join(dict.fromkeys(extra))}"
