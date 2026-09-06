# Contributing

## Setting up

```bash
git clone https://github.com/IGORSVOLOHOVS/repo-quality-template
cd repo-quality-template
python scripts/install_dependencies.py --dev
pre-commit install
```

`pre-commit install` is not optional — it is what keeps formatting and secret
scanning out of code review.

## Every change starts as an issue

Not because the tracker needs feeding, but because the issue is where the
acceptance criteria are written down. A change whose "done" was never written
down is a change the reviewer has to define on the spot, from the diff, weeks
later.

Pick a form in [Issues](https://github.com/IGORSVOLOHOVS/repo-quality-template/issues/new/choose):
bug report, feature request or task. All three ask for acceptance criteria. The
blank issue is switched off.

Then the branch carries the issue number:

```bash
git switch dev && git pull
git switch -c rqt-12/feat/sbom-in-release
```

The full path from issue to release is [`docs/workflow.md`](docs/workflow.md).

## The loop

```bash
python scripts/check_before_push.py      # everything CI runs, in one command
```

Or piece by piece:

```bash
pytest                                   # tests, with coverage
ruff check . && ruff format .            # lint and format
mypy                                     # strict types over src/
pytest benchmarks --benchmark-only       # only if you touched the domain layer
python scripts/collect_quality_metrics.py
```

CI runs all of these. Running them locally first is faster than waiting for a
red build.

## Rules that the build enforces

| Rule | Enforced by |
| --- | --- |
| Coverage at or above 85 percent | `fail_under` in `pyproject.toml` |
| Cyclomatic complexity at most 10 per function | `ruff` rule `C90` |
| Strict types over `src/` | `mypy` |
| No credential in any commit | `gitleaks`, in pre-commit and CI |
| Three long-lived branches, no strays | `scripts/enforce_branch_policy.py` |
| Branch name, commit format, sign-off, issue link | `scripts/enforce_contribution_policy.py` |
| Formatting | `ruff format` |

## Branches

Three long-lived branches: `release`, `dev`, `test`. Work happens on a
short-lived branch named `<code>-<issue>/<type>/<slug>`, proposed into `dev` by
pull request, and deleted when it merges. Anything else fails
`branch-policy.yml`. See [`docs/branching.md`](docs/branching.md).

## Commits

`<type>(<scope>): <subject>`, signed off. `git commit -s` writes the trailer,
and the pull request fails without it.

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `build`, `ci`,
`chore`, `security`. Scopes: `core`, `cli`, `app`, `ci`, `docs`, `scripts`,
`benchmarks`, `release`. Both lists live in `[tool.repo-quality]` in
`pyproject.toml`, in one place.

Write what changed and why, in English. A commit message that only says what the
diff already shows is not worth reading.

## Opening the pull request

```bash
gh pr create --base dev --fill
```

The body must say `Closes #12`. The template asks for four things: what
changed, why this way, how you verified it, and the issue's acceptance criteria
ticked off. `CODEOWNERS` requests the reviewer; nothing merges itself.

## Adding a feature

1. Put the logic in `core.py`, with no I/O.
2. Add tests for it, including the empty and invalid cases.
3. If it could be slow, add a benchmark.
4. Update the README if the behaviour is user-visible.
5. Add a `CHANGELOG.md` entry under `[Unreleased]`.
6. Tick the acceptance criteria on the issue in the pull request body.

Step 1 matters: logic that reaches into `cli.py` or `app.py` cannot be reused by
the other shell and is much harder to test.
