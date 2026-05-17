"""Извлечение email из коммитов GitHub-репозитория (API + .patch)."""

from __future__ import annotations

import re
from typing import Any

import requests

URL_PATTERN = re.compile(r"^https?://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/?$")
EMAIL_PATTERN = re.compile(r"From:\s+(.*?)\s+<(.*?)>")


def normalize_url(raw_url: str) -> str:
    url = raw_url.strip().rstrip("/")
    if not url.startswith("http"):
        url = "https://" + url
    return url


def extract_owner_repo(url: str) -> tuple[str, str] | None:
    match = URL_PATTERN.match(url)
    if match:
        return match.group(1), match.group(2)
    return None


def get_default_branch(owner: str, repo: str) -> str | None:
    api_url = f"https://api.github.com/repos/{owner}/{repo}"
    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            return response.json().get("default_branch")
        return None
    except requests.RequestException:
        return None


def get_commits(owner: str, repo: str, branch: str, per_page: int = 30) -> list[dict]:
    api_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    params = {"sha": branch, "per_page": per_page}
    try:
        response = requests.get(api_url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else []
    except requests.RequestException:
        return []


def extract_email_from_patch(repo_url: str, sha: str) -> dict | None:
    patch_url = f"{repo_url}/commit/{sha}.patch"
    try:
        response = requests.get(patch_url, timeout=15)
        response.raise_for_status()
        for line in response.text.splitlines():
            match = EMAIL_PATTERN.match(line)
            if match:
                return {
                    "sha": sha,
                    "name": match.group(1).strip(),
                    "email": match.group(2).strip(),
                    "patch_url": patch_url,
                }
    except requests.RequestException:
        pass
    return None


def search_github_repo(raw_url: str, *, commits_limit: int = 30) -> dict[str, Any]:
    repo_url = normalize_url(raw_url)
    owner_repo = extract_owner_repo(repo_url)
    if not owner_repo:
        return {
            "error": "invalid_url",
            "message": "Ожидается: https://github.com/owner/repo",
            "input": raw_url,
        }

    owner, repo = owner_repo
    branch = get_default_branch(owner, repo) or "main"
    commits = get_commits(owner, repo, branch, per_page=commits_limit)

    result: dict[str, Any] = {
        "repository": repo_url,
        "owner": owner,
        "repo": repo,
        "branch": branch,
        "commits_checked": len(commits),
        "email_found": False,
        "from_patch": None,
        "api_authors_sample": [],
    }

    if not commits:
        result["message"] = "Коммиты не получены (пустой репозиторий или лимит API)"
        return result

    for commit in commits:
        sha = commit.get("sha", "")
        if not sha:
            continue
        patch_hit = extract_email_from_patch(repo_url, sha)
        if patch_hit:
            result["email_found"] = True
            result["from_patch"] = patch_hit
            break

    if not result["email_found"]:
        result["message"] = "Email в .patch не найден (noreply, GPG или скрытый email)"
        for commit in commits[:5]:
            sha = (commit.get("sha") or "")[:8]
            author = commit.get("commit", {}).get("author", {})
            result["api_authors_sample"].append(
                {
                    "sha": sha,
                    "name": author.get("name"),
                    "email": author.get("email"),
                }
            )

    return result
