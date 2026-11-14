# Contributing

## Setting up

```powershell
py -3.11 -m venv .venv
.venv\Scripts\pip install -e .[dev]
.venv\Scripts\pre-commit install      # optional: run the checks on every commit
```

## Before a change is done

```powershell
.venv\Scripts\python -m ruff format .
.venv\Scripts\python -m ruff check .
.venv\Scripts\python -m mypy
.venv\Scripts\python -m pytest
.venv\Scripts\python tools\mutation_check.py
```

CI runs the same commands.

## Rules of the house

- **Where things go.** A formula belongs in `domain`, a file format or report layout in
  `adapters`, a decision about what the user sees in `ui/presenter.py`, a widget in
  `ui/main_window.py`. `docs/architecture.md` section 5 has the details; the import
  contracts in `pyproject.toml` enforce them.
- **A new guard must be seen failing.** When you add an assertion, add the mistake it is
  meant to catch to `tools/mutation_check.py` and watch it get caught. An assertion that
  passes on broken code is the most expensive kind of test.
- **Numbers are checked against something independent** — a hand calculation written
  beside the assertion, a property that must hold for every input, or the reference values in
  `tests/golden`. A test that repeats the formula it tests proves nothing.
- **The error model is not improved in passing.** It is the full program's, simplifications
  included, so that the two can be compared. If a result looks wrong, open an issue;
  `docs/adr/0004-error-model-of-the-full-program.md` explains why.
- **Visual changes are checked on pixels.** Run `tools/make_screenshots.py` and look at the
  images, in both themes. The offscreen tests cannot see a clipped label.
- **A decision that would surprise the next reader gets an ADR** in `docs/adr/`.

## Reference values and sample

`tools/make_sample.py` regenerates the sample structure, `tools/make_golden.py` the reference
values (it needs the full RietCalc program, which is not part of this repository). The
reference file stores the SHA-256 of the structure; changing one without the other fails a test.
`tools/make_full_screenshots.py` renders the screenshots of the full program and needs it too.
