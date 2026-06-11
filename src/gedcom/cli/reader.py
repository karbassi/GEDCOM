"""Read an authoring document from a file into a plain mapping.

The parser is chosen by file extension: ``.json`` uses the standard library;
``.yaml``/``.yml`` use PyYAML, imported lazily so it stays an optional extra
(``gedcom[yaml]``) and the core install needs no runtime dependency.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .errors import LoadError

_YAML_SUFFIXES = {".yaml", ".yml"}
_JSON_SUFFIXES = {".json"}


def read_document(path: str | Path) -> dict[str, Any]:
    """Parse the file at ``path`` and return its top-level mapping."""
    path = Path(path)
    suffix = path.suffix.lower()
    try:
        text = path.read_bytes()
    except OSError as error:
        raise LoadError(f"cannot read {path}: {error.strerror or error}") from None
    if suffix in _JSON_SUFFIXES:
        data = _parse_json(text, path)
    elif suffix in _YAML_SUFFIXES:
        data = _parse_yaml(text, path)
    else:
        raise LoadError(
            f"unsupported input extension {suffix or '(none)'!r}; use .yaml, .yml, or .json"
        )
    if not isinstance(data, dict):
        raise LoadError(f"{path}: the document root must be a mapping, got {type(data).__name__}")
    return data


def _parse_json(text: bytes, path: Path) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        raise LoadError(f"{path}: invalid JSON: {error}") from None


def _parse_yaml(text: bytes, path: Path) -> Any:
    try:
        import yaml
    except ModuleNotFoundError:
        raise LoadError(
            "reading YAML needs PyYAML, which is an optional extra; "
            "install it with 'pip install gedcom[yaml]', or use a .json file"
        ) from None
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as error:
        raise LoadError(f"{path}: invalid YAML: {error}") from None
