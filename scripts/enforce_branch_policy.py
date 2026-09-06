"""Point 14: three long-lived branches - release, dev, test - and nothing that
outlives a pull request.

    python scripts/enforce_branch_policy.py                 # report
    python scripts/enforce_branch_policy.py --remote origin # check the remote too
    python scripts/enforce_branch_policy.py --delete-extra  # actually remove them

The rule used to be "three branches, never a fourth", which made a pull request
impossible: a pull request needs a branch on the remote to point at. So a
fourth kind of branch is allowed - a work branch named
``<code>-<issue>/<type>/<slug>``, carrying an issue number, deleted when its
pull request merges. The grammar comes from ``[tool.repo-quality]`` in
pyproject.toml, the same place the commit checker reads.

There is a fifth: branches a bot opened. Dependabot cannot open an issue first
and cannot name its branch after one, so point 21 - something must watch the
dependencies - and point 14 contradicted each other until this existed. The
prefixes are configured, not hard-coded, because Renovate names its branches
differently.

What is still forbidden is the thing the rule was written against: a long-lived
branch with a name nobody can parse, holding work that is not in `dev` and will
be forgotten. A work branch whose tip is already merged is reported as stale,
because it has become exactly that.

Reporting is the default and deleting is opt-in on purpose: a stray branch is
often the only copy of something. --delete-extra refuses to touch a branch whose
tip is not already contained in release, dev or test, so nothing unique is lost
without being named first.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ALLOWED = ("release", "dev", "test")


def settings() -> dict[str, object]:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        return dict(tomllib.load(handle).get("tool", {}).get("repo-quality", {}))


def work_branch_pattern() -> re.Pattern[str]:
    """The grammar a short-lived branch has to match, from pyproject.toml."""
    configuration = settings()
    code = re.escape(str(configuration.get("code", "")))
    types = "|".join(re.escape(str(t)) for t in configuration.get("branch_types", []))
    return re.compile(rf"^{code}-\d+/({types})/[a-z0-9][a-z0-9-]*$")


def bot_branch_prefixes() -> tuple[str, ...]:
    """Prefixes a bot is allowed to use, from pyproject.toml.

    Dependabot cannot open an issue first and cannot name its branch after one,
    so the rule that every branch carries an issue number would reject every
    dependency update - and with it every other pull request open at the time,
    because the check runs on all of them.
    """
    return tuple(str(p) for p in settings().get("bot_branch_prefixes", []))


def classify(branch: str, pattern: re.Pattern[str], bots: tuple[str, ...] = ()) -> str:
    """One of: long-lived, work, bot, stray."""
    if branch in ALLOWED:
        return "long-lived"
    if pattern.match(branch):
        return "work"
    if any(branch.startswith(prefix) for prefix in bots):
        return "bot"
    return "stray"


def git(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if proc.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {proc.stderr.strip()[:200]}")
    return proc.stdout


def local_branches() -> list[str]:
    return [
        b.strip()
        for b in git("for-each-ref", "--format=%(refname:short)", "refs/heads").splitlines()
        if b.strip()
    ]


def remote_branches(remote: str) -> list[str]:
    out = git("ls-remote", "--heads", remote)
    return [
        line.split("refs/heads/", 1)[1].strip()
        for line in out.splitlines()
        if "refs/heads/" in line
    ]


def is_merged_into_allowed(branch: str, existing: set[str]) -> bool:
    """True when this branch's tip is already an ancestor of an allowed branch."""
    for target in ALLOWED:
        if target not in existing or target == branch:
            continue
        proc = subprocess.run(
            ["git", "merge-base", "--is-ancestor", branch, target], capture_output=True
        )
        if proc.returncode == 0:
            return True
    return False


def report(
    kind: str, branches: list[str], pattern: re.Pattern[str], bots: tuple[str, ...] = ()
) -> tuple[list[str], list[str]]:
    """Print one section and hand back its stray and work branches."""
    stray: list[str] = []
    work: list[str] = []
    print(f"{kind}:" if branches else f"{kind}: none")
    for branch in sorted(branches):
        label = classify(branch, pattern, bots)
        print(f"  {label:<10} {branch}")
        if label == "stray":
            stray.append(branch)
        elif label == "work":
            work.append(branch)
    return stray, work


def delete_merged(branches: list[str], existing: set[str]) -> None:
    """Delete the branches whose tip is already inside a long-lived branch."""
    if branches:
        print("\ndeleting extra local branches:")
    for branch in branches:
        if is_merged_into_allowed(branch, existing):
            git("branch", "-d", branch)
            print(f"  deleted {branch} (already merged)")
        else:
            print(
                f"  KEPT {branch} - has commits not present in release/dev/test; "
                f"merge or export it first"
            )


def explain_failure(stray: list[str], missing: list[str]) -> None:
    print("\nbranch policy NOT satisfied")
    for branch in stray:
        print(
            f"  {branch} is neither long-lived, nor <code>-<issue>/<type>/<slug>, "
            f"nor opened by a bot"
        )
    if missing:
        print(f"  missing: {', '.join(missing)}")
    print("  see docs/branching.md")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--remote", help="also check this remote, e.g. origin")
    parser.add_argument(
        "--delete-extra", action="store_true", help="delete extra branches that are fully merged"
    )
    args = parser.parse_args()

    pattern = work_branch_pattern()
    bots = bot_branch_prefixes()
    local = local_branches()

    # A CI checkout creates exactly one local branch, so "these three exist" can
    # only be judged against the remote. When --remote is given it is the
    # authority for what exists; the local list is then informational.
    remote = remote_branches(args.remote) if args.remote else []
    authoritative = remote if args.remote else local
    missing = [b for b in ALLOWED if b not in authoritative]

    stray_local, work_local = report("local branches", local, pattern, bots)
    stray_remote: list[str] = []
    if args.remote:
        print()
        stray_remote, _ = report(f"{args.remote} branches", remote, pattern, bots)

    if missing:
        where = args.remote if args.remote else "locally"
        print(f"\nmissing required branches on {where}: {', '.join(missing)}")

    # A work branch that is already merged has become the thing the rule exists
    # to prevent, so it is named - but it is not a build failure, because
    # deleting it is the sweep's job and not this check's.
    existing = set(local)
    stale = [b for b in work_local if is_merged_into_allowed(b, existing)]
    if stale:
        print("\nwork branches already merged, safe to delete:")
        for branch in stale:
            print(f"  {branch}")

    if args.delete_extra:
        delete_merged(stray_local + work_local, existing)

    if stray_local or stray_remote or missing:
        explain_failure(stray_local + stray_remote, missing)
        return 1

    print(
        "\nbranch policy satisfied: release, dev, test, work branches with an "
        "issue number, and branches a bot opened"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
