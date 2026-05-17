"""Проверка email: формат, MX, SMTP RCPT."""

from __future__ import annotations

import re
import smtplib
import socket

import dns.resolver


def validate_email(email: str) -> dict:
    result: dict = {
        "email": email,
        "valid_format": False,
        "domain": None,
        "mx_found": False,
        "mx_host": None,
        "smtp_check": None,
    }

    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(pattern, email):
        return result

    result["valid_format"] = True
    domain = email.split("@", 1)[1]
    result["domain"] = domain

    try:
        mx_records = dns.resolver.resolve(domain, "MX")
        mx_host = str(mx_records[0].exchange).rstrip(".")
        result["mx_found"] = True
        result["mx_host"] = mx_host
    except Exception as exc:
        result["mx_error"] = str(exc)
        return result

    try:
        smtp = smtplib.SMTP(timeout=10)
        smtp.connect(mx_host)
        smtp.helo("test.com")
        smtp.mail("check@test.com")
        code, message = smtp.rcpt(email)
        result["smtp_check"] = {
            "code": code,
            "message": message.decode(errors="ignore") if isinstance(message, bytes) else str(message),
        }
        smtp.quit()
    except (socket.timeout, Exception) as exc:
        result["smtp_check"] = "unknown"
        result["smtp_error"] = str(exc)

    return result
