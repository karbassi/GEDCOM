"""The ``gedcom`` command-line entry point (argparse, stdlib only).

Subcommands ``build``, ``validate``, ``init``, ``schema``, ``guide``, and
``help`` are thin shells over the reader, loader, and writer. The tool is
designed to be driven by both people and AI agents: ``schema``/``guide`` make
the authoring dialect self-describing, and ``--json`` gives ``build`` and
``validate`` structured, parseable output (including structured errors).

Exit codes: ``0`` success, ``1`` validation failure, ``2`` usage/input error.
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

from .. import __version__
from ..validation import ValidationError, validate
from ..writer import dump, dumps
from .errors import LoadError
from .loader import build_document
from .reader import read_document
from .scaffold import scaffold
from .schema import GUIDE, schema_json, schema_text

_EXIT_OK = 0
_EXIT_VALIDATION = 1
_EXIT_INPUT = 2


def main(argv: list[str] | None = None) -> int:
    """Parse ``argv`` and dispatch to a subcommand; return the exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return _EXIT_OK
    use_json = bool(getattr(args, "json", False))
    try:
        result: int = args.handler(args)
        return result
    except LoadError as error:
        _emit_error(use_json, error.raw, path=error.path.lstrip("."))
        return _EXIT_INPUT
    except ValidationError as error:
        _emit_error(use_json, str(error))
        return _EXIT_VALIDATION


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gedcom",
        description="Build GEDCOM 7 files from a YAML/JSON/TOML authoring document.",
    )
    parser.add_argument("--version", action="version", version=f"gedcom {__version__}")
    sub = parser.add_subparsers(dest="command", required=False, metavar="command")

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
    build.add_argument(
        "--json", action="store_true", help="emit a structured JSON result (requires -o)"
    )
    build.set_defaults(handler=_cmd_build)

    check = sub.add_parser("validate", help="check an authoring document without writing output")
    check.add_argument("input", help="authoring document (.yaml/.yml/.json/.toml)")
    check.add_argument("--json", action="store_true", help="emit issues as structured JSON")
    check.set_defaults(handler=_cmd_validate)

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

    schema_parser = sub.add_parser(
        "schema", help="describe the authoring dialect (for agents): sections, enums, dates"
    )
    schema_parser.add_argument(
        "-f",
        "--format",
        choices=("json", "text"),
        default="json",
        help="output format (default: json)",
    )
    schema_parser.set_defaults(handler=_cmd_schema)

    guide = sub.add_parser("guide", help="print an agent-oriented walkthrough of the workflow")
    guide.set_defaults(handler=_cmd_guide)

    help_parser = sub.add_parser("help", help="show help for the tool or a specific command")
    help_parser.add_argument("topic", nargs="?", help="command to describe")
    help_parser.set_defaults(handler=_cmd_help)

    commands = {
        "build": build,
        "validate": check,
        "init": init,
        "schema": schema_parser,
        "guide": guide,
        "help": help_parser,
    }
    parser.set_defaults(_parser=parser, _commands=commands)
    return parser


def _cmd_build(args: argparse.Namespace) -> int:
    document = build_document(read_document(args.input))
    strict = not args.lenient
    destination = args.output
    if args.json and destination in (None, "-"):
        raise LoadError("with --json, write the GEDCOM to a file with -o (stdout carries the JSON)")
    if destination in (None, "-"):
        with _CapturedWarnings() as caught:
            text = dumps(document, strict=strict)
        sys.stdout.write(text)
        _print_warnings(caught)
        return _EXIT_OK
    suffix = Path(destination).suffix.lower()
    with _CapturedWarnings() as caught:
        if suffix == ".gdz":
            from ..gedzip import dump_gedzip

            dump_gedzip(document, destination, strict=strict)
            kind = "gedzip"
        elif suffix == ".ged":
            dump(document, destination, strict=strict)
            kind = "gedcom"
        else:
            raise LoadError(f"unknown output extension {suffix or '(none)'!r}; use .ged or .gdz")
    if args.json:
        print(
            json.dumps(
                {
                    "ok": True,
                    "output": destination,
                    "format": kind,
                    "records": len(document.records),
                    "warnings": caught,
                }
            )
        )
    else:
        _print_warnings(caught)
        print(f"wrote {destination}", file=sys.stderr)
    return _EXIT_OK


def _cmd_validate(args: argparse.Namespace) -> int:
    document = build_document(read_document(args.input))
    issues = validate(document, strict=False)
    if args.json:
        print(json.dumps({"ok": not issues, "issues": issues}))
        return _EXIT_VALIDATION if issues else _EXIT_OK
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


def _cmd_schema(args: argparse.Namespace) -> int:
    sys.stdout.write(schema_text() if args.format == "text" else schema_json() + "\n")
    return _EXIT_OK


def _cmd_guide(args: argparse.Namespace) -> int:
    sys.stdout.write(GUIDE)
    return _EXIT_OK


def _cmd_help(args: argparse.Namespace) -> int:
    topic = args.topic
    commands = args._commands
    if topic and topic in commands:
        commands[topic].print_help()
    else:
        args._parser.print_help()
    return _EXIT_OK


def _emit_error(use_json: bool, message: str, *, path: str = "") -> None:
    if use_json:
        error: dict[str, str] = {"message": message}
        if path:
            error["path"] = path
        print(json.dumps({"ok": False, "error": error}))
    else:
        location = f"{path}: " if path else ""
        print(f"error: {location}{message}", file=sys.stderr)


class _CapturedWarnings:
    """Context manager yielding a list of warning messages raised in the block."""

    def __init__(self) -> None:
        self._messages: list[str] = []
        self._catcher = warnings.catch_warnings(record=True)
        self._records: list[warnings.WarningMessage] | None = None

    def __enter__(self) -> list[str]:
        self._records = self._catcher.__enter__()
        warnings.simplefilter("always")
        return self._messages

    def __exit__(self, *exc: object) -> None:
        for record in self._records or []:
            self._messages.append(str(record.message))
        self._catcher.__exit__(None, None, None)


def _print_warnings(messages: list[str]) -> None:
    for message in messages:
        print(f"warning: {message}", file=sys.stderr)
