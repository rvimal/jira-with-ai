from __future__ import annotations

import logging
from collections.abc import MutableMapping
from typing import Any


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s run_id=%(run_id)s %(message)s",
    )


class RunLoggerAdapter(logging.LoggerAdapter):
    def process(
        self,
        msg: str,
        kwargs: MutableMapping[str, Any],
    ) -> tuple[str, MutableMapping[str, Any]]:
        extra = kwargs.get("extra")
        if not isinstance(extra, dict):
            extra = {}
        adapter_extra = self.extra or {}
        run_id = adapter_extra.get("run_id", "unknown")
        extra["run_id"] = run_id
        kwargs["extra"] = extra
        return msg, kwargs
