---
name: md2ipynb
description: Convert Jupyter notebooks to Markdown and back for agent-friendly notebook authoring. Use when creating a notebook from scratch or making substantial edits across multiple notebook cells, sections, explanations, or examples. Prefer notebook editing or execution tools instead for tiny cell edits, running cells, inspecting outputs, kernel work, or other notebook-native tasks.
---

# md2ipynb

## Overview

Use this skill to author or substantially rewrite Jupyter notebooks through Markdown. Markdown is easier for agents to edit coherently than raw `.ipynb` JSON, and the bundled script converts between Markdown and notebooks.

For small edits, cell execution, output inspection, kernel state, or notebook UI operations, use notebook-native tools instead of this workflow.

## Workflow

1. Check dependencies:
   - If `python -c "import nbformat"` succeeds, use the active Python environment.
   - If `nbformat` is missing and the active environment is a normal project or virtual environment, install the small dependency with `python -m pip install -r <skill>/scripts/requirements.txt`.
   - If the environment looks global, managed, or sensitive, create a local virtual environment and install the requirements there.
2. For an existing notebook, convert it to a temporary Markdown file:

```bash
python <skill>/scripts/md2ipynb.py ipynb2md path/to/notebook.ipynb --output path/to/scratch --force
```

3. Edit the Markdown file, not the notebook JSON.
4. Convert the Markdown back to a notebook:

```bash
python <skill>/scripts/md2ipynb.py md2ipynb path/to/scratch/notebook.md --output path/to/notebook.ipynb --force
```

5. Delete intermediate Markdown files by default unless the user explicitly asks to keep them.

For a new notebook, write the notebook content as temporary Markdown first, convert it to `.ipynb`, then delete the Markdown source unless the user wants a paired source file.

## Markdown format

- Use ` ```python ` fenced blocks only for real notebook code cells.
- Use plain fenced blocks for code examples that should remain inside Markdown cells.
- To keep a Python-highlighted example inside Markdown, put `<!-- md2ipynb: keep-markdown -->` immediately above that ` ```python ` block.
- When exporting notebooks, the script rewrites ` ```python ` fences inside existing Markdown cells to plain fences and emits a warning, preventing accidental code-cell creation on round trip.

## Authoring rules

Read `references/notebook-authoring.md` before creating or substantially rewriting instructional notebooks.

Core defaults: use sentence case for headers, and do not add student-facing error handling such as `try`/`except` or `if`/`else` in code cells unless the user explicitly asks for it.
