#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

from github_common import (
    COPILOT_SWE_AGENT_LOGIN_BOT,
    GitHubRequestError,
    github_request,
    resolve_token,
    write_github_output,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assign a GitHub issue to Copilot coding agent.")
    parser.add_argument("--issue-number", required=True, type=int)
    parser.add_argument("--repository", required=False)
    parser.add_argument("--api-url", default="https://api.github.com")
    parser.add_argument("--base-branch", default="main")
    parser.add_argument("--target-repo")
    parser.add_argument("--instructions-file")
    parser.add_argument("--instructions")
    parser.add_argument("--github-output")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def read_instructions(args: argparse.Namespace) -> str:
    if args.instructions:
        return args.instructions.strip()
    if args.instructions_file:
        return Path(args.instructions_file).read_text(encoding="utf-8").strip()
    return ""


def main() -> int:
    args = parse_args()
    repository = args.repository or Path.cwd().name
    target_repo = args.target_repo or repository
    instructions = read_instructions(args)
    payload = {
        "assignees": [COPILOT_SWE_AGENT_LOGIN_BOT],
        "agent_assignment": {
            "target_repo": target_repo,
            "base_branch": args.base_branch,
            "custom_instructions": instructions,
        },
    }

    if args.dry_run:
        print("[dry-run] would assign Copilot with payload:")
        print(json.dumps(payload, indent=2))
        write_github_output(
            args.github_output,
            {"copilot_status": "dry-run", "copilot_mode": "agent-assignment"},
        )
        return 0

    token = resolve_token()
    try:
        github_request(
            "POST",
            f"/repos/{repository}/issues/{args.issue_number}/assignees",
            token,
            api_url=args.api_url,
            payload=payload,
        )
        status = "assigned"
        mode = "agent-assignment"
    except GitHubRequestError as exc:
        fallback_payload = {"assignees": [COPILOT_SWE_AGENT_LOGIN_BOT]}
        if "agent_assignment" not in str(exc):
            raise
        github_request(
            "POST",
            f"/repos/{repository}/issues/{args.issue_number}/assignees",
            token,
            api_url=args.api_url,
            payload=fallback_payload,
        )
        status = "assigned"
        mode = "assignee-only-fallback"

    print(
        f"Assigned issue #{args.issue_number} in {repository} to {COPILOT_SWE_AGENT_LOGIN_BOT} ({mode})."
    )
    write_github_output(
        args.github_output,
        {"copilot_status": status, "copilot_mode": mode},
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GitHubRequestError as exc:
        print(str(exc))
        raise SystemExit(1)
