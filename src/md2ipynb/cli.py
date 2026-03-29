from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import AppConfig, install_cursor_integration, load_config, write_config
from .converter import convert_markdown_paths_to_notebooks, convert_notebook_paths_to_markdown


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
        "Output directory by default, or a single notebook file when using --join.",
    )

    parser_config = subparsers.add_parser("config", help="Manage global md2ipynb configuration.")
    config_subparsers = parser_config.add_subparsers(dest="config_command", required=True)

    parser_config_path = config_subparsers.add_parser("path", help="Print the global config path.")
    parser_config_path.add_argument("--config", help="Custom config path to resolve.")

    parser_config_show = config_subparsers.add_parser("show", help="Print the effective config as JSON.")
    parser_config_show.add_argument("--config", help="Custom config path to load.")

    parser_config_init = config_subparsers.add_parser("init", help="Create a config file.")
    parser_config_init.add_argument("--config", help="Custom config path to write.")
    parser_config_init.add_argument("--python-executable", help="Python executable used for Cursor MCP integration.")
    parser_config_init.add_argument("--instructions-file", help="Path to a file with notebook authoring instructions.")
    parser_config_init.add_argument("--instructions-text", help="Inline notebook authoring instructions.")
    parser_config_init.add_argument(
        "--cell-threshold",
        type=int,
        default=2,
        help="Maximum number of notebook cells to edit directly before preferring markdown round-trip.",
    )
    parser_config_init.add_argument("--cursor-root", help="Override the Cursor global configuration directory.")
    parser_config_init.add_argument("--cursor-mcp-config-path", help="Override the Cursor mcp.json path.")
    parser_config_init.add_argument("--cursor-rules-dir", help="Override the Cursor rules directory.")
    parser_config_init.add_argument("--force", action="store_true", help="Overwrite an existing config file.")

    parser_config_cursor = config_subparsers.add_parser(
        "install-cursor",
        help="Install global Cursor MCP and rules files using the current md2ipynb config.",
    )
    parser_config_cursor.add_argument("--config", help="Custom config path to load.")
    parser_config_cursor.add_argument("--force", action="store_true", help="Overwrite an existing rule file.")

    return parser


def _print_conversion_summary(result) -> None:
    for output_path in result.output_paths:
        print(output_path)
    if result.index_path:
        print(result.index_path)
    for warning in result.warnings:
        print(f"WARNING: {warning}", file=sys.stderr)


def _handle_config_command(args: argparse.Namespace) -> int:
    if args.config_command == "path":
        print(load_config(args.config).config_path)
        return 0

    if args.config_command == "show":
        config = load_config(args.config)
        print(json.dumps(config.to_dict(), indent=2))
        return 0

    if args.config_command == "init":
        config = AppConfig(
            python_executable=args.python_executable,
            instructions_file=args.instructions_file,
            instructions_text=args.instructions_text,
            markdown_edit_cell_threshold=args.cell_threshold,
            cursor_root=args.cursor_root,
            cursor_mcp_config_path=args.cursor_mcp_config_path,
            cursor_rules_dir=args.cursor_rules_dir,
            config_path=Path(args.config).expanduser() if args.config else load_config().config_path,
        )
        print(write_config(config, force=args.force))
        return 0

    if args.config_command == "install-cursor":
        installed_paths = install_cursor_integration(load_config(args.config), force=args.force)
        for path in installed_paths.values():
            print(path)
        return 0

    raise ValueError(f"Unknown config command: {args.config_command}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "config":
        return _handle_config_command(args)

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

    raise ValueError(f"Unknown command: {args.command}")


def ipynb2md_entry() -> int:
    return main(["ipynb2md", *sys.argv[1:]])


def md2ipynb_entry() -> int:
    return main(["md2ipynb", *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())
