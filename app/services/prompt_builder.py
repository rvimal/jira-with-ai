from __future__ import annotations

from pathlib import Path

from app.models import Ticket


class FilePromptBuilder:
    def __init__(self, template_path: Path, rules_path: Path) -> None:
        self.template = template_path.read_text(encoding="utf-8")
        self.rules = rules_path.read_text(encoding="utf-8")

    def build_prompt(self, ticket: Ticket) -> str:
        fields = {
            "ticket_id": ticket.ticket_id,
            "summary": ticket.summary,
            "description": ticket.description,
            "labels": ",".join(ticket.labels),
            "story_points": "" if ticket.story_points is None else str(ticket.story_points),
            "priority": ticket.priority or "",
            "assignee": ticket.assignee or "",
            "sprint": ticket.sprint or "",
            "components": ",".join(ticket.components),
            "dependencies": ",".join(ticket.dependencies),
            "rules": self.rules,
        }
        return self.template.format(**fields)
