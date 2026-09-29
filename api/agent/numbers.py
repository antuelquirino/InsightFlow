"""Checks that every number in a written answer comes from the result rows.

A number in the text is supported when some value in the rows, rounded the way
the text shows it, gives that number: 0.0918 supports "9.2%" and "9%", 297287
supports "$297,287", "$297k" and "$0.3M", 2.5 supports "2.5x". Signs are
ignored ("lost $5,160" for -5160). Small integers (up to 12: "3 months",
"12-month NRR"), numbers from the question and the parts of dates in the rows
are always allowed. Anything else, such as a difference or a ratio the model
worked out itself, is reported.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Iterable

NUMBER = re.compile(
    r"(?<![\w.])\$?(?P<digits>\d{1,3}(?:,\d{3})+|\d+)(?:\.(?P<decimals>\d+))?"
    r"(?:\s?(?P<unit>%|[kKmMbB](?![a-zA-Z])))?"
)
SCALES = {"k": 1e3, "m": 1e6, "b": 1e9}
ALWAYS_ALLOWED_MAX = 12


@dataclass(frozen=True)
class Mention:
    text: str
    value: float
    decimals: int
    unit: str | None


def mentions(text: str) -> list[Mention]:
    found = []
    for match in NUMBER.finditer(text or ""):
        decimals = match["decimals"] or ""
        value = float(match["digits"].replace(",", "") + ("." + decimals if decimals else ""))
        unit = match["unit"].lower() if match["unit"] else None
        found.append(Mention(match.group(0).strip(), value, len(decimals), unit))
    return found


def unsupported_numbers(text: str, rows: list[dict[str, Any]], question: str = "") -> list[str]:
    """Numbers in `text` that no value in `rows` supports."""
    values = [abs(float(v)) for v in _row_values(rows)]
    allowed = {m.value for m in mentions(question)} | set(_date_parts(rows))
    unsupported = []
    for mention in mentions(text):
        if mention.unit is None and mention.decimals == 0:
            if mention.value <= ALWAYS_ALLOWED_MAX or mention.value in allowed:
                continue
        if not any(_supports(value, mention) for value in values):
            unsupported.append(mention.text)
    return unsupported


def _supports(value: float, mention: Mention) -> bool:
    tolerance = 0.5 * 10 ** -mention.decimals + 1e-9
    if mention.unit == "%":
        candidates = (value * 100, value)  # a fraction shown as a percentage, or already a percentage
    elif mention.unit in SCALES:
        candidates = (value / SCALES[mention.unit],)
    else:
        candidates = (value,)
    return any(abs(candidate - mention.value) <= tolerance for candidate in candidates)


def _row_values(rows: Iterable[dict[str, Any]]) -> Iterable[float]:
    for row in rows:
        for value in row.values():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                yield value


def _date_parts(rows: Iterable[dict[str, Any]]) -> Iterable[float]:
    for row in rows:
        for value in row.values():
            if isinstance(value, (date, datetime)):
                yield from (value.year, value.month, value.day)
            elif isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}(-\d{2})?", value):
                yield from (float(part) for part in value.split("-"))
