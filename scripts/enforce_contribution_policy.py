"""The shape of a contribution: branch name, commit messages, and the issue.

    python scripts/enforce_contribution_policy.py                 # this branch
    python scripts/enforce_contribution_policy.py --base dev
    python scripts/enforce_contribution_policy.py --pr-body-file body.txt

Three rules, all of them mechanical, all of them checked here so that a
reviewer never spends a comment on them:

1. A work branch is named ``<code>-<issue>/<type>/<slug>``. The issue number is
   in the branch, so every later question - why does this code exist, what was
   it meant to fix - has an answer one command away.
2. Every commit subject is ``<type>(<scope>): <subject>`` and carries a
   ``Signed-off-by`` line. ``git commit -s`` writes the sign-off.
3. A pull request closes an issue. Work that arrived without one is work whose
   acceptance criteria were never written down.

The vocabulary lives in ``pyproject.toml`` under ``[tool.repo-quality]``, in
one place, so the branch checker, the commit checker and the templates cannot
drift apart.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - CI runs this job on 3.12
    raise SystemExit("this check needs Python 3.11 or newer for tomllib")

ROOT = Path(__file__).resolve().parent.parent

SUBJECT_MAX = 72


def load_settings() -> dict[str, object]:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        document = tomllib.load(handle)
    settings = document.get("tool", {}).get("repo-quality", {})
    if not settings:
        raise SystemExit("pyproject.toml has no [tool.repo-quality] section")
    return dict(settings)


def git(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if proc.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {proc.stderr.strip()[:200]}")
    return proc.stdout


def current_branch() -> str:
    """The branch under review.

    In a pull request GitHub checks out a detached merge commit, so the branch
    name has to come from the event rather than from HEAD.
    """
    for variable in ("GITHUB_HEAD_REF", "GITHUB_REF_NAME"):
        value = os.environ.get(variable, "").strip()
        if value:
            return value
    return git("rev-parse", "--abbrev-ref", "HEAD").strip()


def commits_under_review(base: str) -> list[str]:
    """Commit hashes on this branch that are not already on `base`."""
    for reference in (f"origin/{base}", base):
        proc = subprocess.run(
            ["git", "rev-list", "--no-merges", f"{reference}..HEAD"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode == 0:
            return [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    return []


def check_branch_name(branch: str, settings: dict[str, object]) -> list[str]:
    long_lived = [str(b) for b in settings.get("long_lived_branches", [])]
    if branch in long_lived:
        return []

    code = str(settings.get("code", ""))
    types = "|".join(str(t) for t in settings.get("branch_types", []))
    pattern = re.compile(rf"^{re.escape(code)}-\d+/({types})/[a-z0-9][a-z0-9-]*$")

    if pattern.match(branch):
        return []
    return [
        f"branch name {branch!r} does not match <code>-<issue>/<type>/<slug>\n"
        f"    expected something like {code}-12/feat/coverage-gate\n"
        f"    types: {types.replace('|', ', ')}"
    ]


def check_commit(commit: str, settings: dict[str, object]) -> list[str]:
    subject = git("log", "-1", "--format=%s", commit).strip()
    body = git("log", "-1", "--format=%B", commit)
    problems: list[str] = []

    types = "|".join(str(t) for t in settings.get("commit_types", []))
    scopes = [str(s) for s in settings.get("commit_scopes", [])]
    scope_pattern = "|".join(re.escape(s) for s in scopes) if scopes else "[a-z0-9-]+"
    pattern = re.compile(rf"^({types})(\(({scope_pattern})\))?: .+$")

    if not pattern.match(subject):
        problems.append(f"{commit[:8]} subject is not <type>(<scope>): <subject>\n    {subject}")
    elif len(subject) > SUBJECT_MAX:
        problems.append(f"{commit[:8]} subject is {len(subject)} characters, over {SUBJECT_MAX}")
    elif subject.rstrip().endswith("."):
        problems.append(f"{commit[:8]} subject ends with a full stop")

    if "Signed-off-by:" not in body:
        problems.append(f"{commit[:8]} has no Signed-off-by line - use git commit -s")

    return problems


def check_pull_request_body(text: str) -> list[str]:
    """A pull request has to close an issue, and say so where GitHub reads it."""
    if re.search(r"\b(closes|fixes|resolves)\s+#\d+", text, re.IGNORECASE):
        return []
    return [
        "the pull request body does not close an issue\n"
        "    add a line like 'Closes #12' so merging shuts the issue"
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", default="dev", help="branch this work is proposed into")
    parser.add_argument("--branch", help="override the branch name to check")
    parser.add_argument("--pr-body-file", help="file holding the pull request body")
    parser.add_argument("--skip-commits", action="store_true", help="check only the branch name")
    args = parser.parse_args()

    settings = load_settings()
    branch = args.branch or current_branch()
    problems: list[str] = []

    print(f"branch: {branch}")
    problems += check_branch_name(branch, settings)

    if not args.skip_commits:
        commits = commits_under_review(args.base)
        if commits:
            print(f"commits not yet on {args.base}: {len(commits)}")
            for commit in commits:
                problems += check_commit(commit, settings)
        else:
            print(f"no commits ahead of {args.base}")

    if args.pr_body_file:
        body = Path(args.pr_body_file).read_text(encoding="utf-8", errors="replace")
        problems += check_pull_request_body(body)

    if problems:
        print("\ncontribution policy NOT satisfied:")
        for problem in problems:
            print(f"  - {problem}")
        print("\nsee docs/workflow.md")
        return 1

    print("\ncontribution policy satisfied")
    return 0


if __name__ == "__main__":
    sys.exit(main())
