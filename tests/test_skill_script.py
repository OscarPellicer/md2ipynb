from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import nbformat


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
