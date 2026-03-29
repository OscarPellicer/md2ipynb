from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from .config import load_config
from .converter import convert_markdown_paths_to_notebooks, convert_notebook_paths_to_markdown


CONFIG = load_config()
CUSTOM_INSTRUCTIONS = CONFIG.effective_instructions() or "No custom notebook-authoring instructions are configured."
SERVER_INSTRUCTIONS = "\n".join(
    [
        "Use this server whenever notebook work would be easier in markdown than direct .ipynb editing.",
        "",
        "Default workflow:",
        "1. For new notebooks, author markdown first and convert with md2ipynb.",
        f"2. For notebook edits touching more than {CONFIG.markdown_edit_cell_threshold} cells, convert to markdown with ipynb2md, edit the markdown, then convert back with md2ipynb.",
        f"3. Direct cell editing is only preferred for changes touching {CONFIG.markdown_edit_cell_threshold} or fewer cells.",
        "4. Markdown examples inside markdown cells must use plain ``` fences, while real code cells must use ```python fences.",
        "",
        "Configured notebook instructions:",
        CUSTOM_INSTRUCTIONS,
    ]
)


mcp = FastMCP("md2ipynb", instructions=SERVER_INSTRUCTIONS, json_response=True)


def _result_payload(result) -> dict[str, Any]:
    return {
        "processed_inputs": [str(path) for path in result.processed_inputs],
        "output_paths": [str(path) for path in result.output_paths],
        "index_path": str(result.index_path) if result.index_path else None,
        "warnings": result.warnings,
    }


@mcp.tool()
def ipynb2md(
    inputs: list[str] | None = None,
    output: str | None = None,
    join: bool = False,
    index: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Convert notebook files or directories to markdown files. Separate output is the default; set join=true to combine inputs."""
    return _result_payload(
        convert_notebook_paths_to_markdown(
            inputs=inputs,
            output=output,
            separate=not join,
            index=index,
            force=force,
        )
    )


@mcp.tool()
def md2ipynb(
    inputs: list[str] | None = None,
    output: str | None = None,
    join: bool = False,
    index: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Convert markdown files or directories to notebook files. Separate output is the default; set join=true to combine inputs."""
    return _result_payload(
        convert_markdown_paths_to_notebooks(
            inputs=inputs,
            output=output,
            separate=not join,
            index=index,
            force=force,
        )
    )


@mcp.resource("md2ipynb://instructions")
def instructions_resource() -> str:
    """Return the effective notebook workflow instructions exposed by this server."""
    return SERVER_INSTRUCTIONS


@mcp.resource("md2ipynb://config")
def config_resource() -> str:
    """Return the effective runtime configuration as JSON."""
    return json.dumps(CONFIG.to_dict(), indent=2)


@mcp.prompt(title="Notebook markdown workflow")
def notebook_markdown_workflow(task: str = "Edit a notebook") -> str:
    """Prompt that reminds models to prefer markdown round-trips for notebook-heavy work."""
    return f"{SERVER_INSTRUCTIONS}\n\nCurrent task: {task}"


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
