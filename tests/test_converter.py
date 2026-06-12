from __future__ import annotations

import json
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


def test_annotated_python_fence_remains_markdown() -> None:
    notebook = parse_markdown_to_notebook(
        "# Session handout\n\nOverview text.\n\n<!-- md2ipynb: keep-markdown -->\n```python\nprint('example')\n```\n"
    )

    assert len(notebook.cells) == 1
    assert notebook.cells[0].cell_type == "markdown"
    assert notebook.cells[0].metadata["language"] == "markdown"
    assert "```python\nprint('example')\n```" in notebook.cells[0].source
    assert "md2ipynb: keep-markdown" not in notebook.cells[0].source


def test_generated_notebook_includes_python_metadata() -> None:
    notebook = parse_markdown_to_notebook("# Lesson\n\n```python\nprint('code')\n```\n")

    assert notebook.metadata["kernelspec"]["name"] == "python3"
    assert notebook.metadata["language_info"]["name"] == "python"
    assert notebook.cells[0].metadata["language"] == "markdown"
    assert notebook.cells[1].metadata["language"] == "python"


def test_heading_boundaries_split_markdown_cells() -> None:
    notebook = parse_markdown_to_notebook("# Title\n\nIntro\n\n## Part one\n\nBody\n\n## Part two\n\nMore\n")

    assert [cell.cell_type for cell in notebook.cells] == ["markdown", "markdown", "markdown"]
    assert notebook.cells[0].source.startswith("# Title")
    assert notebook.cells[1].source.startswith("## Part one")
    assert notebook.cells[2].source.startswith("## Part two")


def test_custom_markdown_file_converts_to_non_empty_multicell_notebook(tmp_path: Path) -> None:
    markdown_path = tmp_path / "session_guide.md"
    markdown_path.write_text(
        "# Session guide\n\n"
        "Intro text.\n\n"
        "## Environment setup\n\n"
        "Use this command:\n\n"
        "```bash\npython -m venv .venv\n```\n\n"
        "<!-- md2ipynb: keep-markdown -->\n"
        "```python\nprint('example snippet')\n```\n\n"
        "## Actual code\n\n"
        "```python\nprint('real code cell')\n```\n",
        encoding="utf-8",
    )

    output_path = tmp_path / "session_guide.ipynb"
    result = convert_markdown_paths_to_notebooks(
        inputs=[str(markdown_path)],
        output=str(output_path),
        separate=False,
        force=True,
    )

    assert result.output_paths == [output_path]

    notebook_json = json.loads(output_path.read_text(encoding="utf-8"))

    assert notebook_json["metadata"]["kernelspec"]["name"] == "python3"
    assert len(notebook_json["cells"]) == 4
    assert [cell["cell_type"] for cell in notebook_json["cells"]] == [
        "markdown",
        "markdown",
        "markdown",
        "code",
    ]
    assert notebook_json["cells"][0]["source"][0] == "# Session guide\n"
    assert notebook_json["cells"][1]["source"][0] == "## Environment setup\n"
    assert "```python\n" in "".join(notebook_json["cells"][1]["source"])
    assert "md2ipynb: keep-markdown" not in "".join(notebook_json["cells"][1]["source"])
    assert notebook_json["cells"][2]["source"][0] == "## Actual code"
    assert notebook_json["cells"][3]["source"] == ["print('real code cell')"]


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

