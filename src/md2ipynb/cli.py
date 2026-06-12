from __future__ import annotations

import argparse
from importlib import resources
import sys
from pathlib import Path

from .converter import convert_markdown_paths_to_notebooks, convert_notebook_paths_to_markdown


def get_agents_quickstart_text() -> str:
    return resources.files("md2ipynb").joinpath("agents_quickstart.md").read_text(encoding="utf-8")


def get_dynamic_instructions_text() -> str | None:
    local_instructions = Path.cwd() / "instructions.md"
    if local_instructions.is_file():
        return local_instructions.read_text(encoding="utf-8").strip()

    return None


def render_agents_output() -> str:
    quickstart = get_agents_quickstart_text().strip()
    instructions_text = get_dynamic_instructions_text()
    if not instructions_text:
        return f"{quickstart}\n"
    return f"{quickstart}\n\n## Instructions\n\n{instructions_text}\n"


def _add_shared_conversion_arguments(parser: argparse.ArgumentParser, output_help: str) -> None:
    parser.add_argument(
        "inputs",
        nargs="*",
        help="Input files and/or directories. Defaults to the current directory when omitted.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help=output_help,
    )
    parser.add_argument(
        "--join",
        action="store_true",
        help="Join all processed inputs into a single output file.",
    )
    parser.add_argument(
        "--index",
        metavar="INDEX_FILE",
        help="Write an index markdown file listing the detected headers from the processed inputs.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow overwriting target paths instead of creating unique filenames.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert Jupyter notebooks and Markdown in both directions.")
    parser.add_argument(
        "--agents",
        action="store_true",
        help="Print the packaged terminal quickstart for coding agents and exit.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Command to run")

    parser_ipynb2md = subparsers.add_parser(
        "ipynb2md",
        aliases=["extract", "export"],
        help="Convert notebooks to markdown.",
    )
    _add_shared_conversion_arguments(
        parser_ipynb2md,
        "Output directory by default, or a single markdown file when using --join.",
    )

    parser_md2ipynb = subparsers.add_parser(
        "md2ipynb",
        aliases=["create", "import"],
        help="Convert markdown files to notebooks.",
    )
    _add_shared_conversion_arguments(
        parser_md2ipynb,
        "Output directory by default, or an exact .ipynb path for one input. With --join, output is a single notebook file.",
    )

    return parser


def _print_conversion_summary(result) -> None:
    for output_path in result.output_paths:
        print(output_path)
    if result.index_path:
        print(result.index_path)
    for warning in result.warnings:
        print(f"WARNING: {warning}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--agents" in argv:
        print(render_agents_output(), end="")
        return 0

    args = build_parser().parse_args(argv)

    try:
        if args.command in {"ipynb2md", "extract", "export"}:
            result = convert_notebook_paths_to_markdown(
                inputs=args.inputs,
                output=args.output,
                separate=not args.join,
                index=args.index,
                force=args.force,
            )
            _print_conversion_summary(result)
            return 0

        if args.command in {"md2ipynb", "create", "import"}:
            result = convert_markdown_paths_to_notebooks(
                inputs=args.inputs,
                output=args.output,
                separate=not args.join,
                index=args.index,
                force=args.force,
            )
            _print_conversion_summary(result)
            return 0
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    raise ValueError(f"Unknown command: {args.command}")


def ipynb2md_entry() -> int:
    return main(["ipynb2md", *sys.argv[1:]])


def md2ipynb_entry() -> int:
    return main(["md2ipynb", *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())
