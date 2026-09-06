# Quality assessment - ISO/IEC 25010

Eight characteristics. Four are measured on every push by
`scripts/collect_quality_metrics.py`; four are argued, and the arguments cite
those measurements rather than adjectives.

Numbers below are from the run on `dev` after the standard was adopted.
Reproduce them with:

```bash
python scripts/collect_quality_metrics.py
pytest benchmarks --benchmark-only
```

**Measured overall: 91.0.**

---

## 1. Functional suitability - measured

| metric | value |
| --- | --- |
| Tests passed | 35 |
| Tests failed | 0 |
| Pass rate | 100 % |

The suite covers the two modules that decide anything: interval arithmetic
including the jitter bounds, position offset including its corners, the stop
condition, run estimates, duration formatting, preset round-tripping, and every
validation rule with the field it names.

Two of those tests exist because the behaviour they check was wrong in v1.0.0 -
the silent 1 ms clamp and the offset that did nothing without a fixed position.
They are named after the fault rather than after the function.

**Not covered:** the Qt window. See "what was deliberately left out" in
[`architecture.md`](architecture.md).

## 2. Performance efficiency - assessed, with measurements

The clicker asks for an interval and a position before every click, and the
shortest interval the interface allows is 1 ms. Anything these decisions cost
comes out of the rhythm the user asked for, so it is worth knowing.

`benchmarks/test_performance.py`, median of many rounds:

| what is measured | median | per click |
| --- | ---: | --- |
| `next_interval`, no jitter | 81 ns | yes |
| `next_position`, pinned | 117 ns | yes |
| `next_interval`, with jitter | 285 ns | yes |
| `format_duration` | 325 ns | no |
| `next_position`, with offset | 800 ns | yes |
| `estimate_run` | 1.0 µs | once per run |
| `preset_to_settings` | 2.2 µs | once per preset |

Worst case per click is `next_interval` with jitter plus `next_position` with
offset: **1.1 µs**. Against the 1 ms floor that is 0.11 %, and against the 50 ms
interval in the shipped preset it is 0.002 %. The decisions do not eat the
rhythm they are timing.

`preset_to_settings` is twenty times the cost of a click decision and runs
once, when a preset is chosen. It is measured to show that it is nowhere near
the hot path, which is the only reason to keep the string parsing there.

The real cost of a click is `pyautogui`, which is outside this project and is
not measured here.

## 3. Compatibility - assessed

CI runs on Ubuntu and Windows, Python 3.10 and 3.12 - four combinations, all
green. `core` and `settings` are pure Python with no platform calls, so they
run wherever Python does.

The program as a whole is Windows-first in practice: `keyboard` needs root on
Linux to register global hotkeys, and `pyautogui` needs a display. That is a
property of the dependencies, not of this code, and it is why CI does not
install them.

Preset files are UTF-8 JSON and are read identically on every platform. A
preset written on Windows in 2025 loads today - there is a test.

## 4. Usability - assessed

The interface is Russian, for a Russian-speaking audience, and stays that way -
see [`decisions.md`](decisions.md).

What changed for the user with this revision:

- A setting that cannot do what it says is refused **when it is entered**, with
  a message naming the field, instead of silently becoming a click storm at
  run time.
- The window and a preset file go through the same validator, so a
  configuration the file would reject cannot be started from the interface
  either.
- The random offset now does what the checkbox says.

Not assessed: anything about the layout of the window. Nobody has watched a
user in front of it, and inventing a usability score without that would be
making one up.

## 5. Reliability - measured

| metric | value |
| --- | --- |
| Branch coverage | 100 % |
| Coverage floor enforced in CI | 85 % |

Branch coverage, not line coverage: every validation rule has a test for the
branch that raises and the branch that does not.

Reliability of the running program is bounded by `pyautogui` and `keyboard`
holding the mouse and the keyboard hook, which this project does not control.
Failures there are caught and printed rather than crashing the run.

## 6. Security - assessed

There is no network, no subprocess, no deserialisation of anything but the
user's own JSON, and no credential.

| control | how |
| --- | --- |
| Static security linting | `ruff` rule set `S` (bandit rules), in CI |
| Secret scan | `gitleaks`, full history, every push |
| Dependency monitoring | Dependabot, weekly, pip and actions |
| Bill of materials | CycloneDX, generated per release |

The honest caveat: this is a program that moves the mouse and installs a global
keyboard hook. It is indistinguishable, to an antivirus, from something
unpleasant, and that is a property of what it does rather than a defect. The
released binary is not signed - see [`decisions.md`](decisions.md).

## 7. Maintainability - measured

| metric | value |
| --- | --- |
| Average cyclomatic complexity | 2.32 |
| Most complex function | `ClickerThread.run`, 9 |
| Ceiling enforced by `ruff` `C90` | 10 |
| Average maintainability index | 63.8 |
| Outstanding lint findings | 0 |

The most complex function is the worker loop, at 9 against a ceiling of 10.
That is deliberate rather than lucky: it is the one place where the four click
types, the move and the stop condition meet, and every calculation it used to
contain has already been moved out. Splitting what is left would spread six
lines across two functions without removing a branch.

The index of 63.8 is dragged down by `gui.py`, which is 500 lines of widget
construction. `core.py` and `settings.py` sit well above it.

## 8. Portability - measured

| metric | value |
| --- | --- |
| Requires | Python >= 3.10 |
| CI operating systems | ubuntu, windows |
| CI Python versions | 3.10, 3.12 |

No compiled extension of this project's own. The dependencies bring their own
platform constraints, discussed under compatibility.

---

## How to read the score

91.0 is the mean of the four measured characteristics. It is a number about
tests, coverage, complexity and platforms - not about whether the program is
pleasant to use, and not about whether it is the right program to have written.

The four assessed characteristics carry no number on purpose. A usability score
invented without a user in front of the window would be the least trustworthy
figure in this document, and it would be the one people quoted.
