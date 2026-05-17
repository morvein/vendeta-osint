"""Сетевые инструменты: DNS, порты, WHOIS, полное сканирование."""

from __future__ import annotations

import socket
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any

import requests

try:
    import whois

    WHOIS_AVAILABLE = True
except ImportError:
    WHOIS_AVAILABLE = False

try:
    import dns.resolver

    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False

RECORD_TYPES = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"]

COMMON_PORTS = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    111: "RPCBind",
    135: "MSRPC",
    139: "NetBIOS",
    143: "IMAP",
    443: "HTTPS",
    445: "SMB",
    587: "SMTP/TLS",
    993: "IMAPS",
    995: "POP3S",
    1433: "MSSQL",
    1521: "Oracle",
    3306: "MySQL",
    3389: "RDP",
    5432: "PgSQL",
    5900: "VNC",
    6379: "Redis",
    8080: "HTTP-Alt",
    8443: "HTTPS-Alt",
    27017: "MongoDB",
}

PORT_PRESETS = {
    "1": ("common", "Популярные порты"),
    "2": ("1-1024", "Системные 1–1024"),
    "3": ("1-65535", "Все порты 1–65535"),
    "4": ("custom", "Вручную"),
}

WHOIS_FIELDS = [
    "domain_name",
    "registrar",
    "creation_date",
    "expiration_date",
    "updated_date",
    "name_servers",
    "status",
    "emails",
    "country",
    "org",
]


def clean_target(raw: str) -> str:
    t = raw.strip().lower()
    for prefix in ("https://", "http://", "ftp://"):
        if t.startswith(prefix):
            t = t[len(prefix) :]
    return t.rstrip("/")


def parse_ports(arg: str) -> list[int]:
    if arg.strip().lower() == "common":
        return list(COMMON_PORTS.keys())
    ports: set[int] = set()
    for part in arg.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            ports.update(range(int(a), int(b) + 1))
        elif part.isdigit():
            ports.add(int(part))
    return sorted(ports)


def resolve_ip(target: str) -> str:
    try:
        return socket.gethostbyname(target)
    except socket.gaierror:
        return target


def ip_geolocation(ip: str) -> dict[str, Any]:
    """Страна, город, провайдер по IP (ipapi.co)."""
    out: dict[str, Any] = {
        "ip": ip,
        "country": None,
        "city": None,
        "provider": None,
    }
    try:
        response = requests.get(f"https://ipapi.co/{ip}/json/", timeout=12)
        if response.status_code == 200:
            data = response.json()
            out["ip"] = data.get("ip", ip)
            out["country"] = data.get("country_name")
            out["city"] = data.get("city")
            out["provider"] = data.get("org")
        else:
            out["error"] = f"HTTP {response.status_code}"
    except requests.RequestException as exc:
        out["error"] = str(exc)
    return out


def dns_lookup(target: str) -> dict[str, Any]:
    target = clean_target(target)
    ip: str | None = None
    records: dict[str, list[str]] = {}
    try:
        ip = socket.gethostbyname(target)
    except socket.gaierror as exc:
        return {"target": target, "error": str(exc)}

    if DNS_AVAILABLE:
        resolver = dns.resolver.Resolver()
        resolver.timeout = 3
        resolver.lifetime = 5
        for rtype in RECORD_TYPES:
            try:
                records[rtype] = [str(a) for a in resolver.resolve(target, rtype)]
            except Exception:
                pass

    geo = ip_geolocation(ip)
    return {
        "target": target,
        "ip": geo.get("ip", ip),
        "country": geo.get("country"),
        "city": geo.get("city"),
        "provider": geo.get("provider"),
        "dns_records": records,
    }


def _is_port_open(ip: str, port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1.0)
            return sock.connect_ex((ip, port)) == 0
    except OSError:
        return False


def scan_ports(ip: str, ports: list[int], max_workers: int = 100) -> list[int]:
    open_ports: list[int] = []

    def check(port: int) -> int | None:
        return port if _is_port_open(ip, port) else None

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        for port in pool.map(check, ports):
            if port is not None:
                open_ports.append(port)
    return sorted(open_ports)


def whois_lookup(target: str) -> dict[str, Any]:
    if not WHOIS_AVAILABLE:
        return {"error": "python-whois не установлен", "hint": "pip install python-whois"}
    try:
        record = whois.whois(target)
    except Exception as exc:
        return {"error": str(exc)}
    data: dict[str, Any] = {"target": target}
    for key in WHOIS_FIELDS:
        val = getattr(record, key, None)
        if val is not None:
            data[key] = val
    return data


def port_scan(target: str, ports_spec: str) -> dict[str, Any]:
    target = clean_target(target)
    ip = resolve_ip(target)
    try:
        ports = parse_ports(ports_spec)
    except (ValueError, TypeError) as exc:
        return {"error": f"неверный диапазон портов: {exc}"}
    geo = ip_geolocation(ip)
    return {
        "target": target,
        "ip": geo.get("ip", ip),
        "country": geo.get("country"),
        "city": geo.get("city"),
        "provider": geo.get("provider"),
        "open_ports": scan_ports(ip, ports),
    }


def full_network_search(target: str, ports_spec: str = "common") -> dict[str, Any]:
    target = clean_target(target)
    started = datetime.now()
    dns = dns_lookup(target)
    ip = dns.get("ip") or resolve_ip(target)
    geo = ip_geolocation(ip)
    try:
        port_list = parse_ports(ports_spec)
    except (ValueError, TypeError):
        port_list = list(COMMON_PORTS.keys())
    elapsed = (datetime.now() - started).total_seconds()
    return {
        "target": target,
        "ip": geo.get("ip", ip),
        "country": geo.get("country") or dns.get("country"),
        "city": geo.get("city") or dns.get("city"),
        "provider": geo.get("provider") or dns.get("provider"),
        "open_ports": scan_ports(ip, port_list),
        "dns_records": dns.get("dns_records", {}),
        "whois": whois_lookup(target),
        "elapsed_seconds": round(elapsed, 2),
    }
