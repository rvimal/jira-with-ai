from __future__ import annotations

import json

from app.mcp.models import TicketDetails
from app.prompts.loader import PromptAssets


def build_ticket_prompt(prompt_assets: PromptAssets, ticket: TicketDetails, run_id: str, job_name: str) -> str:
    instruction_text = "\n\n".join(file.content.strip() for file in prompt_assets.instructions)
    example_text = "\n\n".join(file.content.strip() for file in prompt_assets.examples)
    ticket_json = json.dumps(ticket.raw, indent=2, ensure_ascii=True, sort_keys=True)

    return (
        "You are processing Jira work items through an automated workflow.\n\n"
        f"Job Name: {job_name}\n"
        f"Run ID: {run_id}\n\n"
        "Instructions:\n"
        f"{instruction_text}\n\n"
        "Examples:\n"
        f"{example_text}\n\n"
        "Ticket Data:\n"
        f"{ticket_json}\n\n"
        "Return JSON only. The JSON must match this shape:\n"
        '{"update": {"fields": {}}, "reason": "short explanation"}'
    )