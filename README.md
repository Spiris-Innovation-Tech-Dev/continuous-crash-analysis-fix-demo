# Continuous Crash Analysis Fix Demo

This repository is a small, cloneable demo of a crash automation loop:

1. A synthetic signal generator pretends that something crashed.
2. The run writes `analysis-report.json` and `analysis-report.md`.
3. A GitHub issue is created from the fingerprinted report.
4. Running the same scenario again comments on the existing issue instead of opening a duplicate.
5. New issues can be assigned to GitHub Copilot using `copilot-swe-agent[bot]`.
6. A simplified `.github/workflows/claude-crashdump-root-cause.yml` reacts to the created issue.

The demo is intentionally synthetic. It is meant to showcase the orchestration around a crash, not real dump parsing.

## Repository Layout

- `.github/workflows/simulate-crash.yml` - manual end-to-end demo workflow
- `.github/workflows/claude-crashdump-root-cause.yml` - simplified issue-triggered Claude workflow
- `scripts/simulate_crash.py` - synthetic crash signal generator
- `scripts/upsert_issue.py` - create-or-comment GitHub issue automation
- `scripts/assign_copilot.py` - assign the issue to Copilot
- `src/demo_service.py` - tiny sample module the synthetic crash can point at
- `templates/copilot-custom-instructions.txt` - optional instructions sent with Copilot assignment

## GitHub Requirements

You need the following repository configuration before the workflows will behave end-to-end:

- Secret: `CRASH_DEMO_GH_TOKEN`
  - Use a fine-grained PAT or GitHub App token with write access to issues and pull requests.
  - Do not use `GITHUB_TOKEN` for issue creation here, because workflow-created issues will not trigger the follow-on `issues.opened` workflow.
- Secret: `CLAUDE_CODE_OAUTH_TOKEN`
  - Optional, only needed if you want the Claude workflow to invoke `anthropics/claude-code-action`.
- Variable: `CLAUDE_CRASHDUMP_ALLOWED_ISSUE_AUTHORS`
  - Comma-separated GitHub logins that are allowed to trigger the Claude job.
- GitHub Copilot coding agent enabled for this repository.

If your organization manages Copilot centrally, also make sure this repository is allowed for Copilot coding agent access.

## Running The Demo In GitHub Actions

1. Push this repository to GitHub.
2. Add the secrets and variable listed above.
3. Run the `Simulate Crash` workflow manually.
4. Open the created issue.
5. Run the same workflow again with the same inputs.

Expected behavior:

- First run: creates a new issue with labels `crash-dump`, `automated`, and `demo`.
- Second run with the same fingerprint: comments on the existing issue.
- New issues can be assigned to `copilot-swe-agent[bot]`.
- The simplified Claude workflow is triggered by `issues.opened`.

## Running Locally

Generate a synthetic report:

```bash
python3 scripts/simulate_crash.py --output-dir reports/generated/local
```

Preview the GitHub issue payload without calling the API:

```bash
python3 scripts/upsert_issue.py \
  --report-json reports/generated/local/analysis-report.json \
  --report-markdown reports/generated/local/analysis-report.md \
  --repository owner/repo \
  --dry-run
```

Preview the Copilot assignment payload:

```bash
python3 scripts/assign_copilot.py \
  --issue-number 123 \
  --repository owner/repo \
  --instructions-file templates/copilot-custom-instructions.txt \
  --dry-run
```

Run the included unit test:

```bash
python3 -m unittest discover
```

## Fingerprint Dedup

The demo fingerprint is stable for the same synthetic scenario. It is derived from:

- service name
- crash type
- faulting function
- exception code
- module name

That means two runs with the same crash inputs will land on the same issue, and `upsert_issue.py` will add a comment instead of creating a duplicate.
