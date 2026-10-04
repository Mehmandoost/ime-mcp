"""Jalali and Gregorian date parsing for IME APIs."""

from __future__ import annotations

import re
from dataclasses import dataclass

import jdatetime as jd

_DATE_RE = re.compile(r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$")


@dataclass(frozen=True)
class ParsedDate:
    """Normalized date for API calls."""

    jalali: str  # YYYY/MM/DD
    gregorian: str  # YYYY-MM-DD


def parse_date(value: str) -> ParsedDate:
    """Parse Jalali (13xx/14xx) or Gregorian date strings."""
    value = value.strip()
    match = _DATE_RE.match(value)
    if not match:
        raise ValueError(f"Invalid date {value!r}; use YYYY-MM-DD or YYYY/MM/DD")

    year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))

    if year >= 1700:
        g = __import__("datetime").date(year, month, day)
        j = jd.date.fromgregorian(date=g)
        return ParsedDate(
            jalali=f"{j.year:04d}/{j.month:02d}/{j.day:02d}",
            gregorian=f"{g.year:04d}-{g.month:02d}-{g.day:02d}",
        )

    if year >= 1300:
        j = jd.date(year, month, day)
        g = j.togregorian()
        return ParsedDate(
            jalali=f"{j.year:04d}/{j.month:02d}/{j.day:02d}",
            gregorian=f"{g.year:04d}-{g.month:02d}-{g.day:02d}",
        )

    g = __import__("datetime").date(year, month, day)
    j = jd.date.fromgregorian(date=g)
    return ParsedDate(
        jalali=f"{j.year:04d}/{j.month:02d}/{j.day:02d}",
        gregorian=f"{g.year:04d}-{g.month:02d}-{g.day:02d}",
    )


def today_jalali() -> str:
    t = jd.date.today()
    return f"{t.year:04d}/{t.month:02d}/{t.day:02d}"


def chunk_jalali_range(start: ParsedDate, end: ParsedDate, chunk_days: int = 30) -> list[tuple[str, str]]:
    """Split inclusive Jalali range into API chunks (YYYY/MM/DD)."""
    start_j = jd.date(*map(int, start.jalali.replace("/", "-").split("-")))
    end_j = jd.date(*map(int, end.jalali.replace("/", "-").split("-")))
    if start_j > end_j:
        return []

    chunks: list[tuple[str, str]] = []
    cur = start_j
    delta = jd.timedelta(days=chunk_days)
    while cur <= end_j:
        nxt = cur + delta
        chunk_end = end_j if nxt > end_j else nxt
        chunks.append(
            (
                f"{cur.year:04d}/{cur.month:02d}/{cur.day:02d}",
                f"{chunk_end.year:04d}/{chunk_end.month:02d}/{chunk_end.day:02d}",
            )
        )
        cur = chunk_end + jd.timedelta(days=1)
    return chunks
