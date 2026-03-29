from __future__ import annotations

import json
from pathlib import Path

from md2ipynb.config import AppConfig, build_cursor_rule_text, install_cursor_integration, load_config, write_config


def test_config_round_trip(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config = AppConfig(
        python_executable="C:/Python/python.exe",
        instructions_text="Use sentence case headers.",
        markdown_edit_cell_threshold=3,
        config_path=config_path,
    )

    write_config(config)
    loaded = load_config(config_path)

    assert loaded.python_executable == "C:/Python/python.exe"
    assert loaded.instructions_text == "Use sentence case headers."
    assert loaded.markdown_edit_cell_threshold == 3


def test_install_cursor_integration_writes_rule_and_merges_mcp_config(tmp_path: Path) -> None:
    cursor_root = tmp_path / ".cursor"
    mcp_config_path = cursor_root / "mcp.json"
    mcp_config_path.parent.mkdir(parents=True, exist_ok=True)
    mcp_config_path.write_text(json.dumps({"mcpServers": {"other": {"command": "python"}}}), encoding="utf-8")

    config = AppConfig(
        python_executable="C:/Python/python.exe",
        instructions_text="Do not edit notebooks directly unless the change is tiny.",
        cursor_root=str(cursor_root),
        config_path=tmp_path / "config.toml",
    )

    installed = install_cursor_integration(config, force=True)
    payload = json.loads(installed["mcp_config_path"].read_text(encoding="utf-8"))
    rule_text = installed["rule_path"].read_text(encoding="utf-8")

    assert "other" in payload["mcpServers"]
    assert payload["mcpServers"]["md2ipynb"]["command"] == "C:/Python/python.exe"
    assert "Do not edit notebooks directly unless the change is tiny." in rule_text
    assert "Prefer md2ipynb markdown workflow" in build_cursor_rule_text(config)


def test_install_cursor_integration_handles_empty_mcp_config(tmp_path: Path) -> None:
    cursor_root = tmp_path / ".cursor"
    mcp_config_path = cursor_root / "mcp.json"
    mcp_config_path.parent.mkdir(parents=True, exist_ok=True)
    mcp_config_path.write_text("", encoding="utf-8")

    config = AppConfig(
        python_executable="C:/Python/python.exe",
        instructions_text="Prefer the markdown workflow.",
        cursor_root=str(cursor_root),
        config_path=tmp_path / "config.toml",
    )

    installed = install_cursor_integration(config, force=True)
    payload = json.loads(installed["mcp_config_path"].read_text(encoding="utf-8"))

    assert payload["mcpServers"]["md2ipynb"]["command"] == "C:/Python/python.exe"
