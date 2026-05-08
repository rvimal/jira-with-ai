from __future__ import annotations

import logging

from app.config import ConfigError, load_config
from app.llm.client import LlmClient
from app.mcp.client import McpClient
from app.mcp.jira_service import JiraService
from app.logging_config import setup_logging
from app.orchestrator.job_runner import JobRunner
from app.utils.time import new_run_id


def main() -> int:
    try:
        config = load_config()
    except ConfigError as exc:
        logging.basicConfig(level=logging.ERROR)
        logging.getLogger("jira_with_ai").error(str(exc))
        return 2

    run_id = new_run_id()
    logger = setup_logging(config.logging, run_id=run_id, job_name=config.job.name)

    llm_client = LlmClient(config.llm)
    mcp_client = McpClient(config.mcp)
    jira_service = JiraService(mcp_client, config.mcp.tools)
    runner = JobRunner(config=config, llm_client=llm_client, jira_service=jira_service, logger=logger, run_id=run_id)
    return runner.run()


if __name__ == "__main__":
    raise SystemExit(main())