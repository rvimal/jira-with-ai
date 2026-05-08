from __future__ import annotations

import json
import logging

from app.llm.client import LlmClient
from app.llm.prompt_builder import build_ticket_prompt
from app.mcp.jira_service import JiraService
from app.mcp.models import TicketSummary, UpdateResult
from app.prompts.loader import PromptAssets


def process_ticket(
    *,
    ticket: TicketSummary,
    prompt_assets: PromptAssets,
    llm_client: LlmClient,
    jira_service: JiraService,
    logger: logging.Logger,
    run_id: str,
    job_name: str,
) -> UpdateResult:
    ticket_logger = logging.LoggerAdapter(logger, {"ticket_id": ticket.key, "run_id": run_id, "job_name": job_name})
    ticket_logger.info("Fetching ticket details")
    details = jira_service.get_ticket(ticket.ticket_id)

    prompt = build_ticket_prompt(prompt_assets=prompt_assets, ticket=details, run_id=run_id, job_name=job_name)
    ticket_logger.info("Requesting LLM completion")
    response = llm_client.generate(prompt, metadata={"ticket_id": ticket.ticket_id, "ticket_key": ticket.key})

    update_payload = _parse_update_payload(response.text)
    ticket_logger.info("Updating ticket through MCP")
    return jira_service.update_ticket(ticket.ticket_id, update_payload)


def _parse_update_payload(text: str) -> dict[str, object]:
    normalized = text.strip()
    if normalized.startswith("```"):
        normalized = normalized.strip("`")
        if normalized.startswith("json"):
            normalized = normalized[4:].strip()
    data = json.loads(normalized)
    if not isinstance(data, dict):
        raise ValueError("LLM response must be a JSON object")

    update = data.get("update", data)
    if not isinstance(update, dict):
        raise ValueError("LLM update payload must be a JSON object")
    return update