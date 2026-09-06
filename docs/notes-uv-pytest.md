# Notes — uv, pytest, and what "passing" means

Written 2026-09-06. Carry-over notes for continuing this project elsewhere.

---

## 1. uv does not run tests. pytest does.

These are two different tools doing two different jobs.

- **uv** manages the virtual environment and the dependency lock. It installs
  things and launches programs inside the environment. It has no concept of a
  test.
- **pytest** is the test runner. It finds tests, runs them, and decides
  pass/fail.

`uv run pytest` means: *start pytest, with this project's environment active.*
Nothing more. There is no "uv test result" — only a pytest result.

| Command | What it does |
|---|---|
| `uv sync` | Install/update the environment from `pyproject.toml` + `uv.lock` |
| `uv run pytest` | Run the whole test suite |
| `uv run pytest -v` | Same, one line per test with its name |
| `uv run pytest tests/test_smoke.py` | Run one file |
| `uv run pytest -k smoke` | Run tests whose name contains "smoke" |
| `uv run ruff check` | Lint |
| `uv run mypy` | Type-check |
| `uv run python somefile.py` | Run a file as a plain script (**not** a test run) |

`uv run somefile.py` is the script path, not the test path. If a filename is
not found, uv falls back to treating the argument as a program name — which is
why a wrong path reports `program not found` rather than `file not found`.

---

## 2. What "a test passed" actually means

A test is a **function**, not a file. pytest finds it by naming convention:

- the file matches `test_*.py` or `*_test.py`
- the function is named `test_*` and sits at module level
  (or is a method inside a `Test*` class)

The rule for pass/fail is one sentence:

> **The test passes if the function returns without raising. It fails if
> anything raises — normally a failed `assert`.**

Consequences that are not obvious at first:

- `print(...)` proves nothing. pytest captures stdout and hides it unless the
  test fails or you pass `-s`.
- `return True` proves nothing. The return value is ignored entirely.
- A file with no `test_*` function reports `collected 0 items` and exits
  successfully. **Zero tests is not a failure.** It is the most common way to
  think you have a green suite when you have nothing at all.

### Reading the output

```
collected 0 items      → nothing was found. Check naming, check testpaths.
1 passed               → one test function ran and did not raise.
1 failed               → an assert was false, or the code raised.
1 error                → the failure happened outside the test body,
                         usually a bad import at collection time.
```

`failed` and `error` mean different things. A failure is your assertion
rejecting the code. An error is the test never getting to run.

### assert introspection

pytest rewrites `assert` so the failure shows the real values:

```
>       assert len(items) == 4
E       assert 3 == 4
E        +  where 3 = len([1, 2, 3])
```

This is why plain `assert` is enough — no `assertEqual` helpers needed.

### The trap I hit

```python
assert scpi_sim, "scpi_sim not imported"
```

A module object is **always truthy**. This assertion can never fail, so it
tests nothing. Before writing a truthiness check, ask what the falsy cases are
— `0`, `0.0`, `""`, `[]`, `None` — and whether any of them are valid data. In a
measurement project a reading of exactly `0.0 V` is valid data, and `if value:`
would silently discard it.

---

## 3. Where this project stands

Phase 0 — Foundations. Not yet committed; not yet a git repository.

Done:
- Directory layout `src/scpi_sim/`, `src/scpi_driver/`, `tests/`, `docs/`
- `pyproject.toml` — src layout, pytest/ruff/mypy config, dev dependency group
- Environment installs, pytest collects and runs

Open, in order:
1. **`py.typed` marker missing.** `pyproject.toml` declares the classifier
   `Typing :: Typed`, but neither package ships the marker file, so mypy treats
   both as untyped (`import-untyped`) and strict mode is silently defeated.
   Fix: an empty `py.typed` inside each package directory, then confirm the
   `import-untyped` errors are gone. See PEP 561.
2. **Rewrite the smoke test** so the assertion is capable of failing, and give
   it a name that describes the property, not the act of checking.
   Needs `-> None` (ruff `ANN201`, mypy `no-untyped-def`).
3. `git init`, `.gitignore`, GitHub repo, first commit.
4. Pre-commit hook running ruff.

Habit to build: run `uv run ruff check` and `uv run mypy` **before** asking
whether code is correct. They answer faster than a person will.

---

## 4. If continuing this in the Claude app

The repo has a `CLAUDE.md` holding a learning contract — a list of components
that must not be written for me (SCPI parser, parameter parsing, error queue,
status registers, `*OPC`/`*WAI`, transport abstraction, choosing what to test).
That file is not visible outside the CLI. Paste sections 3 and 4 of it into any
new conversation, or the assistant will simply write the parser and the
learning objective is gone.

Fair game to ask for anywhere: config files, conceptual explanations of any
depth, syntax lookups, code review, adversarial test *ideas*.
