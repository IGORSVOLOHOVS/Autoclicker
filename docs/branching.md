# Branching

Three long-lived branches, and nothing that outlives a pull request.

| Branch | Holds | Protected |
| --- | --- | --- |
| `release` | What is published. Every commit is tagged `vX.Y.Z` and has a GitHub Release with a downloadable artefact | yes |
| `test` | Release candidate. Full CI plus manual checks before it moves to `release` | yes |
| `dev` | Day-to-day work. CI must be green | yes |

```
dev ──────► test ──────► release ──► tag vX.Y.Z ──► artefact
 ▲                                        │
 └──────────── hotfix merged back ────────┘
```

## Work branches

A pull request needs a branch on the remote to point at, so there is a fourth
kind — and only that kind:

```
<code>-<issue>/<type>/<slug>
rqt-12/feat/sbom-in-release
```

`code` and the type list come from `[tool.repo-quality]` in `pyproject.toml`.
The issue number is part of the name, so the reason the branch exists is never
more than one `gh issue view` away.

A work branch is deleted when its pull request merges. `enforce_branch_policy.py`
names any whose tip is already merged; leaving one is how the graveyard starts.

## Why only three long-lived ones

Long-lived feature branches are where work goes to be forgotten. The audit of
this account found repositories whose default branch was nearly empty while the
real code sat in a branch nobody had touched in a year — `Sandbox`,
`soal-coffee` and `WebSearchAI` among them. Three long-lived branches make that
impossible: if it is not on the way to `dev`, it does not exist.

This used to read "three branches, never a fourth", and work was supposed to
stay in a local clone. That rule forbade pull requests — a pull request cannot
point at a branch that was never pushed — which meant no review gate, no
templates, and no record of why a change was made. The grammar above buys the
review back without buying the graveyard: a branch has to carry an issue
number, and it has to go away when the issue closes.

## Enforcement

`scripts/enforce_branch_policy.py` fails on a branch that is neither long-lived
nor a well-formed work branch, locally or on the remote. It runs on every push
and every Monday via `.github/workflows/branch-policy.yml`.

```bash
python scripts/enforce_branch_policy.py --remote origin   # report
python scripts/enforce_branch_policy.py --delete-extra    # remove merged extras
```

`--delete-extra` refuses to delete a branch whose tip is not already contained
in `release`, `dev` or `test`. A branch holding unique commits is named and
kept, never silently dropped.

## Setting this up on an existing repository

1. **Look before deleting.** List every branch and what is only in it:
   ```bash
   git fetch --all
   for b in $(git branch -r --format='%(refname:short)'); do
     echo "$b: $(git log --oneline origin/dev.."$b" 2>/dev/null | wc -l) unique commits"
   done
   ```
2. Merge or cherry-pick anything worth keeping into `dev`.
3. Create the three branches; rename `main` or `master` to `release`.
4. Delete the rest: `git push origin --delete <branch>`.
5. Set `release` as the default branch and protect all three in repository
   settings: require CI to pass, require pull requests, forbid force-push.

Step 1 is not optional. Deleting a remote branch is not undoable from the GitHub
UI.

## Releasing

```bash
git checkout release && git merge --ff-only test
git tag -s -a v1.2.0 -m "v1.2.0"        # -s signs the tag
git push origin release --tags
```

The tag triggers `.github/workflows/release.yml`, which runs the tests, builds
the executable and the zip, generates the CycloneDX SBOM, writes a checksum for
each file, and publishes a GitHub Release. Update `CHANGELOG.md` before
tagging — the release notes are taken from it, and any fixed vulnerability is
named there.
