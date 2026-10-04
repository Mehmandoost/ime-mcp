import pytest

from ime_mcp.dates import chunk_jalali_range, parse_date


def test_parse_jalali_date():
    parsed = parse_date("1404-07-01")
    assert parsed.jalali == "1404/07/01"
    assert parsed.gregorian.startswith("2025-")


def test_parse_gregorian_date():
    parsed = parse_date("2025-09-23")
    assert parsed.jalali == "1404/07/01"


def test_chunk_jalali_range():
    start = parse_date("1404-07-01")
    end = parse_date("1404-07-05")
    chunks = chunk_jalali_range(start, end, chunk_days=2)
    assert chunks[0][0] == "1404/07/01"
    assert chunks[-1][1] == "1404/07/05"


def test_invalid_date():
    with pytest.raises(ValueError):
        parse_date("not-a-date")
