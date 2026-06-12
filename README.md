# md2ipynb

`md2ipynb` is a skill-first workflow for creating and substantially editing Jupyter notebooks through Markdown.

The repo provides:

- An installable Codex skill at `skills/md2ipynb`
- CLI commands: `ipynb2md`, `md2ipynb`, and `notebook-converter`
- A small Python conversion library backed by `nbformat`
- Pytest coverage for the conversion behavior

## Source layout

The conversion logic exists in two places by design:

- `src/md2ipynb/converter.py` powers the Python package and CLI.
- `skills/md2ipynb/scripts/md2ipynb.py` is a self-contained copy bundled with the skill.

The skill script is duplicated so the skill can be installed from the public GitHub repo and run immediately without requiring `pip install` of this package. Keep both implementations in sync; the test suite includes parity coverage for the package and skill script.

## When to use it

Use the skill when an agent needs to create a notebook from scratch or make large edits across multiple cells, sections, explanations, or examples. The workflow is:

1. Convert a notebook to Markdown, or author a new notebook as Markdown.
2. Edit the Markdown.
3. Convert the Markdown back to `.ipynb`.
4. Delete the intermediate Markdown unless the user asked to keep it.

For tiny cell edits, running cells, inspecting outputs, kernel work, or notebook UI tasks, use notebook-native tools instead.

## Install the skill

Install from this local checkout by copying `skills/md2ipynb` into your Codex skills directory:

```powershell
$dest = "$env:USERPROFILE\.codex\skills\md2ipynb"
New-Item -ItemType Directory -Force (Split-Path $dest)
Copy-Item -Recurse -Force .\skills\md2ipynb $dest
```

Install from the public GitHub repo with the Codex skill installer:

```bash
python ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo OscarPellicer/md2ipynb \
  --path skills/md2ipynb
```

Restart Codex after installing so it discovers the skill.

## Skill dependencies

The skill script requires `nbformat>=5.10`. Agents should first check whether the active Python environment already has it:

```bash
python -c "import nbformat"
```

If it is missing and the active environment is a normal project or virtual environment, install the small dependency there:

```bash
python -m pip install -r skills/md2ipynb/scripts/requirements.txt
```

If the active environment is global, managed, or sensitive, create an isolated virtual environment and install the same requirements file there.

## CLI installation

Install from a checkout:

```bash
pip install .
```

Install with development dependencies:

```bash
pip install -e .[dev]
```

This exposes:

- `ipynb2md`
- `md2ipynb`
- `notebook-converter`

The legacy repo-root entrypoint still works:

```bash
python notebook_converter.py ipynb2md
```

## CLI usage

Convert notebooks to Markdown:

```bash
ipynb2md lesson.ipynb
ipynb2md notebooks --output scratch_md --index notebook_index.md
ipynb2md notebooks lecture.ipynb --join --output combined_notebooks.md
```

Convert Markdown to notebooks:

```bash
md2ipynb lesson.md
md2ipynb markdown_sources --output generated_notebooks --index markdown_index.md
md2ipynb markdown_sources appendix.md --join --output combined_notebook.ipynb
```

Print the packaged agent quickstart:

```bash
md2ipynb --agents
```

## Markdown format

- ` ```python ... ``` ` blocks become notebook code cells.
- Plain fenced blocks remain Markdown content.
- Add `<!-- md2ipynb: keep-markdown -->` immediately above a ` ```python ` block when a Python-highlighted example should stay inside a Markdown cell.
- When exporting notebooks, Python fences inside Markdown cells are rewritten to plain fences and a warning is emitted. This prevents accidental conversion of examples into real code cells on round trip.

## Authoring rules

The default authoring rules live in `instructions.md` and are also included in the skill reference:

- Use sentence case for headers, for example `# Text processing basics`.
- Do not use student-facing error handling such as `try`/`except` or `if`/`else` in code cells unless explicitly requested.

## Development

Run tests:

```bash
pytest
```

The tests exercise both the package implementation and the duplicated skill script. When changing conversion behavior, update both copies in the same commit.

Validate the skill:

```bash
python ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/md2ipynb
```
