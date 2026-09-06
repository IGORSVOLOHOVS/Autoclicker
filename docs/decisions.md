# Decisions that look like gaps

This standard is measured against the [OpenSSF Best Practices
Badge](https://github.com/ossf/best-practices-badge) and [OpenSSF
Scorecard](https://github.com/ossf/scorecard) — see
[`standards-comparison.md`](standards-comparison.md). Some of their criteria
are deliberately not met.

Each one is written down here with its reason, because a divergence that is not
recorded gets rediscovered as a defect, argued about, and then decided the same
way again six months later.

---

## Internationalisation: no

OpenSSF `internationalization`, silver level.

Point 12 of this standard requires English throughout — code, comments, commit
messages, documentation, issues. That is the opposite of what silver asks for.

**Why.** One author, one language, and a repository that a stranger can read.
Mixed-language identifiers are worse than either language alone: `def
проверить_файл` cannot be grepped by half the people who need to, and a
docstring in one language attached to a symbol in another is where translation
drift starts.

If this project ever ships a user interface to people who do not read English,
this decision is reopened — that is the trigger, not a general wish to be
international.

---

## Two-person review: no

OpenSSF `two_person_review`, gold level.

Pull requests require one approval, from `CODEOWNERS`.

**Why.** There is one maintainer. A rule that cannot be satisfied is not a
stricter rule, it is a rule that gets bypassed, and a bypassed rule teaches
that the gates are advisory. One human approval and a green pipeline is the
strongest gate that can actually hold here.

Reopen when there are two people who can review this code.

---

## Governance, roles, bus factor: no

OpenSSF `governance`, `roles_responsibilities`, `bus_factor`, silver and gold.

**Why.** Same reason, stated plainly rather than papered over with a
`GOVERNANCE.md` that says "the maintainer decides". The bus factor of this
repository is one. Writing a governance document would not change that number;
it would only make it harder to see.

The honest mitigation is that everything here is executable and documented:
`scripts/apply_template_to_repo.py`, `docs/workflow.md`, and CI that fails
loudly. Somebody picking this up finds instructions, not folklore.

---

## Reproducible builds: not yet

OpenSSF `build_reproducible`, silver level.

**Why.** The release artefact is built by PyInstaller, which embeds a
timestamp and a build path. Making that reproducible means pinning the Python
build, normalising the environment and post-processing the executable — real
work, for a benefit this project does not yet have a use for.

What exists instead: a SHA-256 per artefact and a CycloneDX SBOM per release,
so what shipped can be identified even though it cannot yet be re-derived.

Reopen when somebody needs to verify a binary they did not build.

---

## Fuzzing and dynamic analysis: no

OpenSSF `dynamic_analysis`, `fuzzing`, passing and silver.

**Why.** The domain layer is pure text processing over `str` with no parser,
no network input and no memory management. A fuzzer would be exercising
CPython's own string handling.

Reopen the moment this project parses a binary format or takes untrusted input
over a socket. Then it is not optional.

---

## Signed releases: partly

OpenSSF `signed_releases`, `version_tags_signed`, silver level.

Tags are signed — `git tag -s`, see [`workflow.md`](workflow.md). Release
artefacts are not.

**Why.** A signed tag proves who cut the release, which is the part that
matters when the source is what people consume. Signing the binaries as well
means key management for a project nobody installs from a binary yet.

---

## What is *not* on this list

Two OpenSSF criteria this standard fails and does **not** defend, because they
are simply not done yet:

- `release_notes_vulns` — release notes do not yet call out fixed
  vulnerabilities by name. They should.
- `know_secure_design`, `know_common_errors` — nothing records that the
  maintainer has read the common design and implementation errors for this kind
  of software.

They are open work, not decisions. Keeping them here, separated from the
decisions, is the point of the file: a list of "we chose this" that quietly
absorbs "we did not get to this" stops being useful.
