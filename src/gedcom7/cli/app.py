"""The ``gedcom7`` command-line entry point (argparse, stdlib only).

Subcommands ``build``, ``validate``, and ``init`` are thin shells over the
reader, loader, and writer. Exit codes: ``0`` success, ``1`` validation
failure, ``2`` usage or input error.
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path
from typing import IO

from .. import __version__
from ..validation import ValidationError, validate
from ..writer import dump, dumps
from .errors import LoadError
from .loader import build_document
from .reader import read_document
from .scaffold import scaffold

_EXIT_OK = 0
_EXIT_VALIDATION = 1
_EXIT_INPUT = 2


def main(argv: list[str] | None = None) -> int:
    """Parse ``argv`` and dispatch to a subcommand; return the exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        result: int = args.handler(args)
        return result
    except LoadError as error:
        print(f"error: {error}", file=sys.stderr)
        return _EXIT_INPUT
    except ValidationError as error:
        print(f"invalid document: {error}", file=sys.stderr)
        return _EXIT_VALIDATION


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gedcom7",
        description="Build GEDCOM 7 files from a YAML/JSON/TOML authoring document.",
    )
    parser.add_argument("--version", action="version", version=f"gedcom7 {__version__}")
    sub = parser.add_subparsers(dest="command", required=True, metavar="command")

    build = sub.add_parser("build", help="build a .ged or .gdz from an authoring document")
    build.add_argument("input", help="authoring document (.yaml/.yml/.json/.toml)")
    build.add_argument(
        "-o",
        "--output",
        help="output path (.ged or .gdz); omit or '-' to write GEDCOM text to stdout",
    )
    build.add_argument(
        "--lenient",
        action="store_true",
        help="warn on document-level issues instead of failing, and emit anyway",
    )
    build.set_defaults(handler=_cmd_build)

    validate = sub.add_parser("validate", help="check an authoring document without writing output")
    validate.add_argument("input", help="authoring document (.yaml/.yml/.json/.toml)")
    validate.set_defaults(handler=_cmd_validate)

    init = sub.add_parser("init", help="print a starter authoring document")
    init.add_argument(
        "-f",
        "--format",
        choices=("yaml", "toml", "json"),
        default="yaml",
        help="template format (default: yaml)",
    )
    init.add_argument("-o", "--output", help="write the template to a file instead of stdout")
    init.set_defaults(handler=_cmd_init)

    return parser


def _cmd_build(args: argparse.Namespace) -> int:
    document = build_document(read_document(args.input))
    strict = not args.lenient
    destination = args.output
    if destination in (None, "-"):
        with warnings.catch_warnings():
            warnings.simplefilter("always")
            warnings.showwarning = _show_warning
            sys.stdout.write(dumps(document, strict=strict))
        return _EXIT_OK
    suffix = Path(destination).suffix.lower()
    with warnings.catch_warnings():
        warnings.simplefilter("always")
        warnings.showwarning = _show_warning
        if suffix == ".gdz":
            from ..gedzip import dump_gedzip

            dump_gedzip(document, destination, strict=strict)
        elif suffix == ".ged":
            dump(document, destination, strict=strict)
        else:
            raise LoadError(f"unknown output extension {suffix or '(none)'!r}; use .ged or .gdz")
    print(f"wrote {destination}", file=sys.stderr)
    return _EXIT_OK


def _cmd_validate(args: argparse.Namespace) -> int:
    document = build_document(read_document(args.input))
    issues = validate(document, strict=False)
    if issues:
        for message in issues:
            print(message, file=sys.stderr)
        print(f"{len(issues)} issue(s) found", file=sys.stderr)
        return _EXIT_VALIDATION
    print("OK: document is valid")
    return _EXIT_OK


def _cmd_init(args: argparse.Namespace) -> int:
    text = scaffold(args.format)
    if args.output and args.output != "-":
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"wrote {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return _EXIT_OK


def _show_warning(
    message: Warning | str,
    category: type[Warning],
    filename: str,
    lineno: int,
    file: IO[str] | None = None,
    line: str | None = None,
) -> None:
    print(f"warning: {message}", file=sys.stderr)
