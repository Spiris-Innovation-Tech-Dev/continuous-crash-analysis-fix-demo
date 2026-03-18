#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from github_common import build_workflow_run_url, write_github_output

CRASH_TYPES: dict[str, dict[str, Any]] = {
    "null-pointer": {
        "exception_code": "EXCEPTION_ACCESS_VIOLATION",
        "exception_code_raw": "0xC0000005",
        "exception_address": "0x0000000000000010",
        "access_type": "read",
        "accessed_address": "0x0000000000000000",
        "severity": "high",
        "summary": "Synthetic null pointer crash while loading a customer profile.",
        "recommended_actions": [
            "Inspect the synthetic crash frames in src/demo_service.py.",
            "Confirm the fingerprint stays stable across repeated runs.",
            "Customize the report fields to match your own incident format.",
        ],
        "frames": [
            "0 demo_service.load_customer_profile (src/demo_service.py:8)",
            "1 demo_service.build_account_overview (src/demo_service.py:19)",
            "2 main.synthetic_request_handler (scripts/simulate_crash.py:172)",
        ],
        "faulting_module": "demo_service.py",
    },
    "divide-by-zero": {
        "exception_code": "EXCEPTION_INT_DIVIDE_BY_ZERO",
        "exception_code_raw": "0xC0000094",
        "exception_address": "0x0000000000401180",
        "access_type": "execute",
        "accessed_address": "0x0000000000401180",
        "severity": "medium",
        "summary": "Synthetic divide-by-zero while calculating the discount ratio.",
        "recommended_actions": [
            "Review guard conditions around discount calculations.",
            "Decide whether this fingerprint should be environment-specific.",
            "Swap the synthetic stack frames for your own real call path.",
        ],
        "frames": [
            "0 pricing.calculate_discount_ratio (src/demo_service.py:25)",
            "1 pricing.build_invoice_preview (src/demo_service.py:31)",
            "2 main.synthetic_request_handler (scripts/simulate_crash.py:172)",
        ],
        "faulting_module": "demo_service.py",
    },
    "assert-failure": {
        "exception_code": "EXCEPTION_BREAKPOINT",
        "exception_code_raw": "0x80000003",
        "exception_address": "0x0000000000401000",
        "access_type": "execute",
        "accessed_address": "0x0000000000401000",
        "severity": "medium",
        "summary": "Synthetic assertion failure used to exercise the automation path.",
        "recommended_actions": [
            "Replace the synthetic assertion with your real fail-fast metadata.",
            "Keep the fingerprint builder stable for repeated incidents.",
            "Tune labels and issue body sections for your team.",
        ],
        "frames": [
            "0 demo_service.synthetic_fail_fast (src/demo_service.py:37)",
            "1 main.synthetic_request_handler (scripts/simulate_crash.py:172)",
        ],
        "faulting_module": "demo_service.py",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a synthetic crash report.")
    parser.add_argument("--service", default="demo-service")
    parser.add_argument("--environment", default="demo")
    parser.add_argument(
        "--crash-type",
        choices=sorted(CRASH_TYPES.keys()),
        default="null-pointer",
    )
    parser.add_argument("--faulting-function", default="load_customer_profile")
    parser.add_argument("--output-dir", default="reports/generated/latest")
    parser.add_argument("--github-output")
    return parser.parse_args()


def build_fingerprint(
    service: str,
    crash_type: str,
    faulting_function: str,
    exception_code: str,
    faulting_module: str,
) -> str:
    fingerprint_source = "\n".join(
        [
            service.strip().lower(),
            crash_type.strip().lower(),
            faulting_function.strip().lower(),
            exception_code.strip().lower(),
            faulting_module.strip().lower(),
        ]
    )
    return hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()[:12]


def build_markdown_report(report: dict[str, Any]) -> str:
    crash_info = report["metadata"]["crash_info"]
    exception = report["dump_analysis"]["exception"]
    triage = report["triage"]
    demo = report["demo"]
    frames = report["dump_analysis"]["stack_traces"]["crashing_thread"]["frames"]

    lines = [
        "# Synthetic Crash Report",
        "",
        "## Crash Summary",
        "",
        f"- Generated (UTC): {report['generated_at_utc']}",
        f"- Service: {crash_info['service_name']}",
        f"- Environment: {crash_info['environment']}",
        f"- Fingerprint: `{triage['fingerprint']}`",
        f"- Severity: {triage['severity']}",
        f"- Exception: {exception['exception_code']} ({exception['exception_code_raw']})",
        f"- Address: {exception['exception_address']}",
        f"- Faulting function: {demo['faulting_function']}",
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

    lines.extend(["", "## Stack Trace", "", "```text"])
    lines.extend(frames)
    lines.extend(
        [
            "```",
            "",
            "## Demo Note",
            "",
            "This report is synthetic and exists to demonstrate issue creation,",
            "fingerprint deduplication, Copilot assignment, and issue-triggered workflows.",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    crash_type = CRASH_TYPES[args.crash_type]
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fingerprint = build_fingerprint(
        args.service,
        args.crash_type,
        args.faulting_function,
        crash_type["exception_code"],
        crash_type["faulting_module"],
    )

    report = {
        "generated_at_utc": generated_at,
        "metadata": {
            "crash_info": {
                "service_name": args.service,
                "environment": args.environment,
                "version": "1.0.0-demo",
                "signal_kind": "synthetic-crash",
            }
        },
        "crash_package": {
            "prefix": f"synthetic/{args.environment}/{args.service}/{fingerprint}"
        },
        "triage": {
            "fingerprint": fingerprint,
            "severity": crash_type["severity"],
            "summary": crash_type["summary"],
            "recommended_actions": crash_type["recommended_actions"],
        },
        "dump_analysis": {
            "stack_trace_source": "synthetic-demo",
            "exception": {
                "exception_code": crash_type["exception_code"],
                "exception_code_raw": crash_type["exception_code_raw"],
                "exception_address": crash_type["exception_address"],
                "module_at_exception": crash_type["faulting_module"],
                "exception_information": {
                    "access_type": crash_type["access_type"],
                    "accessed_address": crash_type["accessed_address"],
                    "is_probable_null_pointer": args.crash_type == "null-pointer",
                },
            },
            "stack_traces": {
                "crashing_thread": {
                    "frames": crash_type["frames"],
                }
            },
        },
        "demo": {
            "crash_type": args.crash_type,
            "faulting_function": args.faulting_function,
            "source_file": "src/demo_service.py",
            "source_line_hint": 8,
            "workflow_run_url": build_workflow_run_url(),
        },
    }

    report_json_path = output_dir / "analysis-report.json"
    report_md_path = output_dir / "analysis-report.md"
    report_markdown = build_markdown_report(report)

    report_json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    report_md_path.write_text(report_markdown, encoding="utf-8")

    print("Something crashed, and we're now collecting crash information and creating a ticket in GitHub.")
    print(f"Synthetic crash type: {args.crash_type}")
    print(f"Fingerprint: {fingerprint}")
    print(f"JSON report: {report_json_path}")
    print(f"Markdown report: {report_md_path}")

    write_github_output(
        args.github_output,
        {
            "fingerprint": fingerprint,
            "report_json": report_json_path.as_posix(),
            "report_markdown": report_md_path.as_posix(),
            "crash_type": args.crash_type,
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
