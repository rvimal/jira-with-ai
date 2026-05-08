from __future__ import annotations

import json
from urllib import error, request

from app.config import LlmSettings
from app.llm.models import LlmResponse
from app.utils.retry import retry_call


class LlmClient:
    def __init__(self, settings: LlmSettings) -> None:
        self._settings = settings
        self._ssl_context = _build_ssl_context(settings.cert_path, settings.verify_ssl)

    def generate(self, prompt: str, metadata: dict[str, object] | None = None) -> LlmResponse:
        payload = {
            "model": self._settings.model,
            "input": prompt,
            "stream": False,
            "metadata": metadata or {},
        }

        def send_request() -> LlmResponse:
            body = json.dumps(payload).encode("utf-8")
            http_request = request.Request(
                self._settings.base_url,
                data=body,
                headers={
                    "Authorization": f"Bearer {self._settings.token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                method="POST",
            )
            with request.urlopen(http_request, timeout=self._settings.timeout_seconds, context=self._ssl_context) as response:
                raw_payload = json.loads(response.read().decode("utf-8"))
                return _parse_response(raw_payload)

        return retry_call(
            send_request,
            attempts=3,
            delay_seconds=1.0,
            retriable_exceptions=(TimeoutError, error.URLError),
        )


def _build_ssl_context(cert_path, verify_ssl: bool):
    import ssl

    if not verify_ssl:
        return ssl._create_unverified_context()
    return ssl.create_default_context(cafile=str(cert_path))


def _parse_response(payload: dict[str, object]) -> LlmResponse:
    request_id = _as_optional_string(payload.get("id") or payload.get("request_id"))
    usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
    text = _extract_text(payload)
    return LlmResponse(text=text, raw_response=payload, request_id=request_id, usage=usage)


def _extract_text(payload: dict[str, object]) -> str:
    direct_keys = ("text", "output_text", "response", "content")
    for key in direct_keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value

    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        first_choice = choices[0]
        if isinstance(first_choice, dict):
            message = first_choice.get("message")
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str) and content.strip():
                    return content
            text = first_choice.get("text")
            if isinstance(text, str) and text.strip():
                return text

    return json.dumps(payload, ensure_ascii=True)


def _as_optional_string(value: object) -> str | None:
    return value if isinstance(value, str) else None