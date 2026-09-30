"""Checks that every number in a written answer comes from the result rows.

A number in the text is supported when some value in the rows, rounded the way
the text shows it, gives that number: 0.0918 supports "9.2%" and "9%", 297287
supports "$297,287", "$297k" and "$0.3M", 2.5 supports "2.5x". Spanish formats
are read too: "9,2%", "US$297 mil", "US$297.287". Signs are
ignored ("lost $5,160" for -5160). Small integers (up to 12: "3 months",
"12-month NRR"), numbers from the question and the parts of dates in the rows
are always allowed, and so are the reference values 0, 1 and 100 ("NRR above
100%"). Anything else, such as a difference or a ratio the model worked out
itself, is reported.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Iterable

NUMBER = re.compile(
    r"(?<![\w.,])(?:US)?\$?(?P<raw>\d[\d.,]*\d|\d)"
    r"(?:\s?(?P<unit>%|mil\b|millones\b|[kKmMbB](?![a-zA-Z])))?"
)
UNITS = {"mil": "k", "millones": "m"}  # Spanish words for the same scales
SCALES = {"k": 1e3, "m": 1e6, "b": 1e9}
ALWAYS_ALLOWED_MAX = 12
# Thresholds such as "above 1.0" or "100%", as (value, unit).
REFERENCE_VALUES = {(0.0, None), (0.0, "%"), (1.0, None), (100.0, "%")}


@dataclass(frozen=True)
class Reading:
    value: float
    decimals: int


@dataclass(frozen=True)
class Mention:
    text: str
    readings: tuple[Reading, ...]  # every way the digits can be read
    unit: str | None

    @property
    def value(self) -> float:
        return self.readings[0].value

    @property
    def decimals(self) -> int:
        return self.readings[0].decimals


def _readings(raw: str) -> tuple[Reading, ...]:
    """English (1,234.5) and Spanish (1.234,5) readings of a number's digits.

    A single separator followed by exactly three digits is ambiguous ("297.287"
    is thousands in Spanish, "1.239" a decimal in English), so both readings are
    kept and the number is supported if either one is.
    """
    commas, dots = raw.count(","), raw.count(".")
    if not commas and not dots:
        return (Reading(float(raw), 0),)
    if commas and dots:
        decimal = "," if raw.rfind(",") > raw.rfind(".") else "."
        thousands = "." if decimal == "," else ","
        whole, _, fraction = raw.replace(thousands, "").partition(decimal)
        return (Reading(float(f"{whole}.{fraction}"), len(fraction)),)
    separator = "," if commas else "."
    groups = raw.split(separator)
    as_thousands = Reading(float("".join(groups)), 0)
    if len(groups) > 2:  # 1,234,567 or 1.234.567
        return (as_thousands,)
    whole, fraction = groups
    as_decimal = Reading(float(f"{whole}.{fraction}"), len(fraction))
    if len(fraction) == 3:
        return (as_decimal, as_thousands) if separator == "." else (as_thousands, as_decimal)
    return (as_decimal,)


def mentions(text: str) -> list[Mention]:
    found = []
    for match in NUMBER.finditer(text or ""):
        unit = match["unit"].lower() if match["unit"] else None
        unit = UNITS.get(unit, unit)
        found.append(Mention(match.group(0).strip(), _readings(match["raw"]), unit))
    return found


def unsupported_numbers(text: str, rows: list[dict[str, Any]], question: str = "") -> list[str]:
    """Numbers in `text` that no value in `rows` supports."""
    values = [abs(float(v)) for v in _row_values(rows)]
    allowed = (
        {(r.value, m.unit) for m in mentions(question) for r in m.readings}
        | {(float(part), None) for part in _date_parts(rows)}
        | REFERENCE_VALUES
    )
    unsupported = []
    for mention in mentions(text):
        if any((r.value, mention.unit) in allowed for r in mention.readings):
            continue
        if mention.unit is None and any(
            r.decimals == 0 and r.value <= ALWAYS_ALLOWED_MAX for r in mention.readings
        ):
            continue
        if not any(
            _supports(value, reading, mention.unit)
            for value in values
            for reading in mention.readings
        ):
            unsupported.append(mention.text)
    return unsupported


def _supports(value: float, reading: Reading, unit: str | None) -> bool:
    tolerance = 0.5 * 10 ** -reading.decimals + 1e-9
    if unit == "%":
        candidates = (value * 100, value)  # a fraction shown as a percentage, or already a percentage
    elif unit in SCALES:
        candidates = (value / SCALES[unit],)
    else:
        candidates = (value,)
    return any(abs(candidate - reading.value) <= tolerance for candidate in candidates)


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
