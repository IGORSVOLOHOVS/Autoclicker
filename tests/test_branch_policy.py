"""How a branch name is classified.

Point 14 is the rule that has been wrong twice: first "never a fourth branch",
which forbade pull requests, and then a version that rejected every branch
Dependabot opened. Both times the rule was only exercised by running it against
a real repository, which is a slow way to find out.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# The script reads pyproject.toml with tomllib, which arrived in 3.11. The
# project supports 3.10 and the test matrix covers it, but every workflow that
# runs this script pins 3.12 - so the right answer is to skip the module rather
# than to add a backport dependency for a path that never executes.
if sys.version_info < (3, 11):  # pragma: no cover - only on the 3.10 leg
    pytest.skip(
        "enforce_branch_policy.py needs tomllib (3.11+); its workflows run 3.12",
        allow_module_level=True,
    )


def load_policy():
    """Import the script by path; scripts/ is not a package."""
    spec = importlib.util.spec_from_file_location(
        "enforce_branch_policy", ROOT / "scripts" / "enforce_branch_policy.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


policy = load_policy()
PATTERN = policy.work_branch_pattern()
BOTS = policy.bot_branch_prefixes()


@pytest.mark.parametrize("branch", ["release", "dev", "test"])
def test_the_three_long_lived_branches(branch: str) -> None:
    assert policy.classify(branch, PATTERN, BOTS) == "long-lived"


@pytest.mark.parametrize(
    "branch",
    [
        "acl-1/feat/issue-and-pull-request-discipline",
        "acl-12/fix/a",
        "acl-9999/security/token-permissions",
        "acl-3/docs/where-the-standard-came-from",
    ],
)
def test_a_work_branch_carries_an_issue_number(branch: str) -> None:
    assert policy.classify(branch, PATTERN, BOTS) == "work"


@pytest.mark.parametrize(
    "branch",
    [
        "dependabot/pip/ruff-gte-0.16.5",
        "dependabot/github_actions/actions/checkout-7",
        "renovate/npm-lodash-4.x",
    ],
)
def test_a_bot_branch_is_allowed_without_an_issue(branch: str) -> None:
    """Dependabot cannot open an issue first, and point 21 asks for it anyway.

    Before this existed, switching Dependabot on turned every pull request in
    the repository red, including ones that had nothing to do with it.
    """
    assert policy.classify(branch, PATTERN, BOTS) == "bot"


@pytest.mark.parametrize(
    "branch",
    [
        "main",
        "master",
        "feature/whatever",
        "rqt/feat/no-issue-number",  # no number
        "acl-12/invented/slug",  # not a known type
        "acl-12/feat/Has-Capitals",
        "acl-12/feat/",  # empty slug
        "wrongcode-12/feat/slug",
        "dependabot",  # the prefix is a directory, not a whole name
    ],
)
def test_everything_else_is_a_stray(branch: str) -> None:
    assert policy.classify(branch, PATTERN, BOTS) == "stray"


def test_the_vocabulary_comes_from_pyproject() -> None:
    """The grammar is configuration, not a literal in the script."""
    configuration = policy.settings()
    assert configuration["code"] == "acl"
    assert "feat" in configuration["branch_types"]
    assert "dependabot/" in configuration["bot_branch_prefixes"]


def test_a_project_with_no_bot_prefixes_rejects_bot_branches() -> None:
    """The allowance is opt-in: a repository that has not switched a bot on
    should not silently accept a branch pretending to be one."""
    assert policy.classify("dependabot/pip/ruff", PATTERN, ()) == "stray"
