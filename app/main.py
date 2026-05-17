#!/usr/bin/env python3
"""Точка входа OSINT-инструмента по номеру телефона."""

import argparse
import sys

from analyzer import analyze_phone, print_report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="OSINT: базовая информация о номере и поиск в соцсетях",
    )
    parser.add_argument(
        "number",
        nargs="?",
        help="Номер телефона (+79..., 8..., и т.д.)",
    )
    parser.add_argument(
        "--no-numverify",
        action="store_true",
        help="Только локальный разбор (phonenumbers), без NumVerify",
    )
    args = parser.parse_args()

    number = args.number
    if not number:
        number = input("Введите номер телефона: ").strip()
    if not number:
        print("Номер не указан.", file=sys.stderr)
        return 1

    report = analyze_phone(number, use_numverify=not args.no_numverify)
    print_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
