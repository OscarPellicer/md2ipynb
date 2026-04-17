# md2ipynb / ipynb2md quickstart

## Description

`md2ipynb` converts Jupyter notebooks to Markdown and back again, with the Markdown format designed to be easier for coding agents to edit safely. In particular:
- Only ` ```python ... ``` ` blocks in the Markdown will become notebook code cells.
- Plain / other fenced blocks ` ``` ... ``` ` remain Markdown content.
- When exporting notebooks from Markdown, any Markdown cell that already contains ` ```python ` fences is rewritten to plain fences and a warning is emitted. This avoids accidental conversion of Markdown examples into real code cells on the way back.

## Usage examples

 - Convert a notebook to Markdown: `ipynb2md lesson.ipynb`
 - Convert Markdown to a notebook: `md2ipynb lesson.md`
 - Convert a directory of notebooks to Markdown and create an index: `ipynb2md notebooks_dir --output exported_dir_md --index notebook_index.md`
 - Convert a directory of Markdown files to notebooks and create an index: `md2ipynb markdown_dir --output generated_notebooks --index markdown_index.md`