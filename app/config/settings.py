from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class Settings:
    app_env: str = "dev"
    log_level: str = "INFO"
    jira_base_url: str = ""
    jira_project_keys: str = ""
    jira_jql: str = ""
    jira_score_field: str = ""
    llm_provider: str = "stub"
    llm_model: str = "gpt-oss"
    max_tickets_per_run: int = 100
    concurrency: int = 4
    request_timeout_seconds: int = 30
    retry_attempts: int = 2


    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            app_env=os.getenv("APP_ENV", "dev"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            jira_base_url=os.getenv("JIRA_BASE_URL", ""),
            jira_project_keys=os.getenv("JIRA_PROJECT_KEYS", ""),
            jira_jql=os.getenv("JIRA_JQL", ""),
            jira_score_field=os.getenv("JIRA_SCORE_FIELD", ""),
            llm_provider=os.getenv("LLM_PROVIDER", "stub"),
            llm_model=os.getenv("LLM_MODEL", "gpt-oss"),
            max_tickets_per_run=int(os.getenv("MAX_TICKETS_PER_RUN", "100")),
            concurrency=int(os.getenv("CONCURRENCY", "4")),
            request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30")),
            retry_attempts=int(os.getenv("RETRY_ATTEMPTS", "2")),
        )
