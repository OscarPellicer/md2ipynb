from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import nbformat

from md2ipynb.converter import convert_markdown_paths_to_notebooks, convert_notebook_paths_to_markdown


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPT = REPO_ROOT / "skills" / "md2ipynb" / "scripts" / "md2ipynb.py"


def run_skill_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SKILL_SCRIPT), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def test_skill_script_round_trips_notebook_through_markdown(tmp_path: Path) -> None:
    notebook = nbformat.v4.new_notebook()
    notebook.cells = [
        nbformat.v4.new_markdown_cell("# Text processing basics\n\nExample:\n```python\nprint('example')\n```"),
        nbformat.v4.new_code_cell("print('real code')"),
    ]
    notebook_path = tmp_path / "lesson.ipynb"
    with notebook_path.open("w", encoding="utf-8") as handle:
        nbformat.write(notebook, handle)

    scratch_dir = tmp_path / "scratch"
    export_result = run_skill_script("ipynb2md", str(notebook_path), "--output", str(scratch_dir), "--force")
    markdown_path = scratch_dir / "lesson.md"

    assert str(markdown_path) in export_result.stdout
    assert "WARNING:" in export_result.stderr
    assert "```\nprint('example')\n```" in markdown_path.read_text(encoding="utf-8")

    output_path = tmp_path / "rewritten.ipynb"
    run_skill_script("md2ipynb", str(markdown_path), "--output", str(output_path), "--join", "--force")

    round_tripped = nbformat.read(output_path, as_version=4)
    assert [cell.cell_type for cell in round_tripped.cells] == ["markdown", "markdown", "code"]
    assert round_tripped.cells[-1].source == "print('real code')"


def test_skill_script_creates_notebook_from_markdown_with_keep_markdown(tmp_path: Path) -> None:
    markdown_path = tmp_path / "new_lesson.md"
    markdown_path.write_text(
        "# Text processing basics\n\n"
        "A displayed Python example:\n\n"
        "<!-- md2ipynb: keep-markdown -->\n"
        "```python\nprint('example only')\n```\n\n"
        "## Real code\n\n"
        "```python\nprint('code cell')\n```\n",
        encoding="utf-8",
    )

    output_path = tmp_path / "new_lesson.ipynb"
    run_skill_script("md2ipynb", str(markdown_path), "--output", str(output_path), "--join", "--force")

    notebook_json = json.loads(output_path.read_text(encoding="utf-8"))
    assert [cell["cell_type"] for cell in notebook_json["cells"]] == ["markdown", "markdown", "code"]
    assert "```python\n" in "".join(notebook_json["cells"][0]["source"])
    assert "md2ipynb: keep-markdown" not in "".join(notebook_json["cells"][0]["source"])
    assert notebook_json["cells"][2]["source"] == ["print('code cell')"]


def test_skill_script_matches_package_for_markdown_to_notebook(tmp_path: Path) -> None:
    markdown_path = tmp_path / "lesson.md"
    markdown_path.write_text(
        "# Text processing basics\n\n"
        "Example block:\n\n"
        "```\nprint('markdown example')\n```\n\n"
        "<!-- md2ipynb: keep-markdown -->\n"
        "```python\nprint('highlighted example')\n```\n\n"
        "## Real code\n\n"
        "```python\nprint('code cell')\n```\n",
        encoding="utf-8",
    )
    package_output = tmp_path / "package.ipynb"
    skill_output = tmp_path / "skill.ipynb"

    convert_markdown_paths_to_notebooks(
        inputs=[str(markdown_path)],
        output=str(package_output),
        separate=False,
        force=True,
    )
    run_skill_script("md2ipynb", str(markdown_path), "--output", str(skill_output), "--join", "--force")

    package_notebook = nbformat.read(package_output, as_version=4)
    skill_notebook = nbformat.read(skill_output, as_version=4)

    assert [cell.cell_type for cell in skill_notebook.cells] == [cell.cell_type for cell in package_notebook.cells]
    assert [cell.source for cell in skill_notebook.cells] == [cell.source for cell in package_notebook.cells]
    assert skill_notebook.metadata == package_notebook.metadata


def test_skill_script_matches_package_for_notebook_to_markdown(tmp_path: Path) -> None:
    notebook = nbformat.v4.new_notebook()
    notebook.cells = [
        nbformat.v4.new_markdown_cell("# Text processing basics\n\n```python\nprint('example')\n```"),
        nbformat.v4.new_code_cell("print('code cell')"),
    ]
    notebook_path = tmp_path / "lesson.ipynb"
    with notebook_path.open("w", encoding="utf-8") as handle:
        nbformat.write(notebook, handle)

    package_dir = tmp_path / "package"
    skill_dir = tmp_path / "skill"
    package_result = convert_notebook_paths_to_markdown(
        inputs=[str(notebook_path)],
        output=str(package_dir),
        force=True,
    )
    skill_result = run_skill_script("ipynb2md", str(notebook_path), "--output", str(skill_dir), "--force")

    package_markdown = package_result.output_paths[0].read_text(encoding="utf-8")
    skill_markdown = (skill_dir / "lesson.md").read_text(encoding="utf-8")

    assert skill_markdown == package_markdown
    assert len(package_result.warnings) == 1
    assert "WARNING:" in skill_result.stderr
