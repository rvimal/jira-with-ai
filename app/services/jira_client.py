from __future__ import annotations

from app.models import Ticket


class InMemoryJiraClient:
    """In-memory implementation for local execution and tests."""

    def __init__(self, tickets: list[Ticket]) -> None:
        self._tickets = {ticket.ticket_id: ticket for ticket in tickets}

    def fetch_backlog(self, jql: str, max_items: int) -> list[Ticket]:
        # jql is accepted for API parity but ignored in this in-memory adapter.
        return list(self._tickets.values())[:max_items]

    def update_score(self, ticket_id: str, field_id: str, score: int) -> None:
        _ = field_id
        ticket = self._tickets[ticket_id]
        ticket.existing_score = score

    @property
    def tickets(self) -> dict[str, Ticket]:
        return self._tickets
