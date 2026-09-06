# PROGRESS

Session state for this project. Update at the end of every working session.
Any AI assistant reads this first — keep it honest, including the parts that
are not going well.

---

## Current position

**Phase:** 0 — Foundations
**Started:** <!-- YYYY-MM-DD -->
**Last session:** <!-- YYYY-MM-DD -->
**Hours invested so far:** 0

**Next concrete task:**
> Initialise the repository and get one trivial test passing in CI.

---

## Phase checklist

Full detail in `docs/BUILD_PLAN.md`. Tick only when committed and pushed.

### Phase 0 — Foundations (3–4 h)
- [ ] `git init`, GitHub repo, `.gitignore`
- [ ] Directory layout: `src/scpi_sim/`, `src/scpi_driver/`, `tests/`, `docs/`
- [ ] `pyproject.toml` with dependencies
- [ ] pytest installed, one trivial test passing
- [ ] ruff configured and clean
- [ ] mypy configured
- [ ] Pre-commit hook running ruff

### Phase 1 — SCPI parser and simulated instrument (10–14 h)
- [ ] Command tree: short/long form, case-insensitive
- [ ] Optional bracketed keywords resolve
- [ ] Leading colon, semicolon chaining
- [ ] Query vs command distinction
- [ ] Numeric parameters with suffixes
- [ ] MIN / MAX / DEF
- [ ] Boolean and discrete parameters
- [ ] Range checking pushes errors
- [ ] `*IDN?`, `*RST`, `*CLS`, `*TST?`
- [ ] Error queue with standard negative codes
- [ ] Noisy measurement values, NPLC affects noise
- [ ] Acquisition timing modelled
- [ ] TCP server on port 5025, partial reads handled
- [ ] **Milestone:** `telnet localhost 5025` → `*IDN?` answers

### Phase 2 — Driver (8–10 h)
- [ ] `Transport` protocol with socket and fake implementations
- [ ] Typed properties, not raw command strings
- [ ] Explicit timeouts on every read
- [ ] `SYST:ERR?` checked after writes
- [ ] Context manager
- [ ] Exception hierarchy
- [ ] DEBUG-level command logging

### Phase 3 — Testing and CI (6–8 h)
- [ ] Unit tests against the fake transport
- [ ] Integration tests over a real socket
- [ ] Failure-path tests: timeout, malformed response, errors, out-of-range
- [ ] Parametrised short/long form tests
- [ ] Coverage above 80%
- [ ] GitHub Actions: ruff + mypy + pytest
- [ ] Badge in README

### Phase 4 — Status system and synchronisation (6–8 h)
- [ ] Status Byte, `*STB?`
- [ ] Standard Event Status Register, `*ESR?`, `*ESE`, `*ESE?`
- [ ] Enable-register masking
- [ ] Questionable and Operation registers
- [ ] `*OPC?`, `*OPC`, `*WAI`
- [ ] Overlapped vs sequential documented per command
- [ ] **Test demonstrating a race condition, then fixed by `*OPC?`**

### Phase 5 — PyVISA integration (4–5 h)
- [ ] Driver works via PyVISA `TCPIP::...::SOCKET`
- [ ] Termination handling verified
- [ ] pyvisa-sim YAML definition of the instrument
- [ ] Backend switchable by config, not code

### Phase 6 — Measurement application (6–8 h)
- [ ] Sweep script with progress output
- [ ] pandas DataFrame, units in column names
- [ ] CSV with metadata header: `*IDN?`, settings, timestamp, git hash
- [ ] scipy fit with parameter uncertainties
- [ ] matplotlib figure, error bars, units on axes
- [ ] Allan deviation of a long constant recording
- [ ] Reproducible from one command

### Phase 7 — Documentation and polish (3–4 h)
- [ ] README: purpose, plot, quickstart, command reference table
- [ ] `docs/scpi-notes.md` — what I learned about the protocol
- [ ] Docstrings complete, `mypy --strict` passes
- [ ] `v1.0.0` tagged
- [ ] Commit history tidied

---

## Session log

Newest first. One entry per session: what I did, what I got stuck on, what I
learned. Keep it short but write the stuck parts down — they are the useful
record.

<!--
### YYYY-MM-DD — 2.5 h
Did:
Stuck on:
Learned:
Next:
-->

---

## Concepts I can explain from memory

Tick only when you could explain it on a whiteboard with no notes. This list
is the actual interview preparation.

- [ ] Why SCPI commands have short and long forms
- [ ] How the command tree resolves an incoming string
- [ ] What the error queue is for and why codes are negative
- [ ] The difference between condition, event and enable registers
- [ ] What `*OPC?` does and what breaks without it
- [ ] Overlapped vs sequential commands
- [ ] Why the transport is injectable and what that buys
- [ ] How the driver is tested with no instrument attached
- [ ] What VISA is and where PyVISA sits in the stack
- [ ] Why a data file needs a metadata header
- [ ] What Allan deviation measures and why variance is insufficient

---

## Open questions

Things I do not understand yet and should ask about or look up.

-
