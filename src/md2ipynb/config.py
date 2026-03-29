from __future__ import annotations

import json
import os
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_CELL_THRESHOLD = 2
DEFAULT_RULE_FILENAME = "md2ipynb-workflow.mdc"


def _default_config_path() -> Path:
    override = os.environ.get("MD2IPYNB_CONFIG")
    if override:
        return Path(override).expanduser()
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "md2ipynb" / "config.toml"
    return Path.home() / ".config" / "md2ipynb" / "config.toml"


def _default_cursor_root() -> Path:
    return Path.home() / ".cursor"


def _clean_dict(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


@dataclass(slots=True)
class AppConfig:
    python_executable: str | None = None
    instructions_file: str | None = None
    instructions_text: str | None = None
    markdown_edit_cell_threshold: int = DEFAULT_CELL_THRESHOLD
    cursor_root: str | None = None
    cursor_mcp_config_path: str | None = None
    cursor_rules_dir: str | None = None
    config_path: Path = field(default_factory=_default_config_path)

    def effective_python_executable(self) -> str:
        return os.environ.get("MD2IPYNB_PYTHON_EXECUTABLE") or self.python_executable or sys.executable

    def effective_instructions(self) -> str | None:
        inline_text = os.environ.get("MD2IPYNB_INSTRUCTIONS_TEXT") or self.instructions_text
        instructions_file = os.environ.get("MD2IPYNB_INSTRUCTIONS_FILE") or self.instructions_file
        if instructions_file:
            path = Path(instructions_file).expanduser()
            if not path.is_absolute():
                path = self.config_path.parent / path
            if path.is_file():
                return path.read_text(encoding="utf-8").strip()
        if inline_text:
            return inline_text.strip()
        return None

    def effective_cursor_root(self) -> Path:
        return Path(self.cursor_root).expanduser() if self.cursor_root else _default_cursor_root()

    def effective_cursor_mcp_config_path(self) -> Path:
        if self.cursor_mcp_config_path:
            return Path(self.cursor_mcp_config_path).expanduser()
        return self.effective_cursor_root() / "mcp.json"

    def effective_cursor_rules_dir(self) -> Path:
        if self.cursor_rules_dir:
            return Path(self.cursor_rules_dir).expanduser()
        return self.effective_cursor_root() / "rules"

    def to_dict(self) -> dict[str, Any]:
        return {
            "python_executable": self.effective_python_executable(),
            "instructions_file": self.instructions_file,
            "instructions_text": self.instructions_text,
            "markdown_edit_cell_threshold": self.markdown_edit_cell_threshold,
            "cursor_root": str(self.effective_cursor_root()),
            "cursor_mcp_config_path": str(self.effective_cursor_mcp_config_path()),
            "cursor_rules_dir": str(self.effective_cursor_rules_dir()),
            "config_path": str(self.config_path),
        }


def load_config(config_path: str | os.PathLike[str] | None = None) -> AppConfig:
    resolved_path = Path(config_path).expanduser() if config_path else _default_config_path()
    if not resolved_path.exists():
        return AppConfig(config_path=resolved_path)

    data = tomllib.loads(resolved_path.read_text(encoding="utf-8"))
    cursor_data = data.get("cursor", {})
    return AppConfig(
        python_executable=data.get("python_executable"),
        instructions_file=data.get("instructions_file"),
        instructions_text=data.get("instructions_text"),
        markdown_edit_cell_threshold=data.get(
            "markdown_edit_cell_threshold",
            DEFAULT_CELL_THRESHOLD,
        ),
        cursor_root=cursor_data.get("root"),
        cursor_mcp_config_path=cursor_data.get("mcp_config_path"),
        cursor_rules_dir=cursor_data.get("rules_dir"),
        config_path=resolved_path,
    )


def _toml_escape(value: str) -> str:
    return json.dumps(value)


def serialize_config(config: AppConfig) -> str:
    lines = [
        f"python_executable = {_toml_escape(config.python_executable or '')}",
        f"instructions_file = {_toml_escape(config.instructions_file or '')}",
        f"instructions_text = {_toml_escape(config.instructions_text or '')}",
        f"markdown_edit_cell_threshold = {config.markdown_edit_cell_threshold}",
        "",
        "[cursor]",
        f"root = {_toml_escape(config.cursor_root or '')}",
        f"mcp_config_path = {_toml_escape(config.cursor_mcp_config_path or '')}",
        f"rules_dir = {_toml_escape(config.cursor_rules_dir or '')}",
        "",
    ]
    return "\n".join(lines)


def write_config(config: AppConfig, force: bool = False) -> Path:
    config.config_path.parent.mkdir(parents=True, exist_ok=True)
    if config.config_path.exists() and not force:
        raise FileExistsError(f"Config file already exists: {config.config_path}")
    config.config_path.write_text(serialize_config(config), encoding="utf-8")
    return config.config_path


def build_cursor_rule_text(config: AppConfig) -> str:
    custom_instructions = config.effective_instructions() or "No custom notebook-authoring instructions are configured."
    return "\n".join(
        [
            "---",
            'description: Prefer md2ipynb markdown workflow for notebook creation and multi-cell notebook edits',
            'globs: ["**/*.ipynb", "**/*.md"]',
            "alwaysApply: false",
            "---",
            "",
            "When a task involves a Jupyter notebook:",
            "",
            "1. If creating a notebook, author the markdown source first and convert it with `md2ipynb`.",
            f"2. If changing more than {config.markdown_edit_cell_threshold} cells, convert the notebook to markdown with `ipynb2md`, edit the markdown, and convert it back with `md2ipynb`.",
            f"3. Only edit notebook cells directly for tiny changes touching {config.markdown_edit_cell_threshold} or fewer cells.",
            "4. Keep markdown code cells fenced as ```python ... ``` and leave non-code examples as plain ``` ... ``` fences.",
            "",
            "Configured notebook instructions:",
            custom_instructions,
            "",
        ]
    )


def install_cursor_integration(config: AppConfig, force: bool = False) -> dict[str, Path]:
    rules_dir = config.effective_cursor_rules_dir()
    mcp_config_path = config.effective_cursor_mcp_config_path()
    rule_path = rules_dir / DEFAULT_RULE_FILENAME

    rules_dir.mkdir(parents=True, exist_ok=True)
    mcp_config_path.parent.mkdir(parents=True, exist_ok=True)

    server_entry = {
        "command": config.effective_python_executable(),
        "args": ["-m", "md2ipynb.mcp_server"],
        "env": _clean_dict({"MD2IPYNB_CONFIG": str(config.config_path)}),
    }

    payload: dict[str, Any] = {"mcpServers": {}}
    if mcp_config_path.exists():
        raw_text = mcp_config_path.read_text(encoding="utf-8").strip()
        if raw_text:
            parsed_payload = json.loads(raw_text)
            if isinstance(parsed_payload, dict):
                payload = parsed_payload
    payload.setdefault("mcpServers", {})["md2ipynb"] = server_entry

    if rule_path.exists() and not force:
        raise FileExistsError(f"Cursor rule already exists: {rule_path}")

    rule_path.write_text(build_cursor_rule_text(config), encoding="utf-8")
    mcp_config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    return {
        "rule_path": rule_path,
        "mcp_config_path": mcp_config_path,
    }
