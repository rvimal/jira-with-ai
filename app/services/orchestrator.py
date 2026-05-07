from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.config.settings import Settings
from app.models import RunSummary, Ticket, TicketProcessResult, TicketStatus
from app.services.interfaces import (
    JiraReadClient,
    JiraWriteClient,
    LLMGateway,
    PromptBuilder,
    ResponseParser,
)
from app.services.response_parser import ResponseValidationError


class BacklogPrioritizationOrchestrator:
    def __init__(
        self,
        settings: Settings,
        read_client: JiraReadClient,
        write_client: JiraWriteClient,
        prompt_builder: PromptBuilder,
        llm_gateway: LLMGateway,
        response_parser: ResponseParser,
    ) -> None:
        self.settings = settings
        self.read_client = read_client
        self.write_client = write_client
        self.prompt_builder = prompt_builder
        self.llm_gateway = llm_gateway
        self.response_parser = response_parser

    def run(self) -> tuple[RunSummary, list[TicketProcessResult]]:
        run_id = str(uuid4())
        started_at = datetime.now(UTC)
        tickets = self.read_client.fetch_backlog(
            jql=self.settings.jira_jql,
            max_items=self.settings.max_tickets_per_run,
        )

        results: list[TicketProcessResult] = []
        for ticket in tickets:
            results.append(self._process_ticket(ticket))

        summary = RunSummary(
            run_id=run_id,
            total=len(results),
            updated=sum(1 for r in results if r.status == TicketStatus.UPDATED),
            skipped=sum(1 for r in results if r.status == TicketStatus.SKIPPED),
            failed=sum(1 for r in results if r.status == TicketStatus.FAILED),
            started_at=started_at,
            finished_at=datetime.now(UTC),
        )
        return summary, results

    def _process_ticket(self, ticket: Ticket) -> TicketProcessResult:
        prompt = self.prompt_builder.build_prompt(ticket)

        for attempt in range(1, self.settings.retry_attempts + 2):
            try:
                raw_response = self.llm_gateway.score_ticket(prompt)
                result = self.response_parser.parse(raw_response)
            except ResponseValidationError as exc:
                if attempt <= self.settings.retry_attempts:
                    continue
                return TicketProcessResult(
                    ticket_id=ticket.ticket_id,
                    status=TicketStatus.FAILED,
                    message=f"Invalid model output after retries: {exc}",
                )

            if ticket.existing_score == result.score:
                return TicketProcessResult(
                    ticket_id=ticket.ticket_id,
                    status=TicketStatus.SKIPPED,
                    message="Score unchanged; update skipped.",
                )

            self.write_client.update_score(
                ticket.ticket_id,
                self.settings.jira_score_field,
                result.score,
            )
            return TicketProcessResult(
                ticket_id=ticket.ticket_id,
                status=TicketStatus.UPDATED,
                message="Score updated successfully.",
            )

        return TicketProcessResult(
            ticket_id=ticket.ticket_id,
            status=TicketStatus.FAILED,
            message="Unexpected failure path.",
        )
