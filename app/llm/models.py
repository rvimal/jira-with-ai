from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LlmResponse:
    text: str
    raw_response: dict[str, Any]
    request_id: str | None = None
    usage: dict[str, Any] = field(default_factory=dict)
    error: str | None = None