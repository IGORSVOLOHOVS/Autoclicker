# Architecture

## The shape

Three layers, with dependencies pointing one way only.

```
        ┌──────────────┐      ┌──────────────┐
        │  cli.py      │      │  app.py      │     shells: parse input,
        │  (terminal)  │      │  (tkinter)   │     render output
        └───────┬──────┘      └──────┬───────┘
                │                    │
                └─────────┬──────────┘
                          ▼
                  ┌───────────────┐
                  │   core.py     │                domain: pure functions
                  │  (no I/O)     │                over plain data
                  └───────────────┘
```

`core.py` imports nothing but the standard library's `re`, `collections` and
`dataclasses`. It does not read files, does not print and does not know a user
interface exists.

## Why this way

**The shells are interchangeable.** `cli.py` and `app.py` both call
`analyse_text` and `top_words` and do nothing else of substance. A third shell —
an HTTP endpoint, say — would be another file at the same level, with no change
below it. It also means the CLI and the GUI cannot disagree about what a word
is, because there is only one implementation.

**The tests are short because the domain has no setup.** `test_core.py` needs no
fixtures, no temporary directories and no mocks: every function takes a string
and returns a value. The only fixture in the whole suite is `tmp_path` in the CLI
tests, which is testing file handling — the thing the CLI is actually for.

**Benchmarking and profiling have a clean target.** `benchmarks/` calls the
domain functions directly, so a measurement reflects the algorithm and not
terminal rendering or window redraws.

## Data flow

1. A shell obtains text — a file, standard input, or the GUI's text widget.
2. `analyse_text(text)` tokenises once, counts once, and returns a frozen
   `TextStats`.
3. `top_words(stats, limit)` filters and ranks the counter that `TextStats`
   already carries. It never re-reads the text.

Step 2 is the only pass over the input. This matters at scale: analysing then
asking for the top 10, then the top 50, costs one tokenisation, not three.

## Deliberate omissions

- **No plugin system.** Two shells do not justify an abstraction layer; adding
  one now would be architecture for its own sake.
- **No configuration file.** Every option is a CLI flag. A config file would
  create a second source of truth for the same settings.
- **No caching.** Analysis is linear and fast; a cache would add invalidation
  bugs for no measurable gain. See `docs/quality-iso25010.md` §2.
- **No streaming.** The whole text is held in memory, which caps usable input at
  roughly a hundred megabytes. Streaming would complicate every function to
  serve a case this tool does not have.

## Where to add things

| To add | Put it |
| --- | --- |
| A new statistic | `core.py`, plus tests in `test_core.py` |
| A new output format | `cli.py`, next to the `--json` branch |
| A new interface | a new module beside `cli.py`, calling `core` only |
| A performance claim | `benchmarks/`, so it is measured rather than asserted |
