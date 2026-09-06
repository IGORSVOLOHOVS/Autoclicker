# Quality assessment — ISO/IEC 25010

The ISO/IEC 25010:2011 product quality model defines eight characteristics. This
document assesses the project against each of them.

Four are **measured** by `scripts/collect_quality_metrics.py`, which runs in CI
on every push and fails the build below a threshold. Four need human judgement
and are argued here, citing the measured numbers rather than asserting quality.

Regenerate the numbers with:

```bash
python scripts/collect_quality_metrics.py --output quality-report.json
```

---

## 1. Functional suitability — measured

*Does it do what it claims, correctly and completely?*

| Sub-characteristic | Evidence |
| --- | --- |
| Functional completeness | Every public function in `quality_template.core` has tests |
| Functional correctness | Test pass rate, reported by the metrics script |
| Functional appropriateness | The CLI and GUI both call the same domain functions, so they cannot disagree |

The README documents exactly the flags `cli.py` implements; `test_cli.py`
exercises each of them, so documentation drift fails the build.

## 2. Performance efficiency — assessed, with measurements

*Time behaviour, resource use, capacity.*

`benchmarks/test_performance.py` measures `analyse_text` at 1, 50 and 500
paragraphs, so the scaling shape is visible rather than assumed.
`scripts/profile_application.py` attributes time to individual functions.

Tokenisation is a single compiled regular expression over the input and
frequency counting is a `Counter`, so the work is linear in input length. There
is no caching layer, which is the deliberate trade: the workload is small enough
that a cache would add invalidation bugs without measurable benefit.

**Known limit:** the whole text is held in memory. Inputs beyond roughly a
hundred megabytes would need streaming, which is not implemented.

## 3. Compatibility — assessed

*Co-existence and interoperability.*

The package writes nothing outside paths given to it, holds no global state and
opens no network connection, so it can run alongside anything. `--json` emits a
stable machine-readable shape for pipelines. The GUI uses tkinter from the
standard library, so it introduces no toolkit conflict.

## 4. Usability — assessed

*Can someone learn it, use it and recover from mistakes?*

| Sub-characteristic | How it is addressed |
| --- | --- |
| Appropriateness recognisability | README opens with a screenshot of the running program |
| Learnability | `--help` lists every flag; one example per flag in the README |
| Operability | Reads a file argument or standard input; the GUI updates as you type |
| User error protection | A missing file exits with a message, not a traceback; a non-positive `--top` is rejected explicitly |
| User interface aesthetics | Dark theme, monospaced numbers, screenshot in `docs/screenshots/` |
| Accessibility | **Weakest area.** No keyboard-only navigation testing, no screen-reader labels, no contrast audit |

## 5. Reliability — measured

*Maturity, availability, fault tolerance, recoverability.*

Branch coverage is measured and the build fails below 85 percent
(`fail_under` in `pyproject.toml`). Tests cover empty input, non-string input,
text with no sentence terminator, stop-words-only text and non-ASCII text —
the boundaries where this kind of code usually breaks.

`TextStats` is a frozen dataclass, so a result cannot be mutated after the fact.

**Known limit:** no fuzzing, and no property-based tests.

## 6. Security — assessed

*Confidentiality, integrity, non-repudiation, accountability, authenticity.*

| Control | Where |
| --- | --- |
| No credential in source | `gitleaks` in pre-commit **and** in CI over full history |
| Committed secrets impossible to add accidentally | `.gitignore` excludes `.env`; `.env.example` carries names only |
| Static security linting | `ruff` rule set `S` (bandit rules) |
| Artefact integrity | Every release file ships a `.sha256` |
| Dependency provenance | `requirements-dev.lock` pins exact versions |

The application parses text and never evaluates it; there is no `eval`, no
`pickle`, no subprocess call on user input.

**Known limit:** no signed commits and no SBOM.

## 7. Maintainability — measured

*Modularity, reusability, analysability, modifiability, testability.*

The domain layer has no I/O and no framework imports, so the CLI and the GUI are
replaceable without touching it — that is what makes the tests short.

Measured: average cyclomatic complexity, worst single function, average
maintainability index, and outstanding lint findings. `ruff` enforces a
complexity ceiling of 10 (`C90`), so a function cannot quietly grow past it.

## 8. Portability — measured

*Adaptability, installability, replaceability.*

CI runs on Ubuntu and Windows across two Python versions; the matrix is read
directly out of `ci.yml` by the metrics script, so this section cannot claim
more than CI actually proves. Installation is one command
(`python scripts/install_dependencies.py`), and a release needs no Python at all.

**Known limit:** macOS is not in the CI matrix, so macOS support is untested.

---

## How to read the score

The overall figure is the mean of the four measured characteristics only. It is
deliberately not a score out of eight: averaging a measured coverage percentage
with a hand-written opinion about usability would produce a number that looks
objective and is not.
