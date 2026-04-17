# md2ipynb

`md2ipynb` converts Jupyter notebooks to Markdown and back again, with the Markdown format designed to be easier for coding agents to edit safely.

The project provides:

- Installable CLI commands: `ipynb2md` and `md2ipynb`
- A shared config file for global instructions and Python path management
- An MCP server that teaches models to prefer Markdown round-trips for notebook-heavy work
- A Cursor global install path so the workflow is available across repositories
- Pytest coverage for the core conversion and configuration behavior

## Why this exists

Many agents are much better at editing Markdown than raw `.ipynb` JSON. This tool supports a workflow where agents:

1. Convert a notebook to Markdown with `ipynb2md`
2. Edit the Markdown file
3. Convert it back with `md2ipynb`

That workflow is especially useful for new notebooks and for edits touching more than a couple of cells.

## Installation

Install from a checkout:

```bash
pip install .
```

Install with development dependencies:

```bash
pip install -e .[dev]
```

This exposes these commands in the environment:

- `ipynb2md`
- `md2ipynb`
- `notebook-converter`
- `md2ipynb-mcp`

Print the packaged terminal quickstart for agents:

```bash
md2ipynb --agents
```

The legacy entrypoint still works from the repo root:

```bash
python notebook_converter.py ipynb2md
```

## CLI usage

### Convert notebooks to Markdown

Convert every notebook in the current directory into separate Markdown files:

```bash
ipynb2md
```

Convert a specific notebook:

```bash
ipynb2md lesson.ipynb
```

Convert multiple files and directories to separate Markdown files and create an index:

```bash
ipynb2md notebooks lecture.ipynb --output exported_md --index notebook_index.md
```

Join multiple inputs into one Markdown file:

```bash
ipynb2md notebooks lecture.ipynb --join --output combined_notebooks.md
```

### Convert Markdown to notebooks

Convert every Markdown file in the current directory into separate notebooks:

```bash
md2ipynb
```

Convert specific Markdown files:

```bash
md2ipynb lesson.md appendix.md
```

Convert a directory to separate notebooks and write an index:

```bash
md2ipynb markdown_sources --output generated_notebooks --index markdown_index.md
```

Join multiple Markdown sources into one notebook:

```bash
md2ipynb markdown_sources appendix.md --join --output combined_notebook.ipynb
```

### Aliases

The subcommands also support these aliases:

- `extract` and `export` for `ipynb2md`
- `create` and `import` for `md2ipynb`

The CLI also supports a top-level flag for terminal-only guidance:

- `--agents` prints the packaged `agents_quickstart.md` guide and exits

## Markdown format expectations

The current repo-specific authoring rules live in `instructions.md`.

Important behavior:

- Only ` ```python ... ``` ` blocks become notebook code cells.
- Plain fenced blocks ` ``` ... ``` ` remain Markdown content.
- When exporting notebooks, any Markdown cell that already contains ` ```python ` fences is rewritten to plain fences and a warning is emitted. This avoids accidental conversion of Markdown examples into real code cells on the way back.

## Global configuration

The tool reads global config from:

- Windows: `%APPDATA%\md2ipynb\config.toml`
- Other platforms: `~/.config/md2ipynb/config.toml`

Print the resolved config path:

```bash
md2ipynb config path
```

Create a config file:

```bash
md2ipynb config init \
  --python-executable "c:\Users\Oscar\miniconda3\envs\nlp3\python.exe" \
  --instructions-file "c:\Users\Oscar\md2ipynb\instructions.md"
```

Show the effective config:

```bash
md2ipynb config show
```

Supported config fields:

- `python_executable`: Python used for Cursor MCP registration
- `instructions_file`: External file containing notebook-authoring instructions
- `instructions_text`: Inline instructions instead of a separate file
- `markdown_edit_cell_threshold`: Maximum number of cells to edit directly before preferring Markdown round-trip
- `[cursor].root`: Override the Cursor global directory
- `[cursor].mcp_config_path`: Override the Cursor `mcp.json` path
- `[cursor].rules_dir`: Override the Cursor global rules directory

## MCP server

Start the MCP server with stdio transport:

```bash
md2ipynb-mcp
```

Or:

```bash
python -m md2ipynb.mcp_server
```

The server exposes:

- `ipynb2md`
- `md2ipynb`
- `md2ipynb://instructions`
- `md2ipynb://config`
- A prompt reminding models to prefer the Markdown workflow for notebook-heavy tasks

The MCP server instructions explicitly tell models to:

1. Create new notebooks through Markdown first
2. Convert existing notebooks to Markdown for edits touching more than the configured threshold
3. Reserve direct cell editing for tiny changes only

## Cursor global integration

Install the global Cursor MCP entry and a global Cursor rule:

```bash
md2ipynb config install-cursor
```

This writes:

- A global Cursor MCP entry pointing to `python -m md2ipynb.mcp_server`
- A global Cursor rule that tells Cursor agents to prefer the Markdown round-trip workflow for notebooks

By default, the install targets:

- `~/.cursor/mcp.json`
- `~/.cursor/rules/md2ipynb-workflow.mdc`

If you configured `python_executable`, that interpreter is used in the generated Cursor MCP entry. That makes the tool available regardless of which repository Cursor currently has open.

After installing, restart Cursor so it reloads the MCP server and rules.

## Example workflow

The `example/` directory contains a sample notebook and its Markdown source:

- `example/text_processing_basics.ipynb`
- `example/text_processing_basics.md`

Use this when you want to test the workflow for a notebook that needs a substantial rewrite instead of a tiny cell edit.

### Manual workflow

Convert the notebook to Markdown:

```bash
ipynb2md example/text_processing_basics.ipynb --output example/workdir --force
```

This creates:

- `example/workdir/text_processing_basics.md`

After the Markdown is edited, convert it back into a notebook:

```bash
md2ipynb example/workdir/text_processing_basics.md --output example/text_processing_basics_reworked.ipynb --force
```

### Instructions to give Cursor agent

Use a prompt like this when the notebook needs a heavy edit:

```text
I want you to heavily rewrite example/text_processing_basics.ipynb using the md2ipynb workflow instead of editing notebook cells directly.

Requirements:
- First convert the notebook to Markdown.
- Edit the Markdown file, not the .ipynb JSON.
- Treat this as a substantial rewrite: reorganize sections, improve explanations, add more examples, and update the code cells accordingly.
- Follow the notebook authoring instructions from instructions.md or the configured md2ipynb global instructions.
- Keep illustrative code examples inside markdown cells as plain fenced blocks ``` ... ```, not ```python ... ```.
- Use ```python ... ``` only for content that should become actual notebook code cells.
- When finished, convert the Markdown back to a notebook.
- Summarize what changed and mention any warnings emitted during conversion.
```

Then you could append a notebook to the agent and ask something like:

```text
Edit the given notebook to add few further examples
```

If the agent has access to the MCP server, it should prefer the `ipynb2md` and `md2ipynb` MCP tools. Otherwise it can run the CLI commands directly.

### What this example is for

The sample notebook is intentionally simple. It is a good target for asking an agent to:

- turn a short lesson into a more complete tutorial
- add more narrative between code cells
- split large cells into smaller teaching steps
- expand the examples and outputs students should inspect

## Development

Run tests:

```bash
pytest
```

## Notes for new users

- The tool is intentionally conservative about overwriting files. Without `--force`, it creates unique output names when a target path already exists.
- Separate output is the default mode, so `--output` is treated as an output directory unless you pass `--join`.
- In `--join` mode, `--output` is treated as a single file path.
