"""Генератор ссылок Google dork по категориям."""

from __future__ import annotations

import urllib.parse

DORK_CATEGORIES: dict[str, list[str]] = {
    "1": ["ФИО", '"{q}"', '"{q}" site:github.com', '"{q}" site:vk.com', '"{q}" site:linkedin.com'],
    "2": ["Телефон", '"{q}" site:forum.*', '"{q}" (contact OR whatsapp OR telegram)'],
    "3": ["Адрес", '"{q}" filetype:pdf', '"{q}" site:maps.*'],
    "4": ["Координаты", '"{q}" "latitude" OR "longitude"'],
    "5": ["IP", '"{q}" site:github.com', '"{q}" filetype:log OR filetype:txt'],
    "6": ["Домен", "site:{q}", '"{q}" whois OR dns OR mx'],
    "7": ["ИИН/БИН", '"{q}" site:gov.*', '"{q}" filetype:pdf OR filetype:xls'],
    "8": ["Компания", '"{q}" site:linkedin.com/company', '"{q}" site:gov.*'],
    "9": [
        "Соцсети",
        '"{q}" site:instagram.com',
        '"{q}" site:vk.com',
        '"{q}" site:x.com',
    ],
    "10": ["Школа", '"{q}" site:edu.*', '"{q}" filetype:pdf'],
    "11": ["Университет", '"{q}" site:edu.*', '"{q}" university OR faculty'],
    "12": ["Никнейм", '"{q}"', '"{q}123"', '"{q}_"', 'intitle:"{q}"'],
    "13": [
        "Email",
        '"{q}" site:github.com',
        '"{q}" filetype:txt OR filetype:csv',
        '"{q}" "@gmail.com" OR "@outlook.com"',
    ],
}

# шаблоны dork (без первого элемента — это название категории)
DORKS: dict[str, list[str]] = {
    k: v[1:] for k, v in DORK_CATEGORIES.items()
}


def build_google_link(dork: str) -> str:
    return "https://www.google.com/search?q=" + urllib.parse.quote(dork)


def list_categories() -> list[dict[str, str]]:
    return [
        {"id": cid, "name": DORK_CATEGORIES[cid][0]}
        for cid in sorted(DORK_CATEGORIES, key=int)
    ]


def generate_dork_links(category_id: str, query: str) -> dict:
    if category_id not in DORKS:
        return {"error": "invalid_category", "available": list_categories()}
    links = []
    for template in DORKS[category_id]:
        dork = template.format(q=query)
        links.append({"dork": dork, "url": build_google_link(dork)})
    return {
        "category_id": category_id,
        "category": DORK_CATEGORIES[category_id][0],
        "query": query,
        "total": len(links),
        "links": links,
    }
