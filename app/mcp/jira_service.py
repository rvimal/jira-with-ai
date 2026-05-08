from __future__ import annotations

from app.config import McpToolSettings
from app.mcp.client import McpClient
from app.mcp.models import TicketDetails, TicketSummary, UpdateResult


class JiraService:
    def __init__(self, client: McpClient, tools: McpToolSettings) -> None:
        self._client = client
        self._tools = tools

    def search_tickets(self, query: str) -> list[TicketSummary]:
        response = self._client.call_tool(self._tools.search_tickets_tool, {"query": query})
        records = _extract_records(response)
        tickets: list[TicketSummary] = []
        for record in records:
            ticket_id = str(record.get("id") or record.get("ticket_id") or record.get("key") or "")
            key = str(record.get("key") or ticket_id)
            if ticket_id:
                tickets.append(TicketSummary(ticket_id=ticket_id, key=key, raw=record))
        return tickets

    def get_ticket(self, ticket_id: str) -> TicketDetails:
        response = self._client.call_tool(self._tools.get_ticket_tool, {"ticket_id": ticket_id})
        record = _extract_single_record(response)
        key = str(record.get("key") or ticket_id)
        return TicketDetails(ticket_id=ticket_id, key=key, raw=record)

    def update_ticket(self, ticket_id: str, payload: dict[str, object]) -> UpdateResult:
        response = self._client.call_tool(self._tools.update_ticket_tool, {"ticket_id": ticket_id, "payload": payload})
        return UpdateResult(ticket_id=ticket_id, success=True, raw=response)


def _extract_records(response: dict[str, object]) -> list[dict[str, object]]:
    result = response.get("result", response)
    if isinstance(result, list):
        return [item for item in result if isinstance(item, dict)]
    if isinstance(result, dict):
        for key in ("tickets", "items", "results", "data"):
            value = result.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def _extract_single_record(response: dict[str, object]) -> dict[str, object]:
    result = response.get("result", response)
    if isinstance(result, dict):
        return result
    return {"value": result}