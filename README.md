# scpi-sim

A simulated SCPI bench instrument (a digital multimeter) and a matching Python
driver. Everything runs without hardware.

- **`src/scpi_sim/`** — a TCP server on port 5025 that speaks SCPI: hierarchical
  command tree, error queue, IEEE 488.2 status registers, realistic timing and
  measurement noise.
- **`src/scpi_driver/`** — the host-side driver: swappable transport, typed API,
  explicit timeouts, error-queue checking.
- **`tests/`** — runs entirely without an instrument attached.

## How this project uses AI

This is a personal project for learning SCPI and instrument-driver design. I use
Claude (Anthropic's AI assistant) as a tutor and reviewer, with a fixed split of
responsibilities.

Claude does:

- Code review of what I write, and final checks before each commit
- Docstrings and commit messages
- Planning and maintaining `PROGRESS.md`
- `pyproject.toml` and other configuration files

Claude does not:

- Write the SCPI code (parser, error queue, status registers, driver logic)
- Design my tests; I decide what to test, Claude reviews the plan
- Make design decisions; those choices are mine

When I'm stuck, help comes in steps. First a question that narrows the
search, then the concept and the shape of a solution (a function signature,
the cases to handle, a pointer to the standard), then one hint at a time.
If I've made several real attempts on the same problem over a couple of
hours, Claude gives one bigger hint: a skeleton of the structure or a
decision table, with the individual steps still left for me to fill in. It
never hands over the finished code.

## Quickstart

```bash
uv sync
uv run pytest
```

## Status

Under construction. See `docs/BUILD_PLAN.md` for the staged plan and
`PROGRESS.md` for the current position.
