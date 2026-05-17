"""
Поиск никнейма по списку площадок (HTTP-проверка профиля).
"""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlparse

import requests

Status = Literal["found", "not_found", "unknown", "error"]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
)

NOT_FOUND_HINTS = (
    "page not found",
    "page isn't available",
    "this page is not available",
    "user not found",
    "profile not found",
    "couldn't find",
    "does not exist",
    "doesn't exist",
    "no user",
    "not exist",
    "404",
    "sorry, this page",
)

# (категория, название, url-шаблон)
USERNAME_SITES: list[tuple[str, str, str]] = [
    ("Соцсети / мессенджеры", "Instagram", "https://instagram.com/{username}"),
    ("Соцсети / мессенджеры", "TikTok", "https://www.tiktok.com/@{username}"),
    ("Соцсети / мессенджеры", "X", "https://x.com/{username}"),
    ("Соцсети / мессенджеры", "Facebook", "https://facebook.com/{username}"),
    ("Соцсети / мессенджеры", "VK", "https://vk.com/{username}"),
    ("Соцсети / мессенджеры", "Telegram", "https://t.me/{username}"),
    ("Соцсети / мессенджеры", "Snapchat", "https://snapchat.com/add/{username}"),
    ("Соцсети / мессенджеры", "Threads", "https://www.threads.net/@{username}"),
    ("Соцсети / мессенджеры", "Reddit", "https://reddit.com/user/{username}"),
    ("Соцсети / мессенджеры", "Pinterest", "https://www.pinterest.com/{username}"),
    ("Соцсети / мессенджеры", "Mastodon", "https://mastodon.social/@{username}"),
    ("Соцсети / мессенджеры", "Bluesky", "https://bsky.app/profile/{username}"),
    ("Соцсети / мессенджеры", "Tumblr", "https://www.tumblr.com/{username}"),
    ("Соцсети / мессенджеры", "Flickr", "https://www.flickr.com/people/{username}"),
    ("Игры / комьюнити", "Steam (id)", "https://steamcommunity.com/id/{username}"),
    ("Игры / комьюнити", "Steam (profiles)", "https://steamcommunity.com/profiles/{username}"),
    ("Игры / комьюнити", "Roblox", "https://www.roblox.com/users/profile?username={username}"),
    ("Игры / комьюнити", "Twitch", "https://twitch.tv/{username}"),
    ("Игры / комьюнити", "Kick", "https://kick.com/{username}"),
    ("Игры / комьюнити", "FACEIT", "https://www.faceit.com/en/players/{username}"),
    ("Игры / комьюнити", "Tracker.gg Valorant", "https://tracker.gg/valorant/profile/riot/{username}"),
    ("Игры / комьюнити", "Tracker.gg Apex", "https://tracker.gg/apex/profile/origin/{username}"),
    ("Игры / комьюнити", "osu!", "https://osu.ppy.sh/users/{username}"),
    ("Игры / комьюнити", "Lichess", "https://lichess.org/@/{username}"),
    ("Игры / комьюнити", "Chess.com", "https://www.chess.com/member/{username}"),
    ("Dev / tech / coding", "GitHub", "https://github.com/{username}"),
    ("Dev / tech / coding", "GitLab", "https://gitlab.com/{username}"),
    ("Dev / tech / coding", "Bitbucket", "https://bitbucket.org/{username}"),
    ("Dev / tech / coding", "Replit", "https://replit.com/@{username}"),
    ("Dev / tech / coding", "dev.to", "https://dev.to/{username}"),
    ("Dev / tech / coding", "Stack Overflow", "https://stackoverflow.com/users/{username}"),
    ("Dev / tech / coding", "Codecademy", "https://www.codecademy.com/profiles/{username}"),
    ("Dev / tech / coding", "LeetCode", "https://leetcode.com/{username}"),
    ("Dev / tech / coding", "HackerRank", "https://www.hackerrank.com/{username}"),
    ("Dev / tech / coding", "TryHackMe", "https://tryhackme.com/p/{username}"),
    ("Dev / tech / coding", "HackTheBox", "https://app.hackthebox.com/profile/{username}"),
    ("Dev / tech / coding", "Keybase", "https://keybase.io/{username}"),
    ("Контент / творчество", "YouTube", "https://youtube.com/@{username}"),
    ("Контент / творчество", "SoundCloud", "https://soundcloud.com/{username}"),
    ("Контент / творчество", "Behance", "https://www.behance.net/{username}"),
    ("Контент / творчество", "Dribbble", "https://dribbble.com/{username}"),
    ("Контент / творчество", "DeviantArt", "https://www.deviantart.com/{username}"),
    ("Контент / творчество", "Medium", "https://medium.com/@{username}"),
    ("Контент / творчество", "Product Hunt", "https://www.producthunt.com/@{username}"),
    ("Контент / творчество", "Spotify", "https://open.spotify.com/user/{username}"),
    ("Форумы / misc", "Quora", "https://www.quora.com/profile/{username}"),
    ("Форумы / misc", "Disqus", "https://disqus.com/by/{username}"),
    ("Форумы / misc", "Goodreads", "https://www.goodreads.com/{username}"),
    ("Форумы / misc", "Letterboxd", "https://letterboxd.com/{username}"),
    ("Форумы / misc", "Last.fm", "https://www.last.fm/user/{username}"),
]


@dataclass
class SiteResult:
    category: str
    platform: str
    url: str
    status: Status
    http_code: int | None = None
    note: str = ""


def normalize_username(raw: str) -> str:
    name = (raw or "").strip().lstrip("@")
    if not name:
        return ""
    if not re.match(r"^[\w.\-]+$", name, re.UNICODE):
        return ""
    return name


def _body_suggests_missing(text: str, username: str) -> bool:
    sample = (text or "")[:12000].lower()
    if not sample:
        return False
    uname = username.lower()
    if f'"{uname}"' in sample and "not found" in sample:
        return True
    return any(hint in sample for hint in NOT_FOUND_HINTS)


def _classify_response(url: str, username: str, response: requests.Response) -> tuple[Status, str]:
    code = response.status_code
    final_url = (response.url or url).lower()

    if code == 404:
        return "not_found", "HTTP 404"
    if code == 410:
        return "not_found", "HTTP 410"
    if code in (401, 403, 429, 999):
        return "unknown", f"HTTP {code} — проверьте вручную"
    if code >= 500:
        return "error", f"HTTP {code}"

    if code not in (200, 201, 203, 206):
        return "unknown", f"HTTP {code}"

    host = urlparse(final_url).netloc
    if "login" in final_url or "signin" in final_url or "signup" in final_url:
        return "unknown", "редирект на вход"

    text = response.text or ""
    if _body_suggests_missing(text, username):
        return "not_found", "страница «не найдено»"

    if host.endswith("github.com") and "not found" in text[:800].lower():
        return "not_found", "GitHub 404"
    if host.endswith("instagram.com") and "login" in text[:2000].lower() and username.lower() not in text[:3000].lower():
        return "unknown", "Instagram требует вход"

    return "found", "профиль доступен"


def check_site(category: str, platform: str, url: str, username: str) -> SiteResult:
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}
    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=12,
            allow_redirects=True,
        )
        status, note = _classify_response(url, username, response)
        return SiteResult(
            category=category,
            platform=platform,
            url=url,
            status=status,
            http_code=response.status_code,
            note=note,
        )
    except requests.Timeout:
        return SiteResult(category, platform, url, "error", None, "таймаут")
    except requests.RequestException as exc:
        return SiteResult(category, platform, url, "error", None, str(exc)[:80])


def research_username(
    username: str,
    *,
    max_workers: int = 14,
) -> tuple[str, list[SiteResult]]:
    """Проверяет ник на всех площадках. Возвращает (нормализованный_ник, результаты)."""
    clean = normalize_username(username)
    if not clean:
        return "", []

    tasks = [
        (cat, plat, tpl.format(username=clean), clean)
        for cat, plat, tpl in USERNAME_SITES
    ]

    results: list[SiteResult] = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(check_site, cat, plat, url, clean): (cat, plat)
            for cat, plat, url, clean in tasks
        }
        for future in as_completed(futures):
            results.append(future.result())

    order = {name: i for i, (_, name, _) in enumerate(USERNAME_SITES)}
    results.sort(key=lambda r: (r.category, order.get(r.platform, 999)))
    return clean, results


def build_external_links(username: str) -> list[tuple[str, str, str]]:
    """Все ссылки по нику без HTTP-проверки (справочно)."""
    clean = normalize_username(username)
    if not clean:
        return []
    return [(cat, plat, tpl.format(username=clean)) for cat, plat, tpl in USERNAME_SITES]


def username_links_payload(username: str) -> dict:
    """Ник + плоский список ссылок на аккаунты."""
    clean = normalize_username(username)
    if not clean:
        return {"error": "invalid_username"}

    return {
        "username": clean,
        "account_links": [url for _, _, url in build_external_links(username)],
    }
