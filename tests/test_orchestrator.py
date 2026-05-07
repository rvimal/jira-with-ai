from app.config.settings import Settings
from app.models import Ticket, TicketStatus
from app.services.jira_client import InMemoryJiraClient
from app.services.orchestrator import BacklogPrioritizationOrchestrator
from app.services.prompt_builder import FilePromptBuilder
from app.services.response_parser import JsonResponseParser


class DeterministicLLM:
    def score_ticket(self, prompt: str) -> str:
        if "PROJ-1" in prompt:
            return '{"ticket_id":"PROJ-1","score":75,"reason":"Important","confidence":0.8}'
        return '{"ticket_id":"PROJ-2","score":50,"reason":"Moderate","confidence":0.7}'


def test_orchestrator_updates_and_skips(tmp_path) -> None:
    template = tmp_path / "template.txt"
    rules = tmp_path / "rules.md"
    template.write_text(
        "Ticket ID: {ticket_id}\nSummary: {summary}\nRules: {rules}\n",
        encoding="utf-8",
    )
    rules.write_text("Use impact and urgency", encoding="utf-8")

    tickets = [
        Ticket(ticket_id="PROJ-1", summary="A", description="B", existing_score=10),
        Ticket(ticket_id="PROJ-2", summary="A", description="B", existing_score=50),
    ]

    settings = Settings(jira_jql="project=PROJ", jira_score_field="customfield_1", retry_attempts=1)
    client = InMemoryJiraClient(tickets)

    orchestrator = BacklogPrioritizationOrchestrator(
        settings=settings,
        read_client=client,
        write_client=client,
        prompt_builder=FilePromptBuilder(template, rules),
        llm_gateway=DeterministicLLM(),
        response_parser=JsonResponseParser(),
    )

    summary, results = orchestrator.run()

    assert summary.total == 2
    assert summary.updated == 1
    assert summary.skipped == 1
    assert summary.failed == 0
    assert results[0].status == TicketStatus.UPDATED
    assert results[1].status == TicketStatus.SKIPPED
    assert client.tickets["PROJ-1"].existing_score == 75
