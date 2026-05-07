from __future__ import annotations

import json


class StubLLMGateway:
    """Deterministic stub provider used for local testing and CI."""

    def score_ticket(self, prompt: str) -> str:
        score = min(100, max(0, len(prompt) % 101))
        response = {
            "ticket_id": self._extract_ticket_id(prompt),
            "score": score,
            "reason": "Stub score based on prompt length for deterministic tests.",
            "confidence": round(min(1.0, 0.5 + (score / 200)), 2),
        }
        return json.dumps(response)

    @staticmethod
    def _extract_ticket_id(prompt: str) -> str:
        marker = "Ticket ID:"
        for line in prompt.splitlines():
            if line.startswith(marker):
                return line.replace(marker, "").strip()
        return "UNKNOWN-0"
