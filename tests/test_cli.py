from __future__ import annotations

from pathlib import Path

from md2ipynb import cli


def test_agents_flag_prints_packaged_quickstart_and_local_instructions(capsys, monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "instructions.md").write_text("# Notebook authoring instructions\n\nUse sentence case headers.\n", encoding="utf-8")

    exit_code = cli.main(["--agents"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "# md2ipynb terminal quickstart" in captured.out
    assert "md2ipynb config show" in captured.out
    assert "## Instructions" in captured.out
    assert "Use sentence case headers." in captured.out


def test_agents_flag_short_circuits_subcommand_parsing(capsys) -> None:
    exit_code = cli.main(["ipynb2md", "--agents"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Print this guide" in captured.out