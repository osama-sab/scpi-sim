# scpi-sim

A simulated SCPI bench instrument (a digital multimeter) and a matching Python
driver. Everything runs without hardware.

- **`src/scpi_sim/`** — a TCP server on port 5025 that speaks SCPI: hierarchical
  command tree, error queue, IEEE 488.2 status registers, realistic timing and
  measurement noise.
- **`src/scpi_driver/`** — the host-side driver: swappable transport, typed API,
  explicit timeouts, error-queue checking.
- **`tests/`** — runs entirely without an instrument attached.

## Quickstart

```
uv sync
uv run pytest
```

## Status

Under construction. See `docs/BUILD_PLAN.md` for the staged plan and
`PROGRESS.md` for the current position.
