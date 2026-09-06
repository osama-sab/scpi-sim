# SCPI Instrument Simulator + Driver — Build Plan

A staged project that teaches SCPI properly and produces a repository a
test-and-measurement employer can evaluate in two minutes.

Everything here runs with no hardware. That is deliberate: hardware-free
testing is how instrument drivers are actually developed in industry, and it
is the single strongest signal in the finished repo.

**Total: 35–50 hours across 6 phases.** Each phase ends with something that
runs and can be committed.

---

## What you are building

Two halves that talk to each other over a TCP socket:

1. **`scpi-sim`** — a simulated bench instrument. A server that accepts SCPI
   commands and behaves like a real device: hierarchical command tree, error
   queue, status registers, realistic timing, plausible noisy data.
2. **`scpi-driver`** — the host-side Python driver that controls it, written
   the way a production instrument driver is written.

The simulator matters as much as the driver. Writing the device side is what
forces you to actually learn the protocol rather than copy command strings out
of a manual.

---

## Phase 0 — Foundations (3–4 h)

Before any instrument code.

- [ ] `git init`, repo on GitHub, sensible `.gitignore`
- [ ] Project layout: `src/scpi_sim/`, `src/scpi_driver/`, `tests/`, `docs/`
- [ ] `pyproject.toml` with dependencies (use `uv` — fast and current)
- [ ] `pytest` installed, one trivial test passing
- [ ] `ruff` for linting, `mypy` for type checking, both configured
- [ ] Pre-commit hook running ruff

**Why it matters:** a reviewer opens your repo and sees whether it is a folder
of scripts or a project. This phase alone separates you from most student
repositories.

**Do not skip the type hints.** Physics students write untyped Python;
industry will not accept it, and `mypy` passing is a visible, checkable claim.

---

## Phase 1 — The SCPI parser and simulated instrument (10–14 h)

Model a **digital multimeter**. It is the simplest instrument with enough
surface to be interesting, and the command set is well documented in any
Keysight 34461A or Rigol DM3068 programming manual — read one, they are free.

### 1.1 The command tree

SCPI commands are hierarchical and colon-separated, with **short and long
forms** that must both be accepted:

```
MEASure:VOLTage:DC?     ->  also valid as  MEAS:VOLT:DC?
CONFigure:CURRent:AC    ->  also valid as  CONF:CURR:AC
[SENSe:]VOLTage:DC:NPLCycles     <- brackets mean optional keyword
```

Implement a tree where each node knows its long form and its short form, and
resolve an incoming command by walking it. This is the core exercise.

- [ ] Node class with long/short form matching, case-insensitive
- [ ] Optional (bracketed) keywords resolve correctly
- [ ] Leading colon resets to root; semicolon chains commands
- [ ] Query (`?`) vs command distinction

### 1.2 Parameter types

- [ ] Numeric with suffix: `1000`, `1E3`, `1KHZ`, `100MV`
- [ ] `MIN` / `MAX` / `DEF` keywords resolve to actual limits
- [ ] Boolean: `ON` / `OFF` / `1` / `0`
- [ ] Discrete: `IMMediate` / `EXTernal` / `BUS`
- [ ] Range checking that pushes an error rather than crashing

### 1.3 IEEE 488.2 common commands

These start with `*` and every instrument has them:

- [ ] `*IDN?` — manufacturer, model, serial, firmware version
- [ ] `*RST` — reset to a documented default state
- [ ] `*CLS` — clear status and error queue
- [ ] `*TST?` — self-test, returns 0 on pass

### 1.4 The error queue

- [ ] FIFO queue, `SYST:ERR?` pops one entry
- [ ] Returns `0,"No error"` when empty
- [ ] Use the **standard negative codes**: `-100` command error,
      `-113` undefined header, `-222` data out of range,
      `-224` illegal parameter value, `-410` query interrupted
- [ ] Queue overflow pushes `-350,"Queue overflow"`

### 1.5 Measurement behaviour

- [ ] Return plausible noisy values, not constants — a DC reading should have
      noise that shrinks as integration time (NPLC) increases
- [ ] Model acquisition time: a slow reading actually takes longer to answer
- [ ] Support a configurable "device under test" so tests are deterministic

### 1.6 Transport

- [ ] TCP socket server, one client, newline-terminated
- [ ] Handle partial reads and multiple commands in one packet
- [ ] Clean shutdown

**Deliverable:** you can `telnet localhost 5025`, type `*IDN?`, and get an
answer. Port 5025 is the SCPI-over-TCP convention — use it.

---

## Phase 2 — The driver (8–10 h)

- [ ] `Transport` protocol (abstract interface), with `SocketTransport` and
      `FakeTransport` implementations
- [ ] Driver class with **typed properties**, not raw strings scattered around:
      `dmm.nplc = 10` rather than `dmm.write("VOLT:DC:NPLC 10")`
- [ ] Explicit timeouts everywhere, no unbounded reads
- [ ] `SYST:ERR?` checked after every write, raising a typed exception
- [ ] Context manager (`with DMM(...) as dmm:`) that resets and closes cleanly
- [ ] Custom exception hierarchy: `InstrumentError`, `CommandError`,
      `TimeoutError`
- [ ] Logging of every command sent and received, at DEBUG level

**The one thing reviewers look for:** that the transport is injectable. It is
what makes the whole thing testable, and it is the difference between a script
and a driver.

---

## Phase 3 — Testing and CI (6–8 h)

This is the phase that most distinguishes you. Do not shorten it.

- [ ] Unit tests against `FakeTransport` — no socket, no device
- [ ] Integration tests that start the simulator in a fixture and talk to it
      over a real socket
- [ ] Test the failure paths, not just the happy ones: timeout, malformed
      response, error-queue entries, out-of-range parameters
- [ ] Parametrised tests over the short/long form pairs
- [ ] Coverage report, aim above 80%
- [ ] **GitHub Actions** workflow: on every push, run ruff + mypy + pytest
- [ ] Green badge in the README

**CV line this earns:** "Testabdeckung >80 %, CI-Pipeline ohne
Hardware-Abhängigkeit." Say that in an interview at a T&M company and you will
be asked to elaborate, which is exactly what you want.

---

## Phase 4 — Status system and synchronisation (6–8 h)

This is the phase almost nobody does, and it is what signals real depth.

### 4.1 Status registers

IEEE 488.2 defines a register model. Implement it:

- [ ] **Status Byte (STB)** — `*STB?`, with the summary bits
- [ ] **Standard Event Status Register (ESR)** — `*ESR?`, `*ESE`, `*ESE?`
- [ ] Enable-register masking: only enabled bits propagate to the summary
- [ ] SCPI **Questionable** and **Operation** status registers with their
      condition / event / enable structure

### 4.2 Synchronisation

- [ ] `*OPC?` — blocks until pending operations complete, returns 1
- [ ] `*OPC` — sets the OPC bit in ESR when operations complete
- [ ] `*WAI` — sequential execution barrier
- [ ] Distinguish **overlapped** from **sequential** commands, and document
      which of your commands are which

### 4.3 The failure mode worth demonstrating

Write a test that shows what goes wrong *without* proper synchronisation: fire
a slow acquisition, immediately query the result, get stale data or a timeout.
Then show `*OPC?` fixing it.

That test is a talking point. It proves you understand instrument control as a
concurrency problem, not just string passing.

---

## Phase 5 — PyVISA integration (4–5 h)

Now connect it to the tools the industry actually uses.

- [ ] Drive your simulator through **PyVISA** using a `TCPIP::...::SOCKET`
      resource string, changing nothing on the device side
- [ ] Verify `read_termination` / `write_termination` handling
- [ ] Write a **`pyvisa-sim` YAML** definition of your instrument, so the
      driver can also run against `pyvisa-sim` with no server at all
- [ ] Document how to point the driver at: your simulator, pyvisa-sim, or a
      real instrument — one config change, no code change

**Why:** "PyVISA" and "pyvisa-sim" on a CV are searchable keywords that a T&M
recruiter recognises immediately. Every posting we looked at at NXP and ESYLUX
implies this stack.

---

## Phase 6 — A real measurement application (6–8 h)

The driver is infrastructure. Now use it, which also closes your stated
numpy/pandas/scipy gaps in a context where they mean something.

- [ ] A sweep script: vary a parameter, record readings, with progress output
- [ ] Store results in a **pandas** DataFrame with proper units in the column
      names
- [ ] Save to CSV **with a metadata header**: instrument `*IDN?`, all settings,
      timestamp, driver version, git commit hash
- [ ] **scipy** fit to the data with uncertainty estimates on the parameters
- [ ] **matplotlib** figure with error bars and axis labels including units
- [ ] Allan deviation of a long constant-value recording — the standard
      stability metric in metrology, and a strong thing to have on a CV
- [ ] Everything reproducible from a single command

**The metadata header is the detail that marks you as a measurement person
rather than a programmer.** A data file you cannot trace back to instrument
settings is not a measurement.

---

## Phase 7 — Documentation and polish (3–4 h)

- [ ] README: what it is, why it exists, a screenshot or plot, quickstart,
      the full command reference table
- [ ] A short `docs/scpi-notes.md` explaining what you learned about the
      protocol — the command tree, the status model, synchronisation
- [ ] Docstrings on public API, `mypy --strict` passing
- [ ] Tag a `v1.0.0` release
- [ ] Clean up the commit history: meaningful messages, no "fix" x20

---

## The CV entry

Under **Projekte**, above your education section:

> **scpi-sim** — Simulator und Treiber für SCPI-gesteuerte Messgeräte
> *Python, pytest, PyVISA, GitHub Actions* — [github.com/…]
> Vollständige Implementierung des SCPI-Kommandobaums (Kurz-/Langform,
> Parametertypen, Fehlerqueue) und des IEEE-488.2-Statusregistermodells
> inklusive `*OPC`-Synchronisation. Treiber mit austauschbarer
> Transportschicht, dadurch vollständig hardwarefrei testbar; CI-Pipeline mit
> >80 % Testabdeckung. Messanwendung mit pandas/scipy, rückverfolgbaren
> Metadaten und Allan-Abweichungs-Analyse.

---

## The eight things that actually make you a better candidate

Ranked by how much each moves a T&M hiring decision:

1. **Hardware-free testability.** Injectable transport, fake device, green CI.
   Almost no student applicant has this. It is the whole differentiator.
2. **Protocol literacy.** You can explain the SCPI command tree, error queue
   and status registers from memory. Most applicants have only *used* an
   instrument.
3. **Synchronisation understanding.** Knowing why `*OPC?` exists means you
   understand instrument control as a timing problem.
4. **PyVISA fluency.** The keyword that maps your project onto their stack.
5. **Traceable data.** Metadata headers, versioning, reproducibility.
6. **Code quality signals.** Type hints, mypy, ruff, docstrings, tests.
7. **Git history.** Incremental commits over weeks prove follow-through —
   which, given your own diagnosis, is the trait you most need to demonstrate.
8. **Written explanation.** The `scpi-notes.md` doubles as proof you can
   document, which every one of these job postings asks for.

---

## Schedule

At 6–8 h/week this is 6 weeks. At 12 h/week, 3–4 weeks.

| Week | Phase | Commit at the end of it |
|---|---|---|
| 1 | 0 + start 1 | Repo skeleton, CI running, parser started |
| 2 | Finish 1 | Simulator answers `*IDN?` over telnet |
| 3 | 2 | Driver controls the simulator |
| 4 | 3 | Green CI badge, >80% coverage |
| 5 | 4 + 5 | Status registers, PyVISA working |
| 6 | 6 + 7 | Measurement app, README, v1.0.0 |

**Commit every session, even unfinished work.** The visible history is part of
the deliverable.

---

## Reference material

- Any Keysight or Rigol **programming manual** (free PDF) — the real command
  reference. Keysight 34461A for a DMM, Rigol DS1000Z for a scope.
- **IEEE 488.2** common command definitions — summarised in every one of those
  manuals.
- **SCPI-99 specification** — the standard itself, for the command tree and
  status model.
- **PyVISA** and **pyvisa-sim** documentation.
- **PyMeasure** source on GitHub — read how they structure instrument classes,
  then decide what to copy and what to do differently.

---

## After this project

The natural next step is a **PyMeasure pull request**: write a driver for a
real instrument against its manual, tested with pyvisa-sim. Your simulator work
makes that straightforward, and a merged PR into an established open-source
instrument-control library is a stronger credential than anything else
available to you without a job.
