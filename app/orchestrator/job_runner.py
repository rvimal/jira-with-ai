from __future__ import annotations

import logging

from app.config import AppConfig
from app.llm.client import LlmClient
from app.mcp.jira_service import JiraService
from app.prompts.loader import load_prompt_assets
from app.workflows.ticket_processor import process_ticket


class JobRunner:
    def __init__(
        self,
        *,
        config: AppConfig,
        llm_client: LlmClient,
        jira_service: JiraService,
        logger: logging.Logger,
        run_id: str,
    ) -> None:
        self._config = config
        self._llm_client = llm_client
        self._jira_service = jira_service
        self._logger = logger
        self._run_id = run_id

    def run(self) -> int:
        logger = logging.LoggerAdapter(self._logger, {"run_id": self._run_id, "job_name": self._config.job.name})
        logger.info("Job started")

        prompt_assets = load_prompt_assets(self._config.prompts)
        logger.info(
            "Loaded prompt assets",
            extra={
                "instructions": len(prompt_assets.instructions),
                "examples": len(prompt_assets.examples),
            },
        )

        tickets = self._jira_service.search_tickets(self._config.job.ticket_search_query)
        if self._config.job.max_tickets > 0:
            tickets = tickets[: self._config.job.max_tickets]

        if not tickets:
            logger.info("No tickets matched the configured query")
            return 0

        success_count = 0
        failure_count = 0

        for ticket in tickets:
            try:
                process_ticket(
                    ticket=ticket,
                    prompt_assets=prompt_assets,
                    llm_client=self._llm_client,
                    jira_service=self._jira_service,
                    logger=self._logger,
                    run_id=self._run_id,
                    job_name=self._config.job.name,
                )
                success_count += 1
            except Exception:
                failure_count += 1
                logger.exception("Ticket processing failed", extra={"ticket_id": ticket.key})

        logger.info("Job finished", extra={"success_count": success_count, "failure_count": failure_count})
        return 0 if failure_count == 0 else 1