# jira-with-ai

Simple Node.js agent platform for Jira automation using:

- LLM reasoning (OpenAI-compatible API for GPT-OSS or Qwen)
- MCP tool execution (`@modelcontextprotocol/sdk`)
- Human-configured prompts per action

The platform owns execution and guardrails. Users own prompts.

## Features

- Configurable LLM URL, model, token, and TLS certificate files
- Configurable MCP command, args, and tool names
- MCP connection test command (`test-mcp`)
- LLM connection test command (`test-llm`)
- Run modes:
    - `--dry-run` preview only
    - `--approve` prompt before update
    - `--execute` apply updates
    - `--schedule` periodic execution
    - `--rollback` revert the last execute run for an action
- Guardrails:
    - score range 0-100
    - required field check
    - skip closed tickets
    - skip manually locked tickets
- Audit log in JSONL format for execute and rollback

## Folder structure

```text
.
├── actions/
│   └── risk/
│       ├── system.md
│       ├── instructions.md
│       └── examples.json
├── config/
│   └── default.json
├── logs/
│   └── audit.jsonl (created automatically)
└── src/
        ├── index.js
        └── lib/
```

## Action contract

Each action folder must have:

- `system.md`
- `instructions.md`
- `examples.json` (optional)

Example action path:

```text
actions/risk/
```

## Setup

```bash
npm install
```

Optional env overrides are available in `.env.example`.

## Configuration

Default config is in `config/default.json`.

Key settings:

- `llm.url`, `llm.model`, `llm.token`
- `llm.caFile`, `llm.certFile`, `llm.keyFile`, `llm.insecureSkipTlsVerify`
- `mcp.command`, `mcp.args`
- `mcp.tools.fetchTickets`, `mcp.tools.updateTicket`
- `jira.query`, `jira.scoreField`, `jira.lockField`, `jira.closedStatuses`
- `actionsDir`, `auditLogFile`, `scheduleIntervalMs`

## CLI commands

```bash
agent test-llm
agent test-mcp

agent run --action risk --dry-run
agent run --action risk --approve
agent run --action risk --execute
agent run --action risk --execute --schedule --interval-ms 600000
agent run --action risk --rollback
```

You can also run via npm:

```bash
npm run agent -- test-llm
npm run agent -- run --action risk --dry-run
```

## Execution flow

1. Connect to MCP
2. List MCP tools
3. Fetch Jira tickets through MCP fetch tool
4. Run LLM with action prompts + ticket data
5. Validate proposals with guardrails
6. Return dry-run preview or apply updates
7. Write audit log

## Notes

- This repo intentionally keeps implementation simple.
- Unit tests are intentionally not included.
