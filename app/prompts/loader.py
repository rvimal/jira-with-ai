from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.config import PromptSettings


SUPPORTED_EXTENSIONS = {".md", ".txt", ".yaml", ".yml", ".json"}


@dataclass(frozen=True)
class PromptFile:
    path: Path
    content: str


@dataclass(frozen=True)
class PromptAssets:
    instructions: list[PromptFile]
    examples: list[PromptFile]


def load_prompt_assets(settings: PromptSettings) -> PromptAssets:
    instructions = _read_directory(settings.instructions_dir)
    examples = _read_directory(settings.examples_dir)

    if not instructions:
        raise FileNotFoundError(f"No instruction files found in {settings.instructions_dir}")
    if not examples:
        raise FileNotFoundError(f"No example files found in {settings.examples_dir}")

    return PromptAssets(instructions=instructions, examples=examples)


def _read_directory(directory: Path) -> list[PromptFile]:
    files = [path for path in sorted(directory.iterdir()) if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS]
    return [PromptFile(path=path, content=path.read_text(encoding="utf-8")) for path in files]