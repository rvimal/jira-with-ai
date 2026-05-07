from __future__ import annotations

import json
from pathlib import Path

from app.config.settings import Settings
from app.models import Ticket
from app.services.jira_client import InMemoryJiraClient
from app.services.llm_gateway import StubLLMGateway
from app.services.orchestrator import BacklogPrioritizationOrchestrator
from app.services.prompt_builder import FilePromptBuilder
from app.services.response_parser import JsonResponseParser

ROOT = Path(__file__).resolve().parent


def bootstrap_demo_tickets() -> list[Ticket]:
    return [
        Ticket(
            ticket_id="PROJ-101",
            summary="Payment timeout under load",
            description="Checkout intermittently fails during traffic spikes.",
            labels=["revenue", "incident"],
            story_points=5,
            priority="High",
            assignee="alice",
            sprint="Sprint 28",
            components=["payments", "api"],
            dependencies=["PROJ-55"],
        ),
        Ticket(
            ticket_id="PROJ-102",
            summary="UI text typo on settings page",
            description="Fix typo in account settings header.",
            labels=["ui"],
            story_points=1,
            priority="Low",
            assignee="bob",
            sprint="Sprint 28",
            components=["frontend"],
            dependencies=[],
        ),
    ]


def main() -> None:
    settings = Settings.from_env()

    template_path = ROOT / "prompts" / "ticket_prompt.txt"
    rules_path = ROOT / "examples" / "scoring_rules.md"

    read_write_client = InMemoryJiraClient(bootstrap_demo_tickets())
    orchestrator = BacklogPrioritizationOrchestrator(
        settings=settings,
        read_client=read_write_client,
        write_client=read_write_client,
        prompt_builder=FilePromptBuilder(template_path, rules_path),
        llm_gateway=StubLLMGateway(),
        response_parser=JsonResponseParser(),
    )

    summary, results = orchestrator.run()
    output = {
        "run_id": summary.run_id,
        "total": summary.total,
        "updated": summary.updated,
        "skipped": summary.skipped,
        "failed": summary.failed,
        "duration_seconds": round(summary.duration_seconds, 3),
        "results": [
            {"ticket_id": r.ticket_id, "status": r.status.value, "message": r.message}
            for r in results
        ],
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
