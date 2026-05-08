from __future__ import annotations

from datetime import UTC, datetime
import json
import logging
from pathlib import Path

from app.config import LoggingSettings


class JsonFormatter(logging.Formatter):
    def __init__(self, run_id: str, job_name: str) -> None:
        super().__init__()
        self._run_id = run_id
        self._job_name = job_name

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "job_name": getattr(record, "job_name", self._job_name),
            "run_id": getattr(record, "run_id", self._run_id),
            "ticket_id": getattr(record, "ticket_id", None),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)


def setup_logging(settings: LoggingSettings, run_id: str, job_name: str) -> logging.Logger:
    logger = logging.getLogger("jira_with_ai")
    logger.setLevel(getattr(logging, settings.level, logging.INFO))
    logger.handlers.clear()

    formatter = JsonFormatter(run_id=run_id, job_name=job_name)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    settings.log_dir.mkdir(parents=True, exist_ok=True)
    log_path = Path(settings.log_dir) / f"{job_name}.log"
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.propagate = False
    return logger