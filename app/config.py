from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class LlmSettings:
    base_url: str
    token: str
    cert_path: Path
    model: str
    timeout_seconds: int
    verify_ssl: bool


@dataclass(frozen=True)
class McpToolSettings:
    tool_call_path: str
    search_tickets_tool: str
    get_ticket_tool: str
    update_ticket_tool: str


@dataclass(frozen=True)
class McpSettings:
    base_url: str
    token: str
    timeout_seconds: int
    verify_ssl: bool
    cert_path: Path | None
    tools: McpToolSettings


@dataclass(frozen=True)
class PromptSettings:
    root_dir: Path
    instructions_dir: Path
    examples_dir: Path


@dataclass(frozen=True)
class LoggingSettings:
    level: str
    log_dir: Path


@dataclass(frozen=True)
class JobSettings:
    name: str
    ticket_search_query: str
    max_tickets: int


@dataclass(frozen=True)
class AppConfig:
    llm: LlmSettings
    mcp: McpSettings
    prompts: PromptSettings
    logging: LoggingSettings
    job: JobSettings


def load_config() -> AppConfig:
    prompt_root = _path_from_env("PROMPT_ROOT_DIR", default="prompt_assets")
    instructions_dir = _path_from_env("INSTRUCTIONS_DIR", default=str(prompt_root / "instructions"))
    examples_dir = _path_from_env("EXAMPLES_DIR", default=str(prompt_root / "examples"))
    log_dir = _path_from_env("LOG_DIR", default="logs")

    llm = LlmSettings(
        base_url=_required_env("LLM_BASE_URL"),
        token=_required_env("LLM_TOKEN"),
        cert_path=_existing_file_from_env("LLM_CERT_PATH"),
        model=_env("LLM_MODEL", "default"),
        timeout_seconds=_int_env("LLM_TIMEOUT_SECONDS", 60),
        verify_ssl=_bool_env("LLM_VERIFY_SSL", True),
    )

    mcp = McpSettings(
        base_url=_required_env("MCP_BASE_URL"),
        token=_required_env("MCP_TOKEN"),
        timeout_seconds=_int_env("MCP_TIMEOUT_SECONDS", 60),
        verify_ssl=_bool_env("MCP_VERIFY_SSL", True),
        cert_path=_optional_existing_file_from_env("MCP_CERT_PATH"),
        tools=McpToolSettings(
            tool_call_path=_normalized_path(_env("MCP_TOOL_CALL_PATH", "/tools/call")),
            search_tickets_tool=_env("MCP_SEARCH_TICKETS_TOOL", "search_tickets"),
            get_ticket_tool=_env("MCP_GET_TICKET_TOOL", "get_ticket"),
            update_ticket_tool=_env("MCP_UPDATE_TICKET_TOOL", "update_ticket"),
        ),
    )

    prompts = PromptSettings(
        root_dir=prompt_root,
        instructions_dir=instructions_dir,
        examples_dir=examples_dir,
    )
    _ensure_directory(prompts.root_dir, "PROMPT_ROOT_DIR")
    _ensure_directory(prompts.instructions_dir, "INSTRUCTIONS_DIR")
    _ensure_directory(prompts.examples_dir, "EXAMPLES_DIR")

    logging = LoggingSettings(
        level=_env("LOG_LEVEL", "INFO").upper(),
        log_dir=log_dir,
    )

    job = JobSettings(
        name=_env("JOB_NAME", "jira-with-ai"),
        ticket_search_query=_env("JIRA_TICKET_SEARCH_QUERY", "status = \"To Do\""),
        max_tickets=_int_env("MAX_TICKETS", 25),
    )

    return AppConfig(llm=llm, mcp=mcp, prompts=prompts, logging=logging, job=job)


def _env(name: str, default: str) -> str:
    return os.getenv(name, default).strip()


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigError(f"Missing required environment variable: {name}")
    return value


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ConfigError(f"Invalid boolean value for {name}: {value}")


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ConfigError(f"Invalid integer value for {name}: {value}") from exc


def _path_from_env(name: str, default: str) -> Path:
    raw_value = os.getenv(name, default).strip()
    return Path(raw_value).expanduser().resolve()


def _existing_file_from_env(name: str) -> Path:
    path = _path_from_env(name, _required_env(name))
    if not path.is_file():
        raise ConfigError(f"Configured path for {name} is not a file: {path}")
    return path


def _optional_existing_file_from_env(name: str) -> Path | None:
    value = os.getenv(name)
    if value is None or not value.strip():
        return None
    path = Path(value.strip()).expanduser().resolve()
    if not path.is_file():
        raise ConfigError(f"Configured path for {name} is not a file: {path}")
    return path


def _ensure_directory(path: Path, env_name: str) -> None:
    if not path.is_dir():
        raise ConfigError(f"Configured path for {env_name} is not a directory: {path}")


def _normalized_path(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ConfigError("MCP tool call path cannot be empty")
    return stripped if stripped.startswith("/") else f"/{stripped}"