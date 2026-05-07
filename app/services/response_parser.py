from __future__ import annotations

import json

from app.models import ScoreResult


class ResponseValidationError(ValueError):
    pass


class JsonResponseParser:
    def parse(self, raw_text: str) -> ScoreResult:
        try:
            payload = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise ResponseValidationError("Model output is not valid JSON.") from exc

        required = {"ticket_id", "score", "reason", "confidence"}
        missing = required.difference(payload.keys())
        if missing:
            raise ResponseValidationError(f"Missing keys: {sorted(missing)}")

        score = payload["score"]
        confidence = payload["confidence"]

        if not isinstance(score, int) or not 0 <= score <= 100:
            raise ResponseValidationError("score must be an integer in range 0..100")

        if not isinstance(confidence, (float, int)) or not 0.0 <= float(confidence) <= 1.0:
            raise ResponseValidationError("confidence must be a number in range 0.0..1.0")

        reason = payload["reason"]
        ticket_id = payload["ticket_id"]
        if not isinstance(reason, str) or not reason.strip():
            raise ResponseValidationError("reason must be a non-empty string")
        if not isinstance(ticket_id, str) or not ticket_id.strip():
            raise ResponseValidationError("ticket_id must be a non-empty string")

        return ScoreResult(
            ticket_id=ticket_id,
            score=score,
            reason=reason.strip(),
            confidence=float(confidence),
        )
