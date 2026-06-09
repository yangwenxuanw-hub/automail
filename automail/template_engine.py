from __future__ import annotations

import re
from dataclasses import asdict, is_dataclass
from datetime import datetime
from enum import Enum
from typing import Any


_VAR_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}")


def _to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _lookup(path: str, context: dict[str, Any]) -> str | None:
    current: Any = context
    for key in path.split("."):
        if isinstance(current, dict) and key in current:
            current = current[key]
            continue
        return None
    value = _to_jsonable(current)
    if value is None:
        return None
    return str(value)


def render_template(content: str, context: dict[str, Any]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        resolved = _lookup(key, context)
        return resolved if resolved is not None else match.group(0)

    return _VAR_PATTERN.sub(replace, content)
