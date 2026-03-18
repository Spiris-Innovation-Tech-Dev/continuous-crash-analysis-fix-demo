#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

DEFAULT_GITHUB_API_URL = "https://api.github.com"
COPILOT_SWE_AGENT_LOGIN_BOT = "copilot-swe-agent[bot]"


class GitHubRequestError(RuntimeError):
    pass


def parse_csv_items(text: str) -> list[str]:
    return [item.strip() for item in text.split(",") if item.strip()]


def unique_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def resolve_token(explicit_token: str | None = None) -> str:
    token = explicit_token or os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        raise GitHubRequestError("Missing GitHub token. Set GH_TOKEN or GITHUB_TOKEN.")
    return token


def build_workflow_run_url() -> str | None:
    server_url = os.getenv("GITHUB_SERVER_URL")
    repository = os.getenv("GITHUB_REPOSITORY")
    run_id = os.getenv("GITHUB_RUN_ID")
    if not server_url or not repository or not run_id:
        return None
    return f"{server_url}/{repository}/actions/runs/{run_id}"


def write_github_output(path: str | None, values: dict[str, Any]) -> None:
    if not path:
        return

    with open(path, "a", encoding="utf-8") as handle:
        for key, value in values.items():
            text = str(value)
            if "\n" in text:
                delimiter = f"EOF_{key.upper()}"
                handle.write(f"{key}<<{delimiter}\n{text}\n{delimiter}\n")
            else:
                handle.write(f"{key}={text}\n")


def github_request(
    method: str,
    path: str,
    token: str,
    *,
    api_url: str | None = None,
    payload: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> Any:
    base_url = (api_url or DEFAULT_GITHUB_API_URL).rstrip("/")
    url = f"{base_url}{path}"
    if params:
        query = urllib.parse.urlencode(params)
        url = f"{url}?{query}"

    data = None
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "continuous-crash-analysis-fix-demo",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method=method.upper())

    try:
        with urllib.request.urlopen(request) as response:
            body = response.read().decode("utf-8")
            if not body:
                return None
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise GitHubRequestError(
            f"{method.upper()} {path} failed with HTTP {exc.code}: {error_body}"
        ) from exc
    except urllib.error.URLError as exc:
        raise GitHubRequestError(f"{method.upper()} {path} failed: {exc.reason}") from exc
