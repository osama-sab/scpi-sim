# PROGRESS

Session state for this project. Update at the end of every working session.
Any AI assistant reads this first — keep it honest, including the parts that
are not going well.

---

## Current position

**Phase:** 1 - SCPI parser and simulated instrument
**Started:**  2026-09-03
**Last session:** 2026-09-22
**Hours invested so far:** ?

**Next concrete task:**
> Leading colon, semicolon chaining. Walk a full chained command
> (`SENS:VOLT:DC:NPLC 10`) by splitting on `:` and calling `resolve()` once
> per keyword, advancing to whatever node it returns each time. Decide how a
> leading `:` resets to root, and how `;` separates chained units. Nothing
> about nested optionals or ambiguity detection yet. `Node` now has both
> `children` and `parent`, and `current_path` will store the resolved
> `Node` itself (not the literal route) — the walker itself hasn't been
> started yet.

---

## Phase checklist

Full detail in `docs/BUILD_PLAN.md`. Tick only when committed and pushed.

### Phase 0 — Foundations (3–4 h)
- [x] `git init`, GitHub repo, `.gitignore`
- [x] Directory layout: `src/scpi_sim/`, `src/scpi_driver/`, `tests/`, `docs/`
- [x] `pyproject.toml` with dependencies
- [x] pytest installed, one trivial test passing
- [x] ruff configured and clean
- [x] mypy configured
- [x] Pre-commit hook running ruff

### Phase 1 — SCPI parser and simulated instrument (10–14 h)

Expanded 2026-09-09 after auditing `docs/BUILD_PLAN.md` against the actual
message syntax. Items marked ⁺ were not in the build plan at all; the plan was
written before I understood the protocol, so it named things at the wrong
granularity. Left the build plan alone — the gap between the two documents is an
honest record of what I learned.

**Command tree (1.1)**
- [x] Command tree: short/long form, case-insensitive
- [x] ⁺ Exactly two spellings per node — `VOLTAG` rejected. Not prefix matching
- [x] ⁺ Mnemonic validated when the tree is built (uppercase prefix is a real
      prefix, remainder lowercase, ≤ 12 chars)
- [x] Optional bracketed keywords resolve
- [ ] ⁺ Nested optional keywords resolve
- [ ] ⁺ Ambiguity detected at tree-build time, error naming both competing paths
- [ ] Leading colon, semicolon chaining
- [ ] ⁺ Current path carried across chained units, reset at the terminator
- [ ] ⁺ Current path is per-connection state, not module-level
- [ ] ⁺ Common commands (`*XYZ`) leave the current path untouched
- [ ] Query vs command distinction
- [ ] ⁺ Settable and queryable are independent flags — bare `SENS` is an error

**Message syntax (1.1b) — ⁺ absent from the build plan entirely**
- [ ] ⁺ Whitespace separates header from parameters; commas between parameters
- [ ] ⁺ Queries may carry parameters (`MEAS:VOLT:DC? 10,0.001`)
- [ ] ⁺ Response message is one line; multiple queries joined by `;`
- [ ] ⁺ Empty message unit (`;;`) rejected
- [ ] ⁺ Keyword numeric suffix (`CHANnel2`); absent suffix means 1

**Parameters (1.2)**
- [ ] Numeric parameters with suffixes
- [ ] MIN / MAX / DEF
- [ ] Boolean and discrete parameters
- [ ] Range checking pushes errors

**Common commands (1.3)**
- [ ] `*IDN?`, `*RST`, `*CLS`, `*TST?`

**Error queue (1.4)**
- [ ] Error queue with standard negative codes
- [ ] ⁺ Parser-generated codes: -101, -102, -103, -108, -110, -112, -114
      (the plan listed only -100, -113, -222, -224, -410, -350)
- [ ] ⁺ **Decide and document:** which code fires for a bare non-executable
      node — -113 or -100?
- [ ] ⁺ **Decide and document:** on a failed unit mid-message, are the remaining
      units discarded, and is the current path modified? (Look it up in
      IEEE 488.2, don't guess)

**Measurement and transport (1.5, 1.6)**
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

### 2026-09-14 — ? h
Did: Decided mnemonic validation lives in `__post_init__` and raises a
custom `InvalidMnemonicError(ValueError)`, so a future tree-builder can
catch this specific failure without swallowing unrelated `ValueError`s.
Implemented the three checks (prefix is a real uppercase prefix, remainder
is lowercase, length ≤ 12). Along the way, fixed an infinite-recursion bug
between `short()`/`long()` for mnemonics ≤ 4 characters, and simplified
`long()` to just `self.mnemonic.upper()` instead of reconstructing it from
`short()`.
Stuck on: My first attempt at the prefix/remainder checks scanned the whole
string collecting uppercase and lowercase characters into two buckets —
this checks a subsequence, not a real prefix, and doesn't test position at
all. Rewrote it to slice at `n = len(self.short())` instead, which is
position-based and reuses `short()`'s own boundary logic as the single
source of truth. That surfaced a bigger issue: `short()`/`long()` were
built assuming the caller passes a plain word and lets the vowel-length
heuristic find the abbreviation boundary, but validation assumes the
caller already writes the boundary into the mnemonic's casing (e.g.
`"VOLTage"`). Those are two different conventions — had to pick one
(casing is authoritative) and rewrite `test_short`/`test_long`'s fixtures
to match.
Learned: `str.isupper()`/`.islower()` both return `False` on an empty
string, which matters for ≤ 4-character mnemonics where the "remainder"
slice is `""`. Mutual recursion between two methods that each call the
other, with no state that ever changes between calls, doesn't loop forever
silently — it raises `RecursionError` once the stack depth limit is hit.
Next: Optional bracketed keywords resolve.

### 2026-09-16 — ? h
Did: Added `children` to `Node` and implemented `resolve(keyword)` — checks
this node's direct children first, then falls back to recursing into
children where `optional` is `True` (never required ones), so a keyword
behind an optional node resolves without being typed. Went through two
representations: `children: list["Node"]` first, then switched to
`children: dict[str, "Node"]` keyed by both `short()` and `long()` of each
child, once the list version's O(n) scan-and-compare felt like it was
fighting the data structure. Wrote `test_resolve`, covering a direct
short-form match, a direct long-form match, a miss, a match reached only
through an optional child, a required child correctly blocking the same
kind of skip, and the returned object being the real node (not a lookalike).
Stuck on: `resolve()` went through many broken versions before the shape was
right, and almost every bug was a variant of the same mistake — computing or
finding the right thing, then returning something *else* that happened to
also be a `Node`: the stale last-iterated loop variable, an empty sentinel
placeholder, a brand-new `Node(keyword)` reconstructed from raw input text
(which also silently re-ran mnemonic validation on protocol input and
crashed on real long-form keywords), the immediate intermediate child
instead of what its own recursive call found. Also hit `UnboundLocalError`
twice from a variable only assigned inside a loop's `if`, then read
unconditionally after the loop — same class of bug as an unfilled variable,
just a different shape than the mnemonic-validation typos from last time.
Learned: a frozen dataclass can't be used as a dict key once any of its
fields is a `list` or `dict` — `TypeError: unhashable type` — so `Node`
itself can never be a key, only ever a value. `mypy --strict` catches type
mismatches (like passing a `list` where a `dict` is expected) but not a
possibly-unbound local variable, and not a runtime crash from a
validly-typed-but-semantically-wrong value (like `Node(keyword)` blowing up
inside its own `__post_init__`) — those only ever showed up by actually
running the code.
Next: Leading colon, semicolon chaining.

### 2026-09-22 — ? h
Did: Resolved the "position vs route" question left open in `ch05` of my
revision notes — `current_path` will store the resolved `Node` itself, not
the literal header text, since `resolve()` already returns `Node`s and two
different spellings reaching the same command should leave identical state.
That meant `Node` needed to track its own `parent` (rule 5: after a unit
resolves, the path becomes the parent of what it resolved to). Hit the
circularity my own `ch03` notes predicted — a child must exist before its
parent, so it can't know its parent at construction time — and resolved it
by dropping `frozen=True` rather than fighting it with `object.__setattr__`.
`parent` is `init=False` (only a parent's own wiring can set it) and
excluded from `__eq__`/`repr` (`compare=False`, `repr=False`). Wired it in
`__post_init__`, in two passes: the first only checks whether a child
already belongs to a different parent and raises the new
`DuplicateParentError(ValueError)`, the second only assigns — so a rejected
construction can't leave earlier children in the same loop half-wired to a
parent that never finished being built.
Stuck on: my first version of the check combined looking and assigning in
one loop, so a raise partway through could leave an *earlier*, perfectly
valid child pointing at a parent that was ultimately rejected — confirmed by
building exactly that case by hand before splitting the loop. Also wrote the
comparison as `!=` before catching myself — dataclass equality compares
data, not identity, so two structurally-equal-but-different parent objects
would have passed silently; needs `is not`. Chained calls like
`ac.resolve(keyword).parent` kept failing `mypy --strict` even after the
logic was right, since `resolve()` returns `Node | None` and mypy can't
narrow a call it hasn't seen assigned to a name — fixed by capturing the
result first and asserting it isn't `None` before using it.
Learned: giving a dataclass a back-reference field without `compare=False`
makes `==` between two structurally identical trees raise `RecursionError`
— the generated `__eq__` walks into `parent`, which walks back into
`children`, which contains the node you started from. Confirmed directly by
triggering it. `field(init=False)` only removes a field from the generated
`__init__`; on a non-frozen class it does nothing to stop a plain
`node.parent = x` afterwards — the two are unrelated protections.
Next: the colon/semicolon-chaining walker itself — `Node` now has what it
needs, but nothing has been written for it yet.

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
