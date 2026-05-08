# LLM Client Implementation Plan

## Objective

Implement a Python-based scheduled client that:

- authenticates to an LLM API using `token`, `url`, and `certificate`
- supports non-streaming responses first, with a clean path to add streaming later
- connects to one or more configurable MCP servers using `url` and `token`
- reads prompt and example files from a configured folder
- executes instruction-driven workflows to fetch Jira ticket details, process them with the LLM, and update Jira through MCP
- stores structured logs for scheduler and troubleshooting use

## Scope

Included in this phase:

- Python client architecture
- configuration model for LLM and MCP connectivity
- prompt/example file loading
- orchestration flow for cron or scheduler execution
- logging and failure handling strategy
- extension points for future streaming support

Explicitly excluded for now:

- unit tests, integration tests, and test scaffolding
- streaming LLM responses in the first implementation

## Target Flow

1. A scheduler or cron job starts the Python script.
2. The script loads runtime configuration.
3. The client reads instruction, prompt, and example files from a configured folder.
4. The client connects to the configured MCP server(s).
5. The workflow requests Jira ticket details through MCP.
6. The workflow assembles the prompt using instructions, examples, and ticket data.
7. The client sends a non-streaming request to the LLM.
8. The workflow parses the LLM response and determines required ticket updates.
9. The workflow sends Jira update calls through MCP.
10. The script writes logs for start, progress, results, and failures.

## Proposed Project Structure

```text
app/
  main.py
  config.py
  logging_config.py
  orchestrator/
    job_runner.py
    workflow_engine.py
  llm/
    client.py
    models.py
    prompt_builder.py
  mcp/
    client.py
    models.py
    jira_service.py
  prompts/
    loader.py
  workflows/
    ticket_processor.py
  utils/
    file_io.py
    retry.py
    time.py
prompt_assets/
  instructions/
  examples/
logs/
```

If the repository already has a preferred package layout, keep the same structure and place these modules into the existing package hierarchy rather than creating a parallel design.

## Configuration Design

Use a single typed configuration layer loaded from environment variables and optional config files.

### LLM configuration

- `LLM_BASE_URL`
- `LLM_TOKEN`
- `LLM_CERT_PATH`
- `LLM_MODEL`
- `LLM_TIMEOUT_SECONDS`
- `LLM_VERIFY_SSL` or equivalent certificate verification setting
- `LLM_STREAMING_ENABLED=false` for now

### MCP configuration

- `MCP_BASE_URL`
- `MCP_TOKEN`
- `MCP_TIMEOUT_SECONDS`
- optional support for multiple MCP targets later through a list-based config

### File and runtime configuration

- `PROMPT_ROOT_DIR`
- `INSTRUCTION_FILE`
- `EXAMPLES_DIR`
- `LOG_DIR`
- `LOG_LEVEL`
- `JOB_NAME`

### Design requirements

- validate required configuration at startup and fail fast with clear errors
- keep secrets only in environment or secret store, never in source files
- isolate certificate handling in config/bootstrap logic so both LLM and MCP clients can reuse it if needed later

## LLM Client Plan

### Responsibilities

- build authenticated HTTPS requests to the configured LLM endpoint
- send non-streaming inference requests
- return structured response objects to the workflow layer
- handle request timeouts, API errors, and TLS/certificate settings

### Implementation notes

- use a standard Python HTTP client such as `httpx` or `requests`
- prefer `httpx` if future async or streaming support is likely
- implement a small adapter interface so streaming can be added later without changing orchestration code

### Interface shape

Example responsibilities for the client API:

- `generate(prompt: str, metadata: dict | None = None) -> LlmResponse`
- no streaming parameter exposed in v1 beyond an internal feature flag defaulted to `false`
- response object should include raw text, request id if available, usage metadata if available, and error details when applicable

### Future streaming readiness

- keep response parsing separate from transport
- define a stable request/response model now
- reserve a second method such as `stream_generate(...)` for later rather than overloading v1 behavior

## MCP Client Plan

### Responsibilities

- connect to MCP server using configurable `url` and `token`
- expose MCP operations needed by the workflow
- wrap MCP-specific request/response details behind a Python client abstraction

### Initial MCP capabilities

- fetch Jira ticket details
- fetch any additional reference data needed for prompt context
- update Jira tickets after LLM processing
- emit operation-level logs for all outbound MCP calls

### Interface shape

- `get_ticket(ticket_id: str) -> TicketDetails`
- `search_tickets(query: str) -> list[TicketDetails]`
- `update_ticket(ticket_id: str, payload: dict) -> UpdateResult`

If the MCP server uses generic tool invocation instead of typed endpoints, add a lower-level method such as `call_tool(name: str, arguments: dict)` and build Jira-specific helpers on top of it.

## Prompt and Example File Loading

### Requirements

- read several files from a specific folder
- separate instruction files from example files
- support deterministic load order so cron runs are reproducible

### Folder strategy

- `prompt_assets/instructions/` for task instructions
- `prompt_assets/examples/` for one or more example files

### Loader behavior

- load files by extension such as `.md`, `.txt`, or `.yaml` based on team preference
- sort files by filename before reading
- combine content into a structured prompt payload instead of plain string concatenation only
- log which files were loaded for each run
- fail with a clear startup error if required files are missing

### Prompt assembly

Build the final prompt from:

- global instruction content
- workflow-specific instruction content
- example content
- current Jira ticket data from MCP
- execution metadata when useful, such as run timestamp or job name

## Orchestration Flow

### Entry point

`main.py` should:

- initialize config
- initialize logging
- build LLM and MCP clients
- create the workflow runner
- execute one scheduled run
- return a non-zero exit code on failure

### Workflow runner

The workflow runner should:

1. load prompt assets
2. determine the target Jira tickets to process
3. fetch each ticket from MCP
4. build prompt input for the ticket
5. call the LLM client
6. validate or normalize the LLM output
7. send update requests through MCP
8. record success or failure for each ticket
9. summarize the run in logs

### Ticket processing strategy

- process tickets one by one first for operational simplicity
- keep the design open for later batching or concurrency
- store per-ticket execution status to avoid losing visibility when one ticket fails

## Logging Plan

### Logging goals

- support cron and scheduler operation
- provide enough detail to diagnose failures without exposing secrets
- support both console and file-based logging if needed

### Minimum logging events

- job start and finish
- config validation success or failure
- prompt files loaded
- MCP request start and result summary
- LLM request start and result summary
- per-ticket processing outcome
- retry attempts
- unhandled exceptions with stack trace

### Logging format

- structured logging preferred, such as JSON or key-value logs
- include `job_name`, `run_id`, `ticket_id`, and external request correlation ids when available
- never log tokens or certificate contents

## Error Handling and Reliability

### Failure handling

- fail fast on invalid startup configuration
- use request timeouts for both LLM and MCP calls
- implement bounded retries for transient network errors
- distinguish retriable failures from validation or data errors
- continue processing remaining tickets when one ticket fails, unless failure is global

### Operational safeguards

- validate LLM output before sending Jira updates
- keep update payload creation explicit and auditable
- consider writing a per-run summary file or final structured log record for scheduler monitoring

## Suggested Implementation Phases

### Phase 1: Bootstrap

- set up Python package structure
- add typed config loader
- add logging bootstrap
- create CLI entry point for scheduler execution

### Phase 2: LLM client v1

- implement non-streaming authenticated LLM client
- support token, URL, timeout, and certificate configuration
- define request and response models

### Phase 3: MCP client v1

- implement configurable MCP client with token and URL
- add Jira-focused helper methods on top of the generic client
- add request logging and timeout handling

### Phase 4: Prompt asset loading

- implement folder-based instruction and example loaders
- add deterministic file ordering
- build prompt assembly utilities

### Phase 5: Workflow orchestration

- implement scheduled job runner
- fetch ticket details through MCP
- call LLM and interpret response
- send Jira updates through MCP
- log per-ticket and per-run results

### Phase 6: Hardening

- improve retry behavior
- improve validation of LLM outputs
- add clearer run summaries and operational diagnostics
- prepare interface seams for future streaming support

## Example End-to-End Scenario

1. Cron starts the script every 15 minutes.
2. The script loads config and creates a new `run_id`.
3. The prompt loader reads instruction files and example files from the configured directory.
4. The MCP client searches for Jira tickets that need processing.
5. For each ticket, the workflow fetches full ticket details through MCP.
6. The prompt builder combines instructions, examples, and ticket data.
7. The LLM client sends a non-streaming completion request.
8. The workflow converts the LLM output into a Jira update payload.
9. The MCP client updates the Jira ticket.
10. Logs capture the ticket result and final run summary.

## Deferred Items

- streaming LLM responses
- test implementation
- parallel ticket execution
- persistent run-state storage or idempotency tracking if later required
- multiple MCP server routing if later required

## Recommended First Deliverable

Build the smallest usable vertical slice first:

1. load config
2. read instruction and example files from disk
3. fetch one Jira ticket through MCP
4. send one non-streaming LLM request
5. update the ticket through MCP
6. write structured logs for the full run

This will validate the network, auth, certificate, prompt-loading, and workflow assumptions before expanding to multi-ticket processing or streaming support.