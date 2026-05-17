"""
OSINT-анализатор номера телефона.

Принцип работы:
  1. Нормализация и локальный разбор (phonenumbers) — страна, оператор, timezone.
  2. Опционально NumVerify — перекрёстная проверка и уточнение carrier/location.
  3. Геокодирование региона через OpenCage (если задан ключ).
  4. Поиск в мессенджерах и соцсетях по номеру.
"""

from __future__ import annotations

import json
from typing import Any

from modules.phone_info import (
    get_coordinates,
    get_local_phone_info,
    merge_phone_info,
    validate_via_numverify,
)
from modules.social import search_social_by_phone
from utils.progress_bar import show_progress_steps


def analyze_phone(
    number: str,
    *,
    use_numverify: bool = True,
    quiet: bool = False,
) -> dict[str, Any]:
    result: dict[str, Any] = {"введённый_номер": number}

    if not quiet:
        steps = [
            "Разбор номера (страна, оператор, timezone)",
            "Проверка через NumVerify",
            "Геокодирование региона",
            "Поиск в социальных сетях",
        ]
        show_progress_steps(steps, 0.3)

    local = get_local_phone_info(number)
    result["локальный_разбор"] = local

    remote: dict[str, Any] = {}
    if use_numverify:
        remote = validate_via_numverify(number)
        result["numverify"] = remote

    result["проверка_номера"] = merge_phone_info(local, remote)
    result["общая_проверка"] = result["проверка_номера"].get("действителен", False)

    region = result["проверка_номера"].get("местоположение")
    lat, lon = get_coordinates(region)
    result["координаты"] = {"широта": lat, "долгота": lon} if lat and lon else None

    result.update(search_social_by_phone(number))

    return result


def print_report(data: dict[str, Any]) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))
