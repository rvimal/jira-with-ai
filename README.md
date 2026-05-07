# jira-with-ai

Automated Jira backlog prioritization baseline in Python 3.12.

This repository now includes a runnable implementation skeleton for:
- Config loading from environment
- Backlog fetch and normalization boundary
- Prompt building from templates and scoring rules
- LLM gateway abstraction (with deterministic stub provider)
- Strict JSON response parsing and validation
- Idempotent score update behavior
- End-to-end orchestration with run summary
- Unit tests for parser and orchestrator

## Project Structure

app/
- config/: runtime settings
- services/: orchestration and integration boundaries
- prompts/: prompt templates
- examples/: scoring rules/examples
- logs/: runtime log output folder placeholder

tests/
- parser and orchestration unit tests

## Quick Start

1. Create and activate a virtual environment.
2. Install dev dependencies:

```bash
pip install -e ".[dev]"
```

3. Copy environment template and edit values:

```bash
cp .env.example .env
```

4. Run tests:

```bash
pytest
```

5. Run local demo orchestration:

```bash
python -m app.main
```

## Quality Gates

```bash
ruff check .
mypy app
pytest
```

## Notes

- Current Jira and LLM integrations use local adapters/stubs to provide a safe baseline.
- Replace in-memory adapters with real Jira MCP and model providers in the next phase.