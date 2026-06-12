from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

try:
    import nbformat
except ImportError as error:
    raise SystemExit(
        "Missing dependency: nbformat. Install it with "
        "`python -m pip install -r scripts/requirements.txt` from this skill directory."
    ) from error


HEADER_PATTERN = re.compile(r"^(#{1,4})\s+(.+?)\s*$")
PYTHON_FENCE_PATTERN = re.compile(r"^(\s*)```python\s*$", re.IGNORECASE)
FENCE_PATTERN = re.compile(r"^```\s*$")
KEEP_MARKDOWN_DIRECTIVE_PATTERN = re.compile(r"^\s*<!--\s*md2ipynb:\s*keep-markdown\s*-->\s*$", re.IGNORECASE)

DEFAULT_NOTEBOOK_METADATA = {
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    },
    "language_info": {
        "name": "python",
        "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    },
}


@dataclass(slots=True)
class MarkdownDocument:
    source_path: Path
    content: str
    headers: list[tuple[int, str]]
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class BatchConversionResult:
    processed_inputs: list[Path]
    output_paths: list[Path]
    index_path: Path | None = None
    warnings: list[str] = field(default_factory=list)


def get_unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    counter = 1
    while True:
        candidate = path.with_name(f"{path.stem}_{counter}{path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def _resolve_target_path(path: Path, force: bool) -> Path:
    return path if force else get_unique_path(path)


def extract_headers(markdown_text: str) -> list[tuple[int, str]]:
    headers: list[tuple[int, str]] = []
    for line in markdown_text.splitlines():
        match = HEADER_PATTERN.match(line.strip())
        if match:
            headers.append((len(match.group(1)), match.group(2).strip()))
    return headers


def generate_index(index_entries: Iterable[tuple[str, list[tuple[int, str]]]]) -> str:
    lines = ["# Index", ""]
    for filename, headers in index_entries:
        lines.append(f"- **{filename}**")
        for level, text in headers:
            lines.append(f"{'  ' * level}- {text}")
    lines.append("")
    return "\n".join(lines)


def _sanitize_markdown_fences(markdown_text: str, notebook_path: Path, cell_number: int) -> tuple[str, list[str]]:
    warnings: list[str] = []
    updated_lines: list[str] = []
    did_convert = False
    for line in markdown_text.splitlines():
        match = PYTHON_FENCE_PATTERN.match(line)
        if match:
            updated_lines.append(f"{match.group(1)}```")
            did_convert = True
            continue
        updated_lines.append(line)
    if did_convert:
        warnings.append(
            f"{notebook_path}: converted python fenced block markers in markdown cell {cell_number} "
            "to plain fences so they stay markdown on round-trip."
        )
    return "\n".join(updated_lines), warnings


def notebook_to_markdown_document(notebook_path: str | Path) -> MarkdownDocument:
    path = Path(notebook_path)
    notebook = nbformat.read(path, as_version=4)
    content_parts = [f"# {path.name}", ""]
    headers: list[tuple[int, str]] = []
    warnings: list[str] = []

    for cell_number, cell in enumerate(notebook.cells, start=1):
        if cell.cell_type == "markdown":
            sanitized_source, cell_warnings = _sanitize_markdown_fences(cell.source, path, cell_number)
            warnings.extend(cell_warnings)
            headers.extend(extract_headers(sanitized_source))
            content_parts.append(sanitized_source)
            content_parts.append("")
        elif cell.cell_type == "code":
            content_parts.append("```python")
            content_parts.append(cell.source)
            content_parts.append("```")
            content_parts.append("")

    return MarkdownDocument(
        source_path=path,
        content="\n".join(content_parts).strip() + "\n",
        headers=headers,
        warnings=warnings,
    )


def _new_markdown_cell(source: str):
    cell = nbformat.v4.new_markdown_cell(source)
    cell.metadata["language"] = "markdown"
    return cell


def _new_code_cell(source: str):
    cell = nbformat.v4.new_code_cell(source)
    cell.metadata["language"] = "python"
    return cell


def parse_markdown_to_notebook(markdown_text: str):
    notebook = nbformat.v4.new_notebook(metadata=DEFAULT_NOTEBOOK_METADATA.copy())
    markdown_lines: list[str] = []
    lines = markdown_text.splitlines()
    index = 0
    keep_next_python_fence_as_markdown = False

    def flush_markdown() -> None:
        source = "\n".join(markdown_lines).strip()
        if source:
            notebook.cells.append(_new_markdown_cell(source))
        markdown_lines.clear()

    while index < len(lines):
        line = lines[index]
        if KEEP_MARKDOWN_DIRECTIVE_PATTERN.match(line):
            keep_next_python_fence_as_markdown = True
        elif PYTHON_FENCE_PATTERN.match(line.strip()) and not keep_next_python_fence_as_markdown:
            flush_markdown()
            code_lines: list[str] = []
            index += 1
            while index < len(lines):
                code_line = lines[index]
                if FENCE_PATTERN.match(code_line.strip()):
                    break
                code_lines.append(code_line)
                index += 1
            notebook.cells.append(_new_code_cell("\n".join(code_lines)))
        else:
            header_match = HEADER_PATTERN.match(line.strip())
            if header_match and markdown_lines and any(existing_line.strip() for existing_line in markdown_lines):
                flush_markdown()
            if PYTHON_FENCE_PATTERN.match(line.strip()) and keep_next_python_fence_as_markdown:
                keep_next_python_fence_as_markdown = False
            markdown_lines.append(line)
        index += 1

    flush_markdown()
    return notebook


def _collect_input_paths(inputs: list[str] | None, expected_suffix: str) -> list[Path]:
    requested_inputs = inputs or ["."]
    collected: list[Path] = []
    seen: set[Path] = set()

    for raw_input in requested_inputs:
        path = Path(raw_input).expanduser()
        if path.is_dir():
            for child in sorted(path.iterdir()):
                if child.suffix.lower() == expected_suffix.lower():
                    resolved = child.resolve()
                    if resolved not in seen:
                        seen.add(resolved)
                        collected.append(child)
            continue

        if path.is_file() and path.suffix.lower() == expected_suffix.lower():
            resolved = path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                collected.append(path)
            continue

        raise FileNotFoundError(f"Input path is not a valid {expected_suffix} file or directory: {path}")

    if not collected:
        raise FileNotFoundError(f"No {expected_suffix} files found in the requested inputs.")

    return collected


def _write_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _write_notebook(path: Path, notebook) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        nbformat.write(notebook, handle)
    return path


def convert_notebook_paths_to_markdown(
    inputs: list[str] | None = None,
    output: str | None = None,
    separate: bool = True,
    index: str | None = None,
    force: bool = False,
) -> BatchConversionResult:
    notebook_paths = _collect_input_paths(inputs, ".ipynb")
    documents = [notebook_to_markdown_document(path) for path in notebook_paths]
    output_paths: list[Path] = []

    if separate:
        output_dir = Path(output).expanduser() if output else None
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
        for document in documents:
            parent = output_dir or document.source_path.parent
            target = _resolve_target_path(parent / f"{document.source_path.stem}.md", force=force)
            output_paths.append(_write_text(target, document.content))
    else:
        default_output = Path("combined_notebooks.md")
        target = _resolve_target_path(Path(output).expanduser() if output else default_output, force=force)
        combined_content = "\n\n---\n\n".join(document.content.strip() for document in documents) + "\n"
        output_paths.append(_write_text(target, combined_content))

    index_path: Path | None = None
    if index:
        index_target = _resolve_target_path(Path(index).expanduser(), force=force)
        index_path = _write_text(
            index_target,
            generate_index((document.source_path.name, document.headers) for document in documents),
        )

    return BatchConversionResult(
        processed_inputs=notebook_paths,
        output_paths=output_paths,
        index_path=index_path,
        warnings=[warning for document in documents for warning in document.warnings],
    )


def convert_markdown_paths_to_notebooks(
    inputs: list[str] | None = None,
    output: str | None = None,
    separate: bool = True,
    index: str | None = None,
    force: bool = False,
) -> BatchConversionResult:
    markdown_paths = _collect_input_paths(inputs, ".md")
    markdown_documents = [
        MarkdownDocument(
            source_path=path,
            content=path.read_text(encoding="utf-8"),
            headers=extract_headers(path.read_text(encoding="utf-8")),
        )
        for path in markdown_paths
    ]
    output_paths: list[Path] = []

    if separate:
        output_dir = Path(output).expanduser() if output else None
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
        for document in markdown_documents:
            target_parent = output_dir or document.source_path.parent
            target = _resolve_target_path(target_parent / f"{document.source_path.stem}.ipynb", force=force)
            output_paths.append(_write_notebook(target, parse_markdown_to_notebook(document.content)))
    else:
        default_output = Path("combined_notebook.ipynb")
        target = _resolve_target_path(Path(output).expanduser() if output else default_output, force=force)
        combined_content = "\n\n---\n\n".join(document.content.strip() for document in markdown_documents) + "\n"
        output_paths.append(_write_notebook(target, parse_markdown_to_notebook(combined_content)))

    index_path: Path | None = None
    if index:
        index_target = _resolve_target_path(Path(index).expanduser(), force=force)
        index_path = _write_text(
            index_target,
            generate_index((document.source_path.name, document.headers) for document in markdown_documents),
        )

    return BatchConversionResult(
        processed_inputs=markdown_paths,
        output_paths=output_paths,
        index_path=index_path,
    )


def _add_shared_conversion_arguments(parser: argparse.ArgumentParser, output_help: str) -> None:
    parser.add_argument("inputs", nargs="*", help="Input files and/or directories. Defaults to current directory.")
    parser.add_argument("-o", "--output", help=output_help)
    parser.add_argument("--join", action="store_true", help="Join all processed inputs into a single output file.")
    parser.add_argument("--index", metavar="INDEX_FILE", help="Write an index markdown file of detected headers.")
    parser.add_argument("--force", action="store_true", help="Overwrite target paths instead of creating unique names.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert Jupyter notebooks and Markdown in both directions.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_ipynb2md = subparsers.add_parser("ipynb2md", aliases=["extract", "export"])
    _add_shared_conversion_arguments(
        parser_ipynb2md,
        "Output directory by default, or a single markdown file when using --join.",
    )

    parser_md2ipynb = subparsers.add_parser("md2ipynb", aliases=["create", "import"])
    _add_shared_conversion_arguments(
        parser_md2ipynb,
        "Output directory by default, or a single notebook file when using --join.",
    )
    return parser


def _print_conversion_summary(result: BatchConversionResult) -> None:
    for output_path in result.output_paths:
        print(output_path)
    if result.index_path:
        print(result.index_path)
    for warning in result.warnings:
        print(f"WARNING: {warning}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
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


if __name__ == "__main__":
    raise SystemExit(main())
