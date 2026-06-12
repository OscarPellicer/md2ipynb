# md2ipynb terminal quickstart

Print this guide with:

```bash
md2ipynb --agents
```

`md2ipynb` converts Jupyter notebooks to Markdown and back again. Use this for creating notebooks from scratch or making substantial notebook edits through Markdown. For tiny edits, running cells, inspecting outputs, or kernel work, use notebook-native tools.

## Format

- Only ` ```python ... ``` ` blocks in the Markdown will become notebook code cells.
- If you want a Python-highlighted example to stay markdown, add `<!-- md2ipynb: keep-markdown -->` immediately above that ` ```python ` block.
- Plain / other fenced blocks ` ``` ... ``` ` remain Markdown content.
- When exporting notebooks from Markdown, any Markdown cell that already contains ` ```python ` fences is rewritten to plain fences and a warning is emitted. This avoids accidental conversion of Markdown examples into real code cells on the way back.

## Usage

- Convert a notebook to Markdown: `ipynb2md lesson.ipynb`
- Convert Markdown to a notebook: `md2ipynb lesson.md`
- Convert Markdown to an exact notebook path: `md2ipynb lesson.md --output lesson.ipynb --force`
- Convert a directory of notebooks to Markdown and create an index: `ipynb2md notebooks_dir --output exported_dir_md --index notebook_index.md`
- Convert a directory of Markdown files to notebooks and create an index: `md2ipynb markdown_dir --output generated_notebooks --index markdown_index.md`

By default, use same-directory Markdown intermediates for notebook rewrites, then delete the `.md` file unless the user asks to keep it. A `.ipynb` output path is allowed only for one Markdown input; use an output directory for multiple separate notebooks or `--join` for one combined notebook.
