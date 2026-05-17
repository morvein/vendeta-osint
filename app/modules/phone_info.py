"""
Блок 1: базовая информация о номере (локально + опционально NumVerify / OpenCage).
"""

from __future__ import annotations

import re
from typing import Any

import phonenumbers
import requests
from phonenumbers import (
    NumberParseException,
    carrier,
    geocoder,
    timezone,
)
from phonenumbers.phonenumberutil import number_type, region_code_for_number

from config import DEFAULT_COUNTRY_CODE, NUMVERIFY_API_KEY, OPENCAGE_API_KEY

_LINE_TYPE_RU = {
    0: "фиксированная",
    1: "мобильная",
    2: "фиксированная или мобильная",
    3: "толл-фри",
    4: "премиум",
    5: "общий доступ",
    6: "VoIP",
    7: "персональный",
    8: "пейджер",
    9: "UAN",
    10: "голосовая почта",
    -1: "неизвестно",
}


def _digits_only(number: str) -> str:
    return re.sub(r"\D", "", number or "")


def parse_number(number: str, region: str | None = None) -> phonenumbers.PhoneNumber | None:
    region = region or DEFAULT_COUNTRY_CODE
    raw = number.strip()
    if not raw:
        return None
    try:
        return phonenumbers.parse(raw, region if not raw.startswith("+") else None)
    except NumberParseException:
        return None


def get_local_phone_info(number: str, region: str | None = None) -> dict[str, Any]:
    """Метаданные через libphonenumber (без внешних API)."""
    parsed = parse_number(number, region)
    if parsed is None:
        return {
            "действителен": False,
            "ошибка": "не удалось разобрать номер",
        }

    valid = phonenumbers.is_valid_number(parsed)
    possible = phonenumbers.is_possible_number(parsed)
    country_code = parsed.country_code
    region_iso = region_code_for_number(parsed) or ""
    national = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
    e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    international = phonenumbers.format_number(
        parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
    )

    carrier_name = carrier.name_for_number(parsed, "ru") or carrier.name_for_number(parsed, "en")
    location = geocoder.description_for_number(parsed, "ru") or geographer_fallback(parsed)
    tz_list = list(timezone.time_zones_for_number(parsed))
    ntype = number_type(parsed)

    return {
        "действителен": valid,
        "возможен": possible,
        "код_страны": country_code,
        "регион_iso": region_iso,
        "национальный_формат": national,
        "международный_формат": international,
        "e164": e164,
        "оператор": carrier_name or None,
        "местоположение": location or None,
        "часовые_пояса": tz_list,
        "тип_линии": _LINE_TYPE_RU.get(ntype, _LINE_TYPE_RU[-1]),
        "источник": "phonenumbers (libphonenumber)",
    }


def geographer_fallback(parsed: phonenumbers.PhoneNumber) -> str | None:
    return geocoder.description_for_number(parsed, "en") or None


def validate_via_numverify(number: str, access_key: str | None = None) -> dict[str, Any]:
    key = access_key or NUMVERIFY_API_KEY
    if not key:
        return {"доступно": False, "причина": "не задан NUMVERIFY_API_KEY"}

    url = (
        "http://apilayer.net/api/validate"
        f"?access_key={key}&number={requests.utils.quote(number)}"
        f"&country_code={DEFAULT_COUNTRY_CODE}&format=1"
    )
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        return {
            "доступно": True,
            "действителен": data.get("valid", False),
            "оператор": data.get("carrier"),
            "тип_линии": data.get("line_type"),
            "местоположение": data.get("location"),
            "страна": data.get("country_name"),
            "код_страны": data.get("country_code"),
            "локальная_версия": data.get("local_format"),
            "сырой_ответ": data,
            "источник": "numverify",
        }
    except requests.RequestException as exc:
        return {"доступно": False, "ошибка": str(exc), "источник": "numverify"}


def get_coordinates(city: str | None, api_key: str | None = None) -> tuple[float | None, float | None]:
    if not city:
        return None, None
    key = api_key or OPENCAGE_API_KEY
    if not key:
        return None, None
    try:
        response = requests.get(
            "https://api.opencagedata.com/geocode/v1/json",
            params={"q": city, "key": key, "limit": 1, "language": "ru"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("results"):
            geometry = data["results"][0]["geometry"]
            return geometry["lat"], geometry["lng"]
    except requests.RequestException:
        pass
    return None, None


def merge_phone_info(local: dict[str, Any], remote: dict[str, Any]) -> dict[str, Any]:
    """Сводка: приоритет локальной валидации + дополнение из API."""
    merged = {
        "действителен": local.get("действителен", False),
        "страна_iso": local.get("регион_iso"),
        "страна_название": remote.get("страна") if remote.get("доступно") else None,
        "оператор": local.get("оператор") or remote.get("оператор"),
        "тип_линии": local.get("тип_линии") or remote.get("тип_линии"),
        "местоположение": local.get("местоположение") or remote.get("местоположение"),
        "часовые_пояса": local.get("часовые_пояса", []),
        "e164": local.get("e164"),
        "форматы": {
            "национальный": local.get("национальный_формат"),
            "международный": local.get("международный_формат"),
        },
    }
    if remote.get("доступно"):
        merged["действителен"] = merged["действителен"] or remote.get("действителен", False)
    return merged
