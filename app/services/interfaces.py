from __future__ import annotations

from typing import Protocol

from app.models import ScoreResult, Ticket


class JiraReadClient(Protocol):
    def fetch_backlog(self, jql: str, max_items: int) -> list[Ticket]: ...


class JiraWriteClient(Protocol):
    def update_score(self, ticket_id: str, field_id: str, score: int) -> None: ...


class PromptBuilder(Protocol):
    def build_prompt(self, ticket: Ticket) -> str: ...


class LLMGateway(Protocol):
    def score_ticket(self, prompt: str) -> str: ...


class ResponseParser(Protocol):
    def parse(self, raw_text: str) -> ScoreResult: ...
