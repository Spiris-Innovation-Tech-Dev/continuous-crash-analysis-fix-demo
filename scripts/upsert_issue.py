#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from github_common import (
    GitHubRequestError,
    build_workflow_run_url,
    github_request,
    parse_csv_items,
    resolve_token,
    write_github_output,
)

DEFAULT_TITLE_PREFIX = "[CrashDump]"
DEFAULT_LABELS = "crash-dump,automated,demo"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create or comment on a fingerprinted GitHub issue.")
    parser.add_argument("--report-json", required=True)
    parser.add_argument("--report-markdown")
    parser.add_argument("--repository", required=False)
    parser.add_argument("--issue-title-prefix", default=DEFAULT_TITLE_PREFIX)
    parser.add_argument("--issue-labels", default=DEFAULT_LABELS)
    parser.add_argument("--api-url", default="https://api.github.com")
    parser.add_argument("--github-output")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def build_issue_title(report: dict[str, Any], title_prefix: str) -> str:
    crash_info = report["metadata"]["crash_info"]
    exception = report["dump_analysis"]["exception"]
    fingerprint = report["triage"]["fingerprint"]
    prefix = title_prefix.strip() or DEFAULT_TITLE_PREFIX
    return (
        f"{prefix}[{crash_info['environment']}][{fingerprint}] "
        f"{crash_info['service_name']} {exception['exception_code']}"
    )


def build_issue_body(report: dict[str, Any], markdown_report: str) -> str:
    crash_info = report["metadata"]["crash_info"]
    exception = report["dump_analysis"]["exception"]
    triage = report["triage"]
    demo = report["demo"]
    frames = report["dump_analysis"]["stack_traces"]["crashing_thread"]["frames"]
    workflow_run_url = demo.get("workflow_run_url") or build_workflow_run_url()

    lines = [
        "## Crash Summary",
        "",
        f"- Generated (UTC): {report['generated_at_utc']}",
        f"- Service: {crash_info['service_name']}",
        f"- Environment: {crash_info['environment']}",
        f"- Fingerprint: `{triage['fingerprint']}`",
        f"- Severity: {triage['severity']}",
        f"- Exception: {exception['exception_code']} ({exception['exception_code_raw']})",
        f"- Address: {exception['exception_address']}",
        f"- Faulting function: `{demo['faulting_function']}`",
        f"- Suggested source: `{demo['source_file']}`",
        "",
        "## Triage Summary",
        "",
        triage["summary"],
        "",
        "## Recommended Actions",
        "",
    ]

    for action in triage["recommended_actions"]:
        lines.append(f"- {action}")

    lines.extend(["", "## Stack Trace (Synthetic)", "", "```text"])
    lines.extend(frames)
    lines.append("```")

    if workflow_run_url:
        lines.extend(["", "## Workflow", "", f"- Source run: {workflow_run_url}"])

    lines.extend(
        [
            "",
            "## Demo Note",
            "",
            "This issue was created by a synthetic crash signal.",
            "Running the same fingerprint again should comment on this issue instead of opening a duplicate.",
            "",
            "<details><summary>Full Markdown Report</summary>",
            "",
            "```markdown",
            markdown_report.strip(),
            "```",
            "",
            "</details>",
        ]
    )
    return "\n".join(lines)


def build_comment_body(report: dict[str, Any]) -> str:
    workflow_run_url = report["demo"].get("workflow_run_url") or build_workflow_run_url()
    triage = report["triage"]
    exception = report["dump_analysis"]["exception"]
    lines = [
        "New crash occurrence detected for the existing fingerprint.",
        "",
        f"- Generated (UTC): {report['generated_at_utc']}",
        f"- Fingerprint: `{triage['fingerprint']}`",
        f"- Severity: {triage['severity']}",
        f"- Exception: {exception['exception_code']} ({exception['exception_code_raw']})",
    ]
    if workflow_run_url:
        lines.append(f"- Source run: {workflow_run_url}")
    lines.extend(
        [
            "",
            "The fingerprint already exists, so this run commented on the existing issue instead of creating a new one.",
        ]
    )
    return "\n".join(lines)


def find_existing_issue(
    *,
    repository: str,
    token: str,
    fingerprint: str,
    api_url: str,
) -> dict[str, Any] | None:
    for page in range(1, 4):
        issues = github_request(
            "GET",
            f"/repos/{repository}/issues",
            token,
            api_url=api_url,
            params={"state": "open", "per_page": 100, "page": page},
        )
        if not isinstance(issues, list) or not issues:
            return None

        fingerprint_marker = f"[{fingerprint}]".lower()
        for issue in issues:
            if "pull_request" in issue:
                continue
            title = str(issue.get("title", "")).lower()
            if fingerprint_marker in title:
                return issue
    return None


def main() -> int:
    args = parse_args()
    repository = args.repository or Path.cwd().name
    report_path = Path(args.report_json)
    markdown_path = Path(args.report_markdown or report_path.with_name("analysis-report.md"))

    report = json.loads(report_path.read_text(encoding="utf-8"))
    markdown_report = markdown_path.read_text(encoding="utf-8") if markdown_path.exists() else ""
    issue_title = build_issue_title(report, args.issue_title_prefix)
    issue_body = build_issue_body(report, markdown_report)
    fingerprint = report["triage"]["fingerprint"]
    labels = parse_csv_items(args.issue_labels)

    if args.dry_run:
        print(f"[dry-run] would upsert issue in {repository}")
        print(f"[dry-run] title: {issue_title}")
        print(f"[dry-run] labels: {', '.join(labels)}")
        write_github_output(
            args.github_output,
            {
                "issue_action": "dry-run",
                "issue_created": "false",
                "issue_number": "",
                "issue_url": "",
                "fingerprint": fingerprint,
            },
        )
        return 0

    token = resolve_token()
    existing_issue = find_existing_issue(
        repository=repository,
        token=token,
        fingerprint=fingerprint,
        api_url=args.api_url,
    )

    if existing_issue:
        issue_number = int(existing_issue["number"])
        github_request(
            "POST",
            f"/repos/{repository}/issues/{issue_number}/comments",
            token,
            api_url=args.api_url,
            payload={"body": build_comment_body(report)},
        )
        issue_url = str(existing_issue.get("html_url", ""))
        print(f"Commented on existing issue #{issue_number}: {issue_url}")
        write_github_output(
            args.github_output,
            {
                "issue_action": "commented",
                "issue_created": "false",
                "issue_number": issue_number,
                "issue_url": issue_url,
                "fingerprint": fingerprint,
            },
        )
        return 0

    created_issue = github_request(
        "POST",
        f"/repos/{repository}/issues",
        token,
        api_url=args.api_url,
        payload={"title": issue_title, "body": issue_body, "labels": labels},
    )
    issue_number = int(created_issue["number"])
    issue_url = str(created_issue.get("html_url", ""))
    print(f"Created issue #{issue_number}: {issue_url}")
    write_github_output(
        args.github_output,
        {
            "issue_action": "created",
            "issue_created": "true",
            "issue_number": issue_number,
            "issue_url": issue_url,
            "fingerprint": fingerprint,
        },
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GitHubRequestError as exc:
        print(str(exc))
        raise SystemExit(1)
