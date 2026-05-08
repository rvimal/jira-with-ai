from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TicketSummary:
    ticket_id: str
    key: str
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TicketDetails:
    ticket_id: str
    key: str
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class UpdateResult:
    ticket_id: str
    success: bool
    raw: dict[str, Any] = field(default_factory=dict)