# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
this project adheres to [Semantic Versioning](https://semver.org/).

## [1.1.0] - unreleased

### Fixed

- A random interval wider than the interval itself silently became a 1 ms click
  storm: the sleep went negative and was clamped without a word. Settings now
  refuse that combination and name both numbers. Presets already in use are
  unaffected - a 25 ms spread on a 50 ms interval was always valid.
- The random offset did nothing unless "fixed position" was ticked. The
  scattered coordinate was computed every iteration and thrown away. It now
  applies to the cursor as well.

### Changed

- **The launcher is `run_autoclicker.py`.** A module named `autoclicker.py`
  next to a package named `autoclicker` shadows it, and the resulting
  "not a package" error points at nothing. The README said `python main.py`,
  which had not been the name of any file for some time.
- The code moved into `src/autoclicker/`: `core.py` and `settings.py` are pure
  and tested, `gui.py` is the Qt window over them.
- A setting that cannot do what it says is refused when it is entered, with a
  message naming the field, rather than at run time.

### Added

- 35 tests, 100 % branch coverage of the domain, with an 85 % floor in CI.
- Benchmarks over the per-click decisions.
- CI on Ubuntu and Windows, Python 3.10 and 3.12: ruff, format, strict mypy,
  tests, coverage gate, gitleaks over full history, ISO 25010 metrics.
- Issue and pull-request templates, `CODEOWNERS`, Dependabot, SBOM per release.
- README screenshots, regenerated from the program itself by
  `scripts/capture_usage_screenshots.py` rather than taken by hand.
- `SECURITY.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`.
- `docs/architecture.md`, `docs/quality-iso25010.md`, `docs/decisions.md`,
  `docs/workflow.md`, `docs/branching.md`.
- Three branches: `release`, `dev`, `test`.


### Added

- Issue templates with mandatory acceptance criteria, a pull-request template,
  and `CODEOWNERS` - the shape of a contribution, in the place GitHub reads it.
- `scripts/enforce_contribution_policy.py` and `contribution-policy.yml`:
  branch grammar, commit format, sign-off and the issue link, checked before a
  human is asked to read the diff.
- `scripts/generate_sbom.py`: a CycloneDX bill of materials, attached to every
  release with its own checksum.
- Strict `mypy` over `src/`, in the lint job.
- `.github/dependabot.yml`, weekly, for pip and for actions.
- `CODE_OF_CONDUCT.md`.
- `docs/workflow.md` - issue to release, six steps.
- `docs/decisions.md` - the OpenSSF criteria this project deliberately does not
  meet, each with its reason.
- `docs/standards-comparison.md` - where the points came from, measured against
  the OpenSSF Best Practices Badge and Scorecard.

### Changed

- The standard is twenty-four points, not fourteen.
- Point 14 is now "three long-lived branches" rather than "three branches":
  work happens on a short-lived `<code>-<issue>/<type>/<slug>` branch that is
  deleted when its pull request merges. The old rule made a pull request
  impossible, and with it the review gate.
- `scripts/apply_template_to_repo.py` copies the new infrastructure and reports
  all twenty-four points.


## [1.0.0] - 2026-08-01

### Added

- Text analysis domain layer (`quality_template.core`): tokenising, sentence
  counting, word frequencies, lexical diversity.
- Command line interface with table and JSON output.
- tkinter desktop window with live analysis as you type.
- Test suite covering the domain layer and the CLI, with a coverage floor of 85
  percent enforced by the build.
- Benchmarks for `analyse_text`, `tokenise` and `top_words`.
- CI on Ubuntu and Windows across Python 3.10 and 3.12: lint, format check,
  tests, secret scan, quality metrics, benchmarks.
- Release workflow producing a single-file executable, a zip and a SHA-256
  checksum for each, published as a GitHub Release on a `v*.*.*` tag.
- ISO/IEC 25010 assessment, with four characteristics measured automatically by
  `scripts/collect_quality_metrics.py`.
- Branch policy of exactly `release`, `dev` and `test`, enforced by CI.
- Secret scanning with `gitleaks` both in pre-commit and over full history in CI.
- `scripts/apply_template_to_repo.py` to roll this layout onto another project.

[Unreleased]: https://github.com/IGORSVOLOHOVS/repo-quality-template/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/IGORSVOLOHOVS/repo-quality-template/releases/tag/v1.0.0
