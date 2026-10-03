# PROGRESS

Session state for this project. Update at the end of every working session.
Any AI assistant reads this first — keep it honest, including the parts that
are not going well.

---

## Current position

**Phase:** 1 - SCPI parser and simulated instrument
**Started:**  2026-09-03
**Last session:** 2026-10-03
**Hours invested so far:** 27

**Next concrete task:**
> Nested optional keywords resolve: a keyword below an optional node that is
> itself inside another optional node — `[A:][B:]C`, reached by typing just
> `C`. `resolve()` already recurses into optional children, so it may already
> work — write the test first and let it decide whether any code changes.

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
- [x] Leading colon, semicolon chaining
- [x] ⁺ Current path carried across chained units, reset at the terminator
- [ ] ⁺ Current path is per-connection state, not module-level
- [ ] ⁺ Common commands (`*XYZ`) leave the current path untouched
- [ ] Query vs command distinction
- [ ] ⁺ Settable and queryable are independent flags — bare `SENS` is an error

**Message syntax (1.1b) — ⁺ absent from the build plan entirely**
- [ ] ⁺ Whitespace separates header from parameters; commas between parameters
- [x] ⁺ Queries may carry parameters (`MEAS:VOLT:DC? 10,0.001`)
- [ ] ⁺ Response message is one line; multiple queries joined by `;`
- [x] ⁺ Empty message unit (`;;`) rejected
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

### 2026-09-24 — 2 h (across 23 and 24 September)
Did: Wrote `walk(root, current, header)` in `parser.py`: split the header on
`:`, treat an empty first element as a leading colon (start from root), then
resolve one keyword per step. It now returns `(landed, path)` — where the
header lands, and the path for the next unit. Moved its tests into
`tests/test_parser.py` and rewrote them as two `pytest.mark.parametrize`
tables (headers that resolve, headers that fail), 15 named rows.
Decided: `current_path` follows the **route**, not the position. I had first
chosen position (the path is the parent of the resolved node), thinking what
real instruments do couldn't be known without hardware. Then I read SCPI-99
§6.2.4: "Default nodes in the tree shall not alter the header path of the
parser", with `DISP ON;DATA` given as an example that must fail. Why comply
instead of documenting a deviation: the simulator exists so a driver tested
against it behaves the same on a real instrument. Position disagreed with the
standard in both directions — tried against my own tree, `VOLT;FUNC` raised an
error no real instrument would, and `DISP ON;DATA` would be accepted where the
standard says it must fail. "My parser follows SCPI-99 §6.2.4" is also a
stronger interview answer than "I deviated". Implemented without storing
text: `path` is the node the loop stood on just before its last step.
Stuck on: the walker kept picking up `resolve()`'s shape — recursion, calling
`walk` again with the whole header, then a `return` indented inside the loop
so it stopped after one keyword. For the path I tried `current.parent`
(position again), `result[-2]` (a keyword string, not a node, and an
`IndexError` on one-keyword headers), and re-walking a shortened header
string (wrong start for relative headers, and collides with my own
""→None rule). Also changed the parser once to accept the root's name as a
keyword so a wrong test would pass — the test was wrong, not the code.
Learned: check the standard before calling a question open — Chapter 5 of my
notes had said to look it up. A function that needs to hand back two things
returns a tuple. `pytest.mark.parametrize` turns nine near-identical tests
into two tables where a new case is one line. The Keysight Truevolt guide
backs up the route (`TRIG:SOUR EXT;COUNT 10` equals `TRIG:COUNT 10`), keeps a
20-entry FIFO error queue per interface, and — like SCPI-99 — doesn't say
whether units after a failed one still run.
Next: the `;` loop.

### 2026-09-25 — 1 h
Did: Wrote `walk_message(root, message)`: split on `;`, strip whitespace
around each unit, walk it from the current path, and carry each unit's route
into the next. Chose provisional behaviours for the two questions no free
source answers — a failed unit ends the message (the list stops at its
`None`), and a trailing `;` is an error — and wrote both into the docstring
and the tests. Gave `walk()`'s `path` a starting value and added the
single-keyword rows. Test tables now cover gotcha one, the route at message
level, stopping at the first failure, whitespace after `;`, whitespace inside
a header, a trailing newline, and an empty message.
Stuck on: a test tree that reused one `NPLCycles` node under both `AC` and
`DC` — `DuplicateParentError` was right; two commands with the same name are
two nodes. `all(...)` without `assert` in front, so tests checked nothing and
passed while three expectations were wrong. `==` on node lists can't tell the
`AC` branch's `RANGe` from the `DC` branch's (same data), so the checks use
`is`, element by element, with `zip(..., strict=True)`. `replace(" ", "")`
also deleted spaces inside headers and would have glued `COUN 1` into
`COUN1`; `strip()` only touches the ends.
Learned: when choosing how strict to be without a spec, err toward stricter
than real hardware — a false alarm on the simulator is harmless, a missed one
fails on the bench. A test is only worth something if it can fail: checked
that the table catches both a wrong branch and a wrong length.
Next: split units into header, `?` and parameters.

### 2026-09-26 — 1 h (entry written 2026-10-02)
Did: Wrote `split_unit(unit)`, returning `(header, is_query, parameter_text)`
or `None`. The header ends at the first whitespace (`split(maxsplit=1)`), the
parameter text keeps its inner spaces, and a `?` counts only at the end of
the header. Kept it separate from `walk`: splitting a unit is message syntax,
resolving a header is the command tree. 14-row table.
Stuck on: the first version rejected units with no parameters, and the test
encoded the same bug; it also took only the second word as the parameter,
split on spaces only (no tabs), searched the whole unit for `?` (so
`DISP:TEXT "Ready?"` became a query), and crashed on an empty unit.
Learned: `split()` with no argument splits on any whitespace and drops empty
pieces; `split(" ")` does neither. A test written from the code's current
output can lock a bug in.
Next: wire `split_unit` into `walk_message`.

### 2026-10-02 — 1 h
Did: Wired `split_unit` into `walk_message`, which now returns
`list[ParsedUnit | None]`. `ParsedUnit` is a small dataclass with `node`,
`is_query` and `parameters`, chosen over a tuple so callers write
`unit.is_query` rather than `unit[1]`, with room for parsed values later.
Only the header goes to `walk`; `current_path` stays a local variable,
because it's parser state, not part of any unit's result. Rewrote the
`walk_message` table to expect `ParsedUnit`s and compare field by field,
then added rows that need the new fields: a query with parameters, a query
on the second unit (`RANG 10;NPLC?`), `VOLT?:DC` mid-message, and `;;`.
Checked they can fail: forcing the query flag to `False`, emptying the
parameters, and re-introducing both of today's `None`-handling bugs each turn
at least one row red.
Stuck on: first wrote the dataclass with the call-site values in the
`class` line (defining and constructing at once). Then a `None` from
`split_unit` was silently skipped, so `VOLT?:DC;MEAS` still ran `MEAS`; then
`.node` was appended instead of the unit so the *old* tests passed while
mypy failed; then an extra `res != ""` branch duplicated a failure
`split_unit` already handled. In the test: `is` between a `ParsedUnit` the
test built and one the parser built (always `False`: different objects), and
a conversion loop that dropped `None`s, so the lengths stopped matching.
Learned: `is` asks "same object in memory" — right for the node, wrong for
anything freshly built; everything else compares with `==`. A dataclass's
generated `==` compares fields with `==`, so it can't tell `AC:RANGe` from
`DC:RANGe`. When a return type changes, red old tests are the signal to
update the tests; bending the code back to fit them is the `"ROOT:"` mistake
again. Many failing rows: group them by error type first — each type was one
cause. Handle each failure once, first, and return early. A failing input
placed alone can hide a bug: `VOLT?:DC` on its own gives `[None]` whether or
not the loop stops, so it belongs mid-message.
Next: query vs command distinction, using `queryable` and `settable`.

### 2026-10-03 — 4 h (across 2 and 3 October)
Did: Query vs command distinction. Read SCPI-99 first: §6.2.3 (p. 29) says
both forms exist unless a node is marked `[query only]` or `[no query]`, and
p. 136 marks `MEASure:<function>?` query only (`CONFigure` is the command
twin). So `Node`'s `settable`/`queryable` now default to `True`, and every
pure path node (`SENSe`, `VOLTage`, `MEASure`, the root) is flagged
explicitly as neither — "has children" can't be used to infer it
(`DISP ON` is valid). Added a command-only `CLEar` under `SENSe` so the test
tree covers all four flag combinations. Wrote `helper_parser(node,
is_query)`: the query flag picks which flag decides — the two-term minimal
DNF, i.e. a 2:1 multiplexer. `walk_message` calls it after `walk`; a
disallowed form adds `None` and ends the message, the same as the other two
failures. Tested the helper alone with the full 8-row truth table (each row
builds its own node), plus message rows for a query on a command-only node,
bare `SENS`, and a rejected form mid-message with the earlier unit kept.
Decided: a bad form returns `None`, not an exception. A client's bad command
is input to report, not a reason to crash the server — and raising would
discard the units already parsed in the message. Exceptions stay for bugs in
the tree itself (`InvalidMnemonicError`, `DuplicateParentError`).
Stuck on: first claimed `MEAS:VOLT:DC` has a command form — p. 136 says
query only. First rule was "`queryable` must equal the query flag", which
rejects `NPLC 10` on a node allowing both; then answered every command row
of the truth table "yes" (only checking queries). Flagged the two `MEAS`
nodes backwards and changed `MEAS:VOLT:DC? 10,0.001` to expect `None` to
match — the test-bending mistake a third time. The first helper was the
truth table as a dict, which would have made the test a copy of the code.
`test_helper` took four attempts: a `return` instead of an `assert`, a `for`
loop inside a parametrized test, and rows describing each case twice (a tree
node and a key) that already disagreed on one row. Several failure rows
failed at the wrong stage — `VOLT:CLE?` (no `CLE` under `VOLT`), a `?`
mid-header, and `SENS:CLE?` resolved relative to `DC` (gotcha one in my own
test) — so they never reached the new check.
Learned: which node allows which form is data about one instrument, not a
parser rule — it lives on the tree, the rule lives in the helper. Code the
rule, test it against the table; a test that copies the implementation
can't catch its mistakes. `parametrize` already is the loop: one row, one
run. A failure row must fail at the stage it's named for — check by
breaking that stage on purpose (helper forced to `True`: exactly the three
new rows went red). When a change breaks a row's first unit, the row may
silently stop testing what it's named for (`gotcha_one`,
`route_at_message_level`).
Next: nested optional keywords.

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

- After a unit fails with `-113`, do the later units in the same message still
  run? SCPI-99 §6.2.4 only says *earlier* units may take effect, and defers
  compound headers to IEEE 488.2 §7.6.1.5 (paid). Check the Keysight 34461A
  programming manual's error-handling section next. The Keysight Truevolt
  guide (pp. 194–196, 459–461) doesn't say either. Provisional choice: the
  message stops at the failed unit.
- Is a trailing `;` before the terminator (`MEAS:VOLT:AC:RANG;`) legal? Not
  covered by SCPI-99 Volume 1 or the Keysight guide; it's in IEEE 488.2's
  message grammar. Provisional choice: an error, because a simulator should be
  at least as strict as real hardware.
- A `;` inside a quoted string parameter (`DISP:TEXT "a;b"`) splits the
  message there, because `walk_message` splits on `;` before anything knows
  about quotes. Fix belongs with parameter parsing; documented in the
  `walk_message` docstring as a known limitation until then.
- Trailing defaults: SCPI's `[SOURce:]VOLTage[:LEVel][:IMMediate][:AMPLitude]`
  means `VOLT 5` reaches `AMPLitude` by continuing *past* the last typed
  keyword through optional children. `walk` stops at the last typed keyword,
  and `resolve()` only skips optional nodes *before* a keyword. Not on the
  checklist yet — decide whether the simulator's tree needs it.
- Which error code fires for a form the node doesn't allow (`CLE?`,
  `MEAS:VOLT:DC 10`)? Look it up in SCPI-99 §21.8.9 (PDF pp. 519–521) and the
  Keysight error list (p. 461) before the error queue replaces the `None`.
