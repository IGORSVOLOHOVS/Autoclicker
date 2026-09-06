# How a change travels

Issue, branch, commits, pull request, merge, release. Six steps, and the first
one is not optional.

```
issue #12 ──► rqt-12/feat/slug ──► commits ──► pull request ──► dev ──► test ──► release ──► tag
     │                                              │
     └────────── acceptance criteria ───────────────┘
```

## 1. An issue, before any code

Every change starts as an issue. Not because the tracker needs feeding, but
because the issue is where the acceptance criteria are written down — and a
change whose "done" was never written down is a change the reviewer has to
define on the spot, weeks later, from the diff.

Three forms, in `.github/ISSUE_TEMPLATE/`:

| form | for |
| --- | --- |
| Bug report | behaviour that differs from what the documentation says |
| Feature request | something the project should be able to do and cannot |
| Task | docs, CI, refactoring, chores |

All three require acceptance criteria. The blank issue is switched off.

A security hole is not an issue — see [`SECURITY.md`](../SECURITY.md).

## 2. A branch named after the issue

```
<code>-<issue>/<type>/<slug>
rqt-12/feat/sbom-in-release
```

`code` and the type vocabulary live in `[tool.repo-quality]` in
`pyproject.toml`, written once, read by both policy scripts and quoted by the
templates.

The issue number is in the branch name so that every later question — why does
this code exist, what was it meant to fix — is one `git log` away from its
answer.

```bash
git switch dev && git pull
git switch -c rqt-12/feat/sbom-in-release
```

## 3. Commits that say what changed

```
<type>(<scope>): <subject>

feat(release): attach a CycloneDX SBOM to every release
```

Signed off, always — `git commit -s` writes the trailer. Subject under 72
characters, no full stop, imperative.

The scopes are `core`, `cli`, `app`, `ci`, `docs`, `scripts`, `benchmarks`,
`release`.

## 4. A pull request that closes the issue

```bash
python scripts/check_before_push.py      # what CI runs, here, first
git push -u origin rqt-12/feat/sbom-in-release
gh pr create --base dev --fill
```

The body must contain `Closes #12`. `contribution-policy.yml` fails the pull
request without it, because a merge that does not shut its issue leaves the
issue open forever and the tracker stops meaning anything.

`.github/PULL_REQUEST_TEMPLATE.md` asks for four things: what changed, why this
way, how it was verified, and the issue's acceptance criteria ticked off.

## 5. Review, then merge

`CODEOWNERS` requests the reviewer automatically. Nothing merges itself: the
gate is green checks **plus** a human clicking.

What the machine checks, so the reviewer does not have to:

| check | workflow |
| --- | --- |
| Branch name grammar | `contribution-policy.yml` |
| Commit subjects and sign-off | `contribution-policy.yml` |
| The pull request closes an issue | `contribution-policy.yml` |
| Lint, format, types | `ci.yml` → `lint` |
| Tests on two platforms and two Pythons | `ci.yml` → `test` |
| Coverage at or above 85 % | `ci.yml` → `coverage` |
| No credential anywhere in history | `ci.yml` → `security` |
| ISO 25010 metrics | `ci.yml` → `quality` |
| Benchmarks | `ci.yml` → `benchmark` |
| Three long-lived branches, no strays | `branch-policy.yml` |

What is left for the reviewer is whether the change is *right*, which is the
only part a machine cannot do.

Delete the branch when it merges. `enforce_branch_policy.py` names work
branches whose tip is already merged; leaving one is how a repository grows the
graveyard that point 14 exists to prevent.

### Closing the issue

`Closes #12` in the pull request body is required, and it will **not** close the
issue when the pull request merges into `dev`. GitHub acts on a closing keyword
only for the default branch, which here is `release`.

That is what the three-branch model costs, so the rule is explicit:

| when | what happens to the issue |
| --- | --- |
| merged into `dev` | **close it by hand**, with a comment naming the pull request |
| reaches `release` | the closing keyword fires, if it is somehow still open |
| release notes | list what shipped - this is where the trail ends |

Keep the keyword in the body regardless. It is the machine-readable link
between a change and the reason it exists, and every later reader - including
GitHub's own "linked issues" panel - follows it.

An issue that is done and still open is the worst state a tracker has: it looks
like work, it is counted as work, and nobody is sure.

## 6. Release

`dev` → `test` → `release`, then a tag.

```bash
git switch test && git merge --ff-only dev && git push
# manual checks on test
git switch release && git merge --ff-only test
git tag -s -a v1.2.0 -m "v1.2.0"        # -s signs it
git push origin release --tags
```

The tag runs the tests, builds the artefacts, generates the SBOM, writes a
SHA-256 for each file and publishes the GitHub Release. `CHANGELOG.md` is the
release notes, so it is updated *before* the tag, not after.

Mention any fixed vulnerability in the release notes by name. Someone deciding
whether to upgrade is reading exactly that line.

## The short version

```bash
gh issue create                       # acceptance criteria go in here
git switch -c rqt-12/feat/slug dev
git commit -s -m "feat(core): ..."
python scripts/check_before_push.py
git push -u origin HEAD
gh pr create --base dev --fill        # body says: Closes #12
```
