from __future__ import annotations

from pathlib import Path

import nbformat

from md2ipynb.cli import build_parser
from md2ipynb.converter import convert_markdown_paths_to_notebooks, convert_notebook_paths_to_markdown, parse_markdown_to_notebook


def test_notebook_export_sanitizes_python_fences_in_markdown_cells(tmp_path: Path) -> None:
    notebook = nbformat.v4.new_notebook()
    notebook.cells = [
        nbformat.v4.new_markdown_cell("Markdown example:\n```python\nprint('example')\n```"),
        nbformat.v4.new_code_cell("print('real code')"),
    ]
    notebook_path = tmp_path / "lesson.ipynb"
    with notebook_path.open("w", encoding="utf-8") as handle:
        nbformat.write(notebook, handle)

    result = convert_notebook_paths_to_markdown(inputs=[str(notebook_path)])

    exported_markdown = result.output_paths[0].read_text(encoding="utf-8")
    assert "Markdown example:\n```\nprint('example')\n```" in exported_markdown
    assert "```python\nprint('real code')\n```" in exported_markdown
    assert len(result.warnings) == 1


def test_plain_fences_remain_markdown_when_creating_notebook() -> None:
    notebook = parse_markdown_to_notebook(
        "# Lesson\n\nExample block:\n```\nprint('example')\n```\n\n```python\nprint('code')\n```\n"
    )

    assert notebook.cells[0].cell_type == "markdown"
    assert "```\nprint('example')\n```" in notebook.cells[0].source
    assert notebook.cells[1].cell_type == "code"
    assert notebook.cells[1].source == "print('code')"


def test_markdown_directory_can_be_combined_to_notebook_and_index(tmp_path: Path) -> None:
    markdown_dir = tmp_path / "markdown"
    markdown_dir.mkdir()
    (markdown_dir / "one.md").write_text("# One\n\n```python\nprint(1)\n```\n", encoding="utf-8")
    (markdown_dir / "two.md").write_text("# Two\n\nText\n", encoding="utf-8")

    output_path = tmp_path / "combined.ipynb"
    index_path = tmp_path / "index.md"
    result = convert_markdown_paths_to_notebooks(
        inputs=[str(markdown_dir)],
        output=str(output_path),
        separate=False,
        index=str(index_path),
    )

    assert result.output_paths == [output_path]
    assert result.index_path == index_path
    assert index_path.read_text(encoding="utf-8").startswith("# Index")

    notebook = nbformat.read(output_path, as_version=4)
    assert len(notebook.cells) >= 2


def test_notebook_conversion_defaults_to_separate_output(tmp_path: Path) -> None:
    notebook = nbformat.v4.new_notebook()
    notebook.cells = [nbformat.v4.new_markdown_cell("# Lesson")]
    notebook_path = tmp_path / "lesson.ipynb"
    with notebook_path.open("w", encoding="utf-8") as handle:
        nbformat.write(notebook, handle)

    result = convert_notebook_paths_to_markdown(inputs=[str(notebook_path)])

    assert result.output_paths == [tmp_path / "lesson.md"]


def test_cli_join_flag_switches_output_mode() -> None:
    parser = build_parser()

    default_args = parser.parse_args(["ipynb2md", "example.ipynb"])
    join_args = parser.parse_args(["ipynb2md", "example.ipynb", "--join"])

    assert default_args.join is False
    assert join_args.join is True

