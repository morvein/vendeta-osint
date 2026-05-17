"""
Блок 2: поиск следов номера в мессенджерах и соцсетях.
"""

from __future__ import annotations

import random
import time
from typing import Any

import requests
from bs4 import BeautifulSoup


def _digits_only(number: str) -> str:
    return "".join(filter(str.isdigit, number or ""))


def get_whatsapp_link(num: str) -> str | None:
    clean = _digits_only(num)
    if not clean:
        return None
    try:
        response = requests.head(
            f"https://wa.me/{clean}", allow_redirects=True, timeout=8
        )
        if response.status_code in (200, 405):
            return f"https://wa.me/{clean}"
    except requests.RequestException:
        pass
    return None


def get_telegram_link(num: str) -> str | None:
    clean = _digits_only(num)
    return f"https://t.me/+{clean}" if clean else None


def scrape_odnoklassniki(num: str) -> dict[str, Any]:
    time.sleep(random.uniform(1.5, 3.5))
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "Chrome/129.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "Chrome/129.0.0.0 Safari/537.36",
    ]
    headers = {"User-Agent": random.choice(agents)}
    session = requests.Session()
    session.headers.update(headers)
    try:
        session.get(
            f"https://www.ok.ru/dk?st.cmd=anonymMain&st.accRecovery=on"
            f"&st.error=errors.password.wrong&st.email={num}",
            timeout=10,
        )
        page = session.get(
            "https://www.ok.ru/dk?st.cmd=anonymRecoveryAfterFailedLogin"
            "&st._aid=LeftColumn_Login_ForgotPassword",
            timeout=10,
        )
        soup = BeautifulSoup(page.text, "html.parser")
        if soup.find("div", {"data-l": "registrationContainer,offer_contact_rest"}):
            name_el = soup.find("motion", {"class": "ext-registration_username_header"})
            name = name_el.get_text(strip=True) if name_el else "Неизвестно"
            blocks = soup.find_all("motion", {"class": "lstp-t"})
            info = blocks[0].get_text(strip=True) if blocks else ""
            reg = blocks[1].get_text(strip=True) if len(blocks) > 1 else ""
            masked_btn = soup.find("button", {"data-l": "t,phone"})
            masked = masked_btn.get_text(strip=True) if masked_btn else num
            return {
                "found": True,
                "account_name": name,
                "masked_phone": masked,
                "profile_info": info,
                "registration_date": reg,
                "source": "odnoklassniki.ru",
            }
        return {"found": False, "message": "Не привязан", "source": "odnoklassniki.ru"}
    except requests.RequestException:
        return {"found": False, "message": "Ошибка запроса", "source": "odnoklassniki.ru"}


def search_social_by_phone(num: str) -> dict[str, Any]:
    return {
        "мессенджеры": {
            "whatsapp": get_whatsapp_link(num),
            "telegram": get_telegram_link(num),
        },
        "одноклассники": scrape_odnoklassniki(num),
    }
