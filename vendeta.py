#!/usr/bin/env python3
"""Точка входа VENDETA OSINT — запуск: python vendeta.py"""
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

_APP = Path(__file__).resolve().parent / "app"
if str(_APP) not in sys.path:
    sys.path.insert(0, str(_APP))

from googlesearch import search
from phonenumbers import (
    PhoneNumberFormat,
    format_number,
    parse,
)
from rich import box
from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from analyzer import analyze_phone
from modules.dork_generator import generate_dork_links, list_categories
from modules.email_smtp import validate_email
from modules.inn_search import search_inn
from modules.netrecon import (
    PORT_PRESETS,
    clean_target,
    dns_lookup,
    full_network_search,
    ip_geolocation,
    port_scan,
    resolve_ip,
    whois_lookup,
)
from modules.github_search import search_github_repo
from modules.username_research import username_links_payload
from utils.json_output import print_json

console = Console()

TOOL_VERSION = "1.0.0"
CREATOR = "@brutalfire"
PANEL_KW = {"border_style": "red", "box": box.SQUARE, "padding": (0, 1)}
TITLE_TOOL = "[bold red]── TOOL DESCRIPTIONS ──[/bold red]"
TITLE_MENU = "[bold red]── MENU (1-12) ──[/bold red]"
GOOGLE_DORK_RESULTS = 10
MENU_COUNT = 12

MENU_ITEMS = [
    "Search by number",
    "Search by username",
    "Search by email",
    "Search by IIN",
    "Search by IP",
    "Google dork generator",
    "Port scanner",
    "DNS / IP lookup",
    "WHOIS lookup",
    "Network full search",
    "GitHub search",
    "Exit",
]

PHONE_EXTERNAL_LINKS = {
    "WhatsApp": "https://wa.me/{}",
    "Telegram": "https://t.me/+{}",
    "VK": "https://vk.com/{}",
    "Instagram": "https://www.instagram.com/{}/",
    "Facebook": "https://m.facebook.com/{}",
    "OK.ru": "https://ok.ru/{}",
}


def build_ascii_art() -> Text:
    art = Text(style="bold red")
    art.append(
        r"""
 __      ________ _   _ _____  ______ _______
 \ \    / /  ____| \ | |  __ \|  ____|__   __|/\
  \ \  / /| |__  |  \| | |  | | |__     | |  /  \
   \ \/ / |  __| | . ` | |  | |  __|    | | / /\ \
    \  /  | |____| |\  | |__| | |____   | |/ ____ \
     \/   |______|_| \_|_____/|______|  |_/_/    \_\
        """.strip("\n")
    )
    art.append(f"\nVENDETA OSINT TOOL\nV{TOOL_VERSION}\n", style="bold red")
    art.append("REMEMBER, REMEMBER...\nTHE 5TH OF NOVEMBER.\n\n", style="white")
    art.append(
        r"""
⣴⣶⣿⣿⣷⡶⢤⡀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡤⢶⣿⣿⣿⣿⣶⣄⠀⠀
⠀⢠⡿⠿⠿⠿⢿⣿⣿⣷⣦⡀⠀⠀⠀⠀⠀⠀⢀⣴⣾⣿⣿⡿⠿⠿⠿⠿⣦⠀
⠀⠀⠀⠀⠀⠀⠀⠈⠙⠿⣿⡿⠆⠀⠀⠀⠀⠰⣿⣿⠿⠋⠁⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⣀⣤⡤⠄⢤⣀⡈⢿⡄⠀⠀⠀⠀⢠⡟⢁⣠⡤⠠⠤⢤⣀⠀⠀⠀⠀
⠐⢄⣀⣼⢿⣾⣿⣿⣿⣷⣿⣆⠁⡆⠀⠀⢰⠈⢸⣿⣾⣿⣿⣿⣷⡮⣧⣀⡠⠀
⠰⠛⠉⠙⠛⠶⠶⠏⠷⠛⠋⠁⢠⡇⠀⠀⢸⡄⠈⠛⠛⠿⠹⠿⠶⠚⠋⠉⠛⠆
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣾⡇⠀⠀⢸⣷⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⠞⢻⠇⠀⠀⠘⡟⠳⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠰⣄⡀⠀⠀⣀⣠⡤⠞⠠⠁⠀⢸⠀⠀⠀⠀⡇⠀⠘⠄⠳⢤⣀⣀⠀⠀⣀⣠⠀
⠀⢻⣏⢻⣯⡉⠀⠀⠀⠀⠀⠒⢎⣓⠶⠶⣞⡱⠒⠀⠀⠀⠀⠀⢉⣽⡟⣹⡟⠀
⠀⠀⢻⣆⠹⣿⣆⣀⣀⣀⣀⣴⣿⣿⠟⠻⣿⣿⣦⣀⣀⣀⣀⣰⣿⠟⣰⡟⠀⠀
⠀⠀⠀⠻⣧⡘⠻⠿⠿⠿⠿⣿⣿⣃⣀⣀⣙⣿⣿⠿⠿⠿⠿⠟⢃⣴⠟⠀⠀⠀
⠀⠀⠀⠀⠙⣮⠐⠤⠀⠀⠀⠈⠉⠉⠉⠉⠉⠉⠁⠀⠀⠀⠤⠊⡵⠋⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠈⠳⡀⠀⠀⠀⠀⠀⠲⣶⣶⠖⠀⠀⠀⠀⠀⢀⠜⠁⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀⠀⠀⠀⢀⣿⣿⡀⠀⠀⠀⠀⠀⠁⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢿⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        """.strip("\n"),
        style="white",
    )
    return art


def google_dorks_search(dorks: list[str], num_results: int = GOOGLE_DORK_RESULTS) -> dict:
    items = []
    for dork in dorks:
        entry: dict = {"query": dork, "urls": []}
        try:
            entry["urls"] = list(search(dork, num_results=num_results, lang="en"))
        except Exception as exc:
            entry["error"] = str(exc)
        items.append(entry)
    return {"queries": items, "total_queries": len(items)}


def build_external_links(clean_digits: str) -> list[dict[str, str]]:
    if not clean_digits:
        return []
    return [
        {"service": name, "url": tpl.format(clean_digits)}
        for name, tpl in PHONE_EXTERNAL_LINKS.items()
    ]


def _brief_ok_ru(ok: dict) -> dict | None:
    if not ok:
        return None
    if ok.get("found"):
        return {
            "found": True,
            "name": ok.get("account_name"),
            "masked_phone": ok.get("masked_phone"),
            "info": ok.get("profile_info"),
        }
    return {"found": False, "message": ok.get("message")}


def run_phone_search(phone: str) -> dict:
    analysis = analyze_phone(phone, use_numverify=True, quiet=True)
    check = analysis.get("проверка_номера") or {}
    local = analysis.get("локальный_разбор") or {}
    messengers = analysis.get("мессенджеры") or {}
    coords = analysis.get("координаты")
    tz = check.get("часовые_пояса") or local.get("часовые_пояса") or []

    payload: dict = {
        "module": "search_by_number",
        "input": phone,
        "valid": bool(analysis.get("общая_проверка")),
        "e164": check.get("e164") or local.get("e164"),
        "country": check.get("местоположение")
        or check.get("страна_название")
        or local.get("местоположение"),
        "carrier": check.get("оператор") or local.get("оператор"),
        "line_type": check.get("тип_линии") or local.get("тип_линии"),
        "timezone": ", ".join(tz) if isinstance(tz, list) else tz,
        "coordinates": (
            {"lat": coords.get("широта"), "lon": coords.get("долгота")} if coords else None
        ),
        "messengers": {
            "whatsapp": messengers.get("whatsapp"),
            "telegram": messengers.get("telegram"),
        },
        "ok_ru": _brief_ok_ru(analysis.get("одноклассники") or {}),
        "external_links": [],
    }

    if local.get("ошибка"):
        payload["error"] = local["ошибка"]
        return payload

    e164 = payload.get("e164")
    if not e164:
        payload["error"] = "invalid_phone"
        return payload

    try:
        parsed = parse(e164, None)
        clean = re.sub(r"[^\d+]", "", format_number(parsed, PhoneNumberFormat.E164)).lstrip("+")
        payload["external_links"] = build_external_links(clean)
    except Exception as exc:
        payload["warning"] = str(exc)

    return payload


def run_username_search(username_q: str) -> dict:
    links = username_links_payload(username_q)
    if links.get("error"):
        return {"module": "search_by_username", "input": username_q, "error": links["error"]}
    return {
        "module": "search_by_username",
        "username": links["username"],
        "account_links": links["account_links"],
    }


def run_holehe(email: str) -> dict:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "holehe", email],
            capture_output=True,
            text=True,
            timeout=120,
        )
        return {
            "stdout": (result.stdout or "").strip(),
            "stderr": (result.stderr or "").strip(),
            "returncode": result.returncode,
        }
    except Exception as exc:
        return {"error": str(exc)}


def run_email_search(email: str) -> dict:
    dorks = [
        f'"{email}"',
        f'intext:"{email}" site:pastebin.com OR site:github.com',
        f'"{email}" filetype:txt OR filetype:log',
    ]
    return {
        "module": "search_by_email",
        "input": email,
        "smtp_validation": validate_email(email),
        "holehe": run_holehe(email),
        "google_dorks": google_dorks_search(dorks),
    }


def run_iin_search(iin: str) -> dict:
    return {
        "module": "search_by_iin",
        "input": iin,
        "ofdata": search_inn(iin),
    }


def run_ip_search(ip: str) -> dict:
    geo = ip_geolocation(ip.strip())
    return {
        "module": "search_by_ip",
        "input": ip,
        "ip": geo.get("ip", ip),
        "country": geo.get("country"),
        "city": geo.get("city"),
        "provider": geo.get("provider"),
        **({"error": geo["error"]} if geo.get("error") else {}),
    }


def run_dork_generator() -> dict:
    cats = list_categories()
    console.print("\n[bold red]Google dork categories[/bold red]")
    for c in cats:
        console.print(f"  [{c['id']}] {c['name']}")
    category_id = console.input("Category (1-13): ").strip()
    query = console.input("Query: ").strip()
    return {"module": "google_dork_generator", **generate_dork_links(category_id, query)}


def _ask_port_preset() -> str:
    console.print("\n[bold red]Port range[/bold red]")
    for key, (_, label) in PORT_PRESETS.items():
        console.print(f"  [{key}] {label}")
    choice = console.input("Choice [1]: ").strip() or "1"
    key, _ = PORT_PRESETS.get(choice, PORT_PRESETS["1"])
    if key == "custom":
        return console.input("Ports (80,443 or 1-1024): ").strip() or "common"
    return key


def run_port_scanner() -> dict:
    target = console.input("Domain or IP: ").strip()
    if not target:
        return {"module": "port_scanner", "error": "empty_target"}
    ports_spec = _ask_port_preset()
    return {"module": "port_scanner", **port_scan(clean_target(target), ports_spec)}


def run_dns_lookup() -> dict:
    target = console.input("Domain or IP: ").strip()
    if not target:
        return {"module": "dns_lookup", "error": "empty_target"}
    return {"module": "dns_lookup", **dns_lookup(clean_target(target))}


def run_whois() -> dict:
    target = console.input("Domain or IP: ").strip()
    if not target:
        return {"module": "whois_lookup", "error": "empty_target"}
    target = clean_target(target)
    ip = resolve_ip(target)
    geo = ip_geolocation(ip)
    return {
        "module": "whois_lookup",
        "target": target,
        "ip": geo.get("ip", ip),
        "country": geo.get("country"),
        "city": geo.get("city"),
        "provider": geo.get("provider"),
        "whois": whois_lookup(target),
    }


def run_network_full() -> dict:
    target = console.input("Domain or IP: ").strip()
    if not target:
        return {"module": "network_full_search", "error": "empty_target"}
    ports_spec = _ask_port_preset()
    return {
        "module": "network_full_search",
        **full_network_search(clean_target(target), ports_spec),
    }


def run_github_search() -> dict:
    repo_url = console.input("GitHub repository URL: ").strip()
    if not repo_url:
        return {"module": "github_search", "error": "empty_url"}
    return {"module": "github_search", **search_github_repo(repo_url)}


def _menu_tag(num: int) -> str:
    return f"[red][ {num} ][/red]" if num < 10 else f"[red][{num}][/red]"


def make_system_info(username: str) -> Panel:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    grid = Table.grid(padding=(0, 1))
    grid.add_column(style="red", justify="left", no_wrap=True)
    grid.add_column(style="white", justify="left")
    grid.add_row("Username:", username)
    grid.add_row("Creator:", CREATOR)
    grid.add_row("Time:", now)
    grid.add_row("Version:", TOOL_VERSION)
    return Panel(
        Align.left(grid, vertical="top"),
        title=TITLE_TOOL,
        title_align="center",
        **PANEL_KW,
    )


def make_menu() -> Panel:
    """Меню внизу: 4 колонки × 3 ряда, как на макете."""
    table = Table.grid(padding=(0, 2), expand=True)
    for _ in range(4):
        table.add_column(ratio=1, no_wrap=True)
    cols = 4
    rows = (len(MENU_ITEMS) + cols - 1) // cols
    for r in range(rows):
        line = []
        for c in range(cols):
            idx = r * cols + c
            if idx < len(MENU_ITEMS):
                num = idx + 1
                line.append(f"{_menu_tag(num)} {MENU_ITEMS[idx]}")
            else:
                line.append("")
        table.add_row(*line)
    return Panel(
        table,
        title=TITLE_MENU,
        title_align="center",
        **PANEL_KW,
    )


def render_header(username: str) -> None:
    console.print(f"[bold red]Enter nickname[/bold red] [white]> {username}[/white]\n")

    layout = Layout()
    layout.split_column(Layout(name="top", ratio=3), Layout(name="bottom", size=9))
    layout["top"].split_row(Layout(name="art", ratio=2), Layout(name="info", ratio=1))

    layout["art"].update(
        Panel(Align.left(build_ascii_art(), vertical="top"), title_align="left", **PANEL_KW)
    )
    layout["info"].update(make_system_info(username))
    layout["bottom"].update(make_menu())
    console.print(layout)


def main() -> None:
    session_user = (
        console.input("[bold red]Enter nickname[/bold red] [white]> [/white]").strip() or "vendetta"
    )

    while True:
        console.clear()
        render_header(session_user)
        choice = console.input(
            f"\n[bold red]Choose (1-{MENU_COUNT})[/bold red] [white]> [/white]"
        ).strip()

        result: dict | None = None

        if choice == "1":
            phone = console.input("Phone (+123...): ").strip()
            if phone:
                result = run_phone_search(phone)

        elif choice == "2":
            username_q = console.input("Username: ").strip()
            if username_q:
                result = run_username_search(username_q)

        elif choice == "3":
            email = console.input("Email: ").strip()
            if email and "@" in email:
                result = run_email_search(email)

        elif choice == "4":
            iin = console.input("IIN/BIN: ").strip()
            if iin:
                result = run_iin_search(iin)

        elif choice == "5":
            ip = console.input("IP: ").strip()
            if ip:
                result = run_ip_search(ip)

        elif choice == "6":
            result = run_dork_generator()

        elif choice == "7":
            result = run_port_scanner()

        elif choice == "8":
            result = run_dns_lookup()

        elif choice == "9":
            result = run_whois()

        elif choice == "10":
            result = run_network_full()

        elif choice == "11":
            result = run_github_search()

        elif choice == "12":
            print_json({"module": "exit", "message": "Goodbye"})
            break

        else:
            result = {"error": "invalid_choice", "choice": choice}

        if result is not None:
            print_json(result)

        if choice != "12":
            console.input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
