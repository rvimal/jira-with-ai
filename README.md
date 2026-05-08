# jira-with-ai

Python worker that runs on a scheduler, reads prompt assets from disk, calls a non-streaming LLM endpoint, fetches and updates Jira data through an MCP server, and writes structured logs for each run.

## Current Status

Implemented in the current slice:

- environment-driven configuration for LLM, MCP, prompt folders, and job settings
- non-streaming LLM client using token, URL, and certificate
- MCP client using configurable URL and token
- prompt and example file loading from local folders
- scheduled job style orchestration for ticket search, fetch, LLM processing, and update
- structured JSON logging to console and log file

Deferred for now:

- streaming LLM responses
- unit tests and integration tests
- concurrency and parallel ticket processing

## Project Layout

```text
app/
	main.py
	config.py
	logging_config.py
	llm/
	mcp/
	orchestrator/
	prompts/
	workflows/
	utils/
.env.example
plan.md
prompt_assets/
	instructions/
	examples/
```

## Runtime Flow

1. A scheduler or cron job starts the Python script.
2. The app loads configuration from environment variables.
3. Prompt instructions and examples are loaded from `prompt_assets/`.
4. The MCP client searches for Jira tickets to process.
5. Each ticket is fetched in detail through MCP.
6. A prompt is assembled from instructions, examples, and ticket data.
7. The LLM client sends a non-streaming request.
8. The LLM response is parsed as JSON.
9. The Jira update payload is sent back through MCP.
10. The run is logged with a `run_id` and per-ticket status.

## Requirements

- Python 3.11+
- network access to the target LLM endpoint
- network access to the target MCP server
- valid bearer tokens for both services
- a CA certificate file for the LLM endpoint

## Configuration

Copy values from `.env.example` into your runtime environment.

### LLM settings

- `LLM_BASE_URL`: non-streaming inference endpoint
- `LLM_TOKEN`: bearer token for the LLM API
- `LLM_CERT_PATH`: CA certificate path used for TLS verification
- `LLM_MODEL`: model name sent in the request payload
- `LLM_TIMEOUT_SECONDS`: request timeout in seconds
- `LLM_VERIFY_SSL`: `true` or `false`

### MCP settings

- `MCP_BASE_URL`: MCP HTTP gateway base URL
- `MCP_TOKEN`: bearer token for MCP
- `MCP_TIMEOUT_SECONDS`: request timeout in seconds
- `MCP_VERIFY_SSL`: `true` or `false`
- `MCP_TOOL_CALL_PATH`: path appended to `MCP_BASE_URL` for tool calls
- `MCP_SEARCH_TICKETS_TOOL`: tool name used to search Jira tickets
- `MCP_GET_TICKET_TOOL`: tool name used to fetch ticket details
- `MCP_UPDATE_TICKET_TOOL`: tool name used to update Jira tickets

### Prompt and job settings

- `PROMPT_ROOT_DIR`: root folder for prompt assets
- `INSTRUCTIONS_DIR`: folder containing instruction files
- `EXAMPLES_DIR`: folder containing example files
- `LOG_DIR`: output folder for structured logs
- `LOG_LEVEL`: logger level
- `JOB_NAME`: job name written into logs
- `JIRA_TICKET_SEARCH_QUERY`: ticket search query sent through MCP
- `MAX_TICKETS`: maximum tickets processed in one run

## Prompt Assets

The worker expects prompt assets on disk.

- `prompt_assets/instructions/`: task instructions loaded in sorted filename order
- `prompt_assets/examples/`: example files loaded in sorted filename order

At least one instruction file and one example file must exist or startup will fail.

## How to Run

Run directly with Python:

```bash
python -m app.main
```

Or install the package locally and use the console script:

```bash
pip install -e .
jira-with-ai
```

## Cron Example

Example cron entry that runs every 15 minutes:

```cron
*/15 * * * * cd /workspaces/jira-with-ai && export $(cat .env | xargs) && python -m app.main >> logs/cron.log 2>&1
```

Use your actual environment-loading method if secrets come from a secret manager, systemd unit, container runtime, or CI/CD scheduler.

## Logging

The app writes structured JSON logs to:

- stdout
- `logs/<JOB_NAME>.log`

Each record includes run-level identifiers such as `run_id`, `job_name`, and, when available, `ticket_id`.

## MCP Assumption

The current implementation assumes an HTTP MCP gateway that accepts a `POST` request to:

- `MCP_BASE_URL + MCP_TOOL_CALL_PATH`

with a JSON body shaped like:

```json
{
	"name": "tool_name",
	"arguments": {
		"key": "value"
	}
}
```

If your MCP server uses a different transport or payload format, update the client implementation in `app/mcp/client.py` and the Jira-specific mapping in `app/mcp/jira_service.py`.

## LLM Response Assumption

The workflow expects the LLM to return JSON that can be parsed into a Jira update payload. The recommended shape is:

```json
{
	"update": {
		"fields": {}
	},
	"reason": "short explanation"
}
```

The `update` object is sent to the Jira update MCP tool.

## Validation

Focused validation used for the current implementation:

```bash
python -m compileall app
```