from __future__ import annotations

import json
from urllib import error, request

from app.config import McpSettings
from app.utils.retry import retry_call


class McpClient:
    def __init__(self, settings: McpSettings) -> None:
        self._settings = settings
        self._ssl_context = _build_ssl_context(settings.cert_path, settings.verify_ssl)

    def call_tool(self, name: str, arguments: dict[str, object]) -> dict[str, object]:
        def send_request() -> dict[str, object]:
            endpoint = f"{self._settings.base_url.rstrip('/')}{self._settings.tools.tool_call_path}"
            body = json.dumps({"name": name, "arguments": arguments}).encode("utf-8")
            http_request = request.Request(
                endpoint,
                data=body,
                headers={
                    "Authorization": f"Bearer {self._settings.token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                method="POST",
            )
            with request.urlopen(http_request, timeout=self._settings.timeout_seconds, context=self._ssl_context) as response:
                payload = json.loads(response.read().decode("utf-8"))
                return payload if isinstance(payload, dict) else {"result": payload}

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
    if cert_path is None:
        return ssl.create_default_context()
    return ssl.create_default_context(cafile=str(cert_path))