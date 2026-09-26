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

- Final checks and sanity checks before each commit
- Docstrings
- Planning and maintaining `PROGRESS.md`
- `pyproject.toml` and other configuration files

Claude does not:

- Write the SCPI code (parser, error queue, status registers, driver logic)
- Give direct solutions, even when asked
- Make design decisions; those choices are mine

## Quickstart

```bash
uv sync
uv run pytest
```

## Status

Under construction. See `docs/BUILD_PLAN.md` for the staged plan and
`PROGRESS.md` for the current position.
