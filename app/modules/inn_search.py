"""Поиск по ИНН через api.ofdata.ru."""

from __future__ import annotations

from typing import Any

import requests

from config import OFDATA_API_KEY


def search_inn(inn_value: str) -> dict[str, Any] | list[dict[str, Any]]:
    if not inn_value:
        return {"error": "ИНН не может быть пустым"}
    if not inn_value.isdigit():
        return {"error": "ИНН должен содержать только цифры"}
    if not OFDATA_API_KEY:
        return {"error": "не задан OFDATA_API_KEY в .env"}

    url = f"https://api.ofdata.ru/v2/person?key={OFDATA_API_KEY}&inn={inn_value}"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get("meta", {}).get("status") == "ok":
            records = data.get("data", {}).get("Записи", data.get("data", {}))
            if isinstance(records, list):
                cleaned_records = records
            elif isinstance(records, dict):
                cleaned_records = [records] if records else []
            else:
                cleaned_records = []

            result = []
            for item in cleaned_records:
                filtered = {
                    k: v
                    for k, v in item.items()
                    if v is not None and k not in ("Учред", "Руковод")
                }
                if filtered:
                    result.append(filtered)
            if not result:
                return {"message": "Данные не найдены"}
            return result

        error_msg = (
            data.get("meta", {}).get("msg")
            or data.get("meta", {}).get("error")
            or "Ошибка при получении данных от API"
        )
        return {"error": error_msg}

    except requests.exceptions.Timeout:
        return {"error": "Превышено время ожидания ответа от API"}
    except requests.exceptions.RequestException as exc:
        return {"error": f"Ошибка соединения: {exc}"}
    except Exception as exc:
        return {"error": f"Ошибка при выполнении запроса: {exc}"}
