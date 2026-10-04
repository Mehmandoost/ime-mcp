"""Tool response helpers."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any


def tool_payload(
    *,
    source: str,
    data: Any,
    row_count: int | None = None,
    truncated: bool = False,
    extra: dict[str, Any] | None = None,
) -> str:
    body: dict[str, Any] = {
        "source": source,
        "fetched_at": datetime.now(UTC).isoformat(),
        "data": data,
    }
    if row_count is not None:
        body["row_count"] = row_count
    if truncated:
        body["truncated"] = True
    if extra:
        body.update(extra)
    return json.dumps(body, ensure_ascii=False, indent=2)


class ImeUnavailableError(RuntimeError):
    """Raised when IME endpoints fail or return unusable data."""
