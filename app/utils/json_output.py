"""Вывод результатов в терминал как JSON."""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any


def _default(obj: Any) -> Any:
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)


def print_json(data: Any, *, indent: int = 2) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=indent, default=_default))
