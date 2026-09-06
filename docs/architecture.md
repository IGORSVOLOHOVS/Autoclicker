# Architecture

Two layers, and the dependency points one way.

```
run_autoclicker.py
        │
        ▼
src/autoclicker/gui.py      Qt widgets, threads, the mouse, the hotkeys
        │
        ▼
src/autoclicker/core.py     when to click, where to click, when to stop
src/autoclicker/settings.py what a run is, what a preset file means
```

`core` and `settings` import `random`, `json`, `dataclasses`, `enum` and
`pathlib`. Not Qt, not pyautogui, not keyboard. That is the whole rule, and
everything below follows from it.

## Why the split exists

v1.0.0 was a single 526-line file. It worked, and there was no way to find out
whether it still worked except by opening it and clicking. Two faults had been
living in it since release, both in code that a test would have caught in a
second:

**A silent 1 ms click storm.** The interval was computed as
`interval + uniform(-range, range) / 1000`, and a negative result was clamped
to `0.001`. Nobody was told. A 50 ms rhythm with a 200 ms spread became a
thousand clicks a second, and the only symptom was that it felt wrong.
`ClickSettings.validate` now refuses that combination and names both numbers.

**A random offset that did nothing.** The scattered coordinate was computed
every iteration, and `moveTo` was only called when "fixed position" was ticked.
With the box unticked the offset was calculated and thrown away. It now applies
to the cursor as well, which is what switching it on was asking for.

Neither is exotic. Both are arithmetic, and arithmetic buried in a Qt thread is
arithmetic nobody reads.

## What is in each layer

### `settings.py` - what a run is

Two shapes, deliberately not one.

`Preset` is the file on disk: every value a string, the mouse button and click
type written in Russian, because that is what the interface shows and because
preset files written by v1.0.0 must keep loading. A test reads
`configs/Dota2Pudge.json` from this repository rather than a fixture, so
compatibility is proven rather than assumed.

`ClickSettings` is what the clicker runs on: floats, integers, enumerations,
and a validator. It is frozen, so a run cannot change under the thread that is
executing it.

`preset_to_settings` is the border between them, and the only place below the
user interface where a Russian label is allowed to appear. When it refuses, it
names the field - somebody who was editing JSON in Notepad should not be shown
`invalid literal for int() with base 10`.

### `core.py` - what happens next

Four functions and an estimate:

| function | asked | per click |
| --- | --- | --- |
| `next_interval` | how long to sleep | yes |
| `next_position` | where to click | yes |
| `should_stop` | is the run finished | yes |
| `estimate_run` | how long will this take | once |

Every one takes a `random.Random` rather than calling the module-level
functions. That is what makes the randomness testable: seed the generator and
the sequence is the same every time, so a failing test is reproducible instead
of appearing one run in fifty.

### `gui.py` - the shell

Qt widgets, the worker threads, the global hotkeys, the file dialogs. It holds
the Russian labels, maps them through `settings.py`, and asks `core` what to do
on every iteration. It decides nothing itself.

## What was deliberately left out

**No test drives the Qt window.** It would need a display, and on a Linux
runner a virtual one, and `keyboard` wants root there to claim the hotkeys.
What a widget test could check - that a checkbox flips a boolean - is not where
the faults were. Coverage excludes `gui.py` and says so rather than quietly
counting it.

**No abstraction over pyautogui.** A `MouseDriver` protocol with a fake for
tests would let `gui.py` be tested without a mouse. It would also add an
indirection to a module whose entire job is four `pyautogui` calls in a row.
When something in the shell becomes worth testing, that is the moment to add
it, not before.

**Settings are still passed as one frozen object.** Splitting them into a
timing object and a targeting object would be tidier and would double the
number of things to thread through the constructor. One object crosses the
boundary; the boundary is one function call.

**The preset format was not modernised.** Strings and Russian labels are
awkward, and changing them would break every preset anybody has saved. The
awkwardness is confined to `Preset`, and nothing above it has to care.

## Where to put a change

| change | where |
| --- | --- |
| timing, scatter, stopping, estimates | `core.py`, with a test |
| a new setting, or a preset field | `settings.py`, with a round-trip test |
| a widget, a dialog, a hotkey | `gui.py` |
| anything you cannot test without a screen | `gui.py`, and ask why |

Logic that reaches into `gui.py` cannot be tested and cannot be reused. That is
the mistake this layout exists to make difficult.
