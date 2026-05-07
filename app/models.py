from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class TicketStatus(StrEnum):
    UPDATED = "updated"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass(slots=True)
class Ticket:
    ticket_id: str
    summary: str
    description: str
    labels: list[str] = field(default_factory=list)
    story_points: float | None = None
    priority: str | None = None
    assignee: str | None = None
    sprint: str | None = None
    components: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    existing_score: int | None = None


@dataclass(slots=True)
class ScoreResult:
    ticket_id: str
    score: int
    reason: str
    confidence: float


@dataclass(slots=True)
class TicketProcessResult:
    ticket_id: str
    status: TicketStatus
    message: str


@dataclass(slots=True)
class RunSummary:
    run_id: str
    total: int
    updated: int
    skipped: int
    failed: int
    started_at: datetime
    finished_at: datetime

    @property
    def duration_seconds(self) -> float:
        return (self.finished_at - self.started_at).total_seconds()
