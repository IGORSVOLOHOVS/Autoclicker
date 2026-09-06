# Decisions that look like gaps

This project follows revision 2 of the
[repo-quality-template](https://github.com/IGORSVOLOHOVS/repo-quality-template)
standard - twenty-four points, themselves measured against the OpenSSF Best
Practices Badge.

Some of those points are deliberately not met here. Each one is written down
with its reason and with the thing that would make it worth reopening, because
a divergence that is not recorded gets rediscovered as a defect, argued about,
and decided the same way again six months later.

---

## Point 12, English throughout: the interface stays Russian

The standard says English everywhere. Here, code, comments, commit messages,
documentation, issues and pull requests are English. The **window** is Russian:
"Один клик", "Левая", "Перетаскивание".

**Why.** The people who use this program read Russian. Translating the
interface to satisfy a rule about the repository would be changing the product
to make the paperwork tidier.

The split is enforced rather than hoped for. `settings.py` holds two tables -
`BUTTON_LABELS` and `CLICK_TYPE_LABELS` - and they are the only place below the
window where a Russian string appears. `core.py` speaks in `ClickType.SINGLE`
and `MouseButton.LEFT`. A translated label changes one dictionary and nothing
else.

`ruff`'s RUF001 rule, which flags Cyrillic letters that could be mistaken for
Latin ones, is switched off for `gui.py` and `settings.py` and nowhere else.

**Reopen if** the program gains users who do not read Russian. Then it is not a
translation, it is internationalisation, and it is a feature with its own
issue.

---

## No test drives the Qt window

OpenSSF `test_most`, and the standard's own point 3.

**Why.** It needs a display; on a Linux runner a virtual one; and `keyboard`
wants root there to claim the global hotkeys. What a widget test would actually
check - that a checkbox flips a boolean - is not where either of the two faults
found during this refactoring lived. Both were arithmetic, and the arithmetic
is now covered at 100 %.

Coverage **excludes** `gui.py` explicitly rather than quietly counting it, so
the 100 % figure is a statement about the two modules it names.

**Reopen if** a fault is ever traced to the widget wiring. That is the evidence
that would change the calculation.

---

## The released binary is not signed

OpenSSF `signed_releases`, silver level.

**Why.** Code-signing certificates cost money annually, and this is a free
program with one maintainer. The release carries a SHA-256 per artefact and a
CycloneDX SBOM, so what shipped can be identified even though its author cannot
be cryptographically proven.

Tags are signed - `git tag -s` - which covers the source.

**Worth knowing:** a program that moves the mouse and installs a keyboard hook
looks, to an antivirus, exactly like something unpleasant. Signing would help
with that, and it is the strongest argument for reopening this.

---

## Two-person review: no

OpenSSF `two_person_review`, gold level.

**Why.** One maintainer. A rule nobody can satisfy is not a stricter rule, it
is a rule that gets bypassed, and a bypassed rule teaches that the gates are
advisory. One approval from `CODEOWNERS` plus a green pipeline is the strongest
gate that can actually hold here.

---

## No fuzzing, no dynamic analysis

OpenSSF `dynamic_analysis`, passing level.

**Why.** The domain is arithmetic over integers and floats, and JSON parsing
handed straight to a validator that rejects anything it does not recognise.
There is no parser of a binary format, no network input, and no memory
management. A fuzzer would be exercising CPython.

**Reopen if** the program ever reads a format it did not write.

---

## The preset format was not modernised

Strings where numbers belong, Russian labels in a data file, a schema with no
version field.

**Why.** Every preset anybody saved since v1.0.0 is in that format. Changing it
means either breaking them or writing a migration for a file with four users.
The awkwardness is confined to the `Preset` dataclass, and nothing above it has
to know.

**Reopen if** a new setting cannot be expressed in it. Then the format gets a
version field and a migration, in one go.

---

## What is *not* on this list

Open work, kept separate on purpose - a list of "we chose this" that quietly
absorbs "we did not get to it" stops being useful:

- **Release notes do not name fixed vulnerabilities** - OpenSSF
  `release_notes_vulns`. There have been none, which is not the same as having
  a practice.
- **No reproducible build.** PyInstaller embeds a timestamp and a build path.
