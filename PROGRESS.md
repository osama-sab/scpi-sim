# PROGRESS

Session state for this project. Update at the end of every working session.
Any AI assistant reads this first — keep it honest, including the parts that
are not going well.

---

## Current position

**Phase:** 1 - SCPI parser and simulated instrument
**Started:**  2026-09-03
**Last session:** 2026-10-19
**Hours invested so far:** 50

**Next concrete task:**
> 1.1b: commas between parameters — split a unit's parameter text into
> separate parameters (the whitespace half of that item is already done by
> `split_unit`). Read how SCPI-99 and IEEE 488.2 define the separator between
> program data first, then write the test plan (rows, and what each one
> catches) before any code.

---

## Phase checklist

Full detail in `docs/BUILD_PLAN.md`. Tick an item in the same commit that
finishes it, so the tick and the code reach GitHub together — never for
uncommitted work.

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
- [x] ⁺ Nested optional keywords resolve
- [x] ⁺ Ambiguity detected at tree-build time (same level, and through
      default nodes at any depth — SCPI-99 p. 25)
- [x] ⁺ Ambiguity error names both competing paths
- [x] Leading colon, semicolon chaining
- [x] ⁺ Current path carried across chained units, reset at the terminator
- [x] ⁺ Current path is per-connection state, not module-level
- [x] ⁺ Common commands (`*XYZ`) leave the current path untouched
- [x] Query vs command distinction
- [x] ⁺ Settable and queryable are independent flags — bare `SENS` is an error

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

### 2026-10-07 — 1 h
Did: Nested optional keywords (`[A:][B:]C` reached by typing `C`). Wrote the
test first; it passed with no code change — `resolve()`'s recursion into
optional children (16 September) already handles any depth. Positive table
on a module-level tree: both optional nodes typed, each skipped alone, both
skipped, with the path checked on every row (`LEAF` alone leaves it at the
start — SCPI-99 §6.2.4 holds through two levels). Negative table: the same
tree with exactly one node made required, and a header that skips that
node, so `walk` must return `None`.
Stuck on: the first single row unpacked `walk`'s result without the `None`
check (mypy) and never checked the path. Then tried one table for positive
and negative rows: the rows named nodes that the test only builds later, so
the whole file failed with `NameError` at import — `parametrize` rows are
evaluated when the module loads. Split into two tests. The first negative
version typed the required node and asserted success, so it was a positive
test; a `resolve()` that ignored `optional` entirely passed every row.
Learned: a test that passes for a broken implementation proves nothing —
negative rows are what pin the `optional` flag down. Build them as a
controlled experiment: change exactly one flag from a passing case, so only
that flag can explain the failure. Checked by running a `resolve()` that
ignores `optional`: both negative rows went red, every positive row stayed
green. Writing the test first is worth it even when no code changes: it
turned "probably works" into a recorded fact.
Next: ambiguity detected at tree-build time.

### 2026-10-09 — 2 h (across 8 and 9 October)
Did: Read SCPI-99 on ambiguity first. §6.2.2 (p. 25): a mnemonic must not
collide with another "at the same level, or one level different where a
default node exists"; p. 26: nodes below a default are "promoted by one
level". Its example, `JSTart`/`JSTop`, is forbidden (both short forms are
`JST`); `TIME`/`TIMer` is allowed. That exposed a problem in my own design:
with `children` built by hand as a dict, a second `JST` key silently
overwrites the first before `Node` ever sees it. So step A, a refactor:
`children` is now a list, and `Node` builds `_lookup` (spelling → child) in
`__post_init__`, after all checks. `resolve()` now does its direct match
with one `.get()` instead of a loop. Converted every test tree; no
expectation changed. Added `AmbiguousPathError` (raised later, in step B —
a colliding tree is a bug in the simulator, so it raises, like
`InvalidMnemonicError`).
Stuck on: removed the quotes from `list["Node"]` — `NameError`, because
inside its own class body `Node` doesn't exist yet on Python 3.12/3.13.
`default=None` and then `default_factory=list` on a dict field. Filled the
lookup by *replacing* the dict each pass, so only the last child survived.
`resolve()` took five attempts: a loop that never used the keyword (every
input, even `banana`, returned the last child), a lowercase lookup into
uppercase keys, `.get()` called twice, an `UnboundLocalError` on a miss,
and a bare `return`. Then, while merging loops, folded the check loop into
the assign loop — the single-loop design rejected on 22 September.
Learned: a dict is asked one question by key, not scanned. Adding to a dict
and replacing it are different operations. A quoted annotation is a
forward reference. The order of children in a list can be the whole point
of a test: the conversion had put the owned child first, so `test_parent`
no longer exercised the half-wiring case, and it never asserted the free
child's state anyway. With the order restored and that assertion added, it
caught the merged-loop regression immediately — and a deliberately
single-loop `__post_init__` now fails it.
Next: step B, the must-raise rows for `AmbiguousPathError`.

### 2026-10-10 — 7 h (across 9 and 10 October)
Did: Step B, the ambiguity check. Same level first: pass 1 records every
child's spellings in a local `seen` dict and raises `AmbiguousPathError`
when a short form is already claimed (`JSTart`/`JSTop`, `AMP`/`AMPere`,
`VOLT`/`VOLTage`; `TIME`/`TIMer` allowed). Then promotion: a new recursive
`typeable_from_parent()` returns a child plus everything promoted up through
it while it's optional, stopping at required nodes, and pass 1 checks every
node in that list. `seen` is local and only for checking; `_lookup` holds
direct children only. Added `DuplicateChildError` for the same object listed
twice, told apart from ambiguity with `is`. Tests in `test_tree.py`: the two
same-level tables (rows are mnemonics, nodes built in the test) and one
function per promotion scenario — direct vs promoted, two optional
siblings, two defaults deep, `JSTart` vs a promoted `JSTop`, `[TREE]`
containing `TREE`, promotion stopping at a required node, the same name
under required siblings, duplicate child — each asserting the children are
still unadopted after a failed build.
Stuck on: visualising promotion. Tried to look *up* from the child, which
can't work: children are built first, so only the parent can see both
sides. The picture that worked: remove an optional node's box and its
children slide up beside their aunts and uncles — then it's a same-level
check. The check went into the assigning loop twice (half-wiring again),
first read `self._lookup` while it was still empty, and once used
`resolve()`, which only finds the first match and depended on `_lookup`
being empty. The recursion took five attempts: no recursion, result
discarded, `append` + `extend` (duplicate node), `self` moved last, `self`
removed (no base case). Test rows first shared module-level nodes that each
row adopted; the duplicate-child check sat after the general raise and used
`list.count()` (`==`).
Learned: the parent is the first node that can see a collision. An optional
node's children count as its siblings. `append` adds one element, `extend`
adds each element; a recursion needs a base case. Check everything before
changing anything — every check, and with its own scratch dict. Test the
special case before the general one. `parametrize` when rows differ in
values, separate functions when they differ in shape; rows hold plain
values. Every same-level collision is a short-form collision, so checking
`short()` against a lookup of both spellings is complete.
Next: name both competing paths in the error message.

### 2026-10-13 — 7 h (across 12 and 13 October)
Did: `Node.path()` — the header path to a node in SCPI notation, walking up
the parent chain: optional nodes bracketed with their colon inside, so
dropping the brackets still leaves a valid header (`[SENSe:]VOLTage`,
`VOLTage[:DC]:NPLCycles`). `AmbiguousPathError` now prints both claimants
with it: `'LEAF' under ORIGin would match both LEAF and
[OUTer:][INNer:]LEAF`. Chose SCPI's own notation over plain `[X]` brackets,
because every instrument manual uses it. Tests: a `parametrize` table of
straight chains (rows are `(mnemonic, optional)` pairs, built bottom-up in
the test) covering every position of an optional node and both single-node
paths; two equal `RANGe` nodes getting different paths; and the message
checked with `pytest.raises(match=re.escape(...))` in both children orders.
Ran a mutation check myself: breaking the "lone optional node" branch turns
exactly `single-optional` red.
Stuck on: the first `path()` looped over the *letters* of the mnemonic, with
`if self.matches(...)` always true (a non-empty list is truthy). Then a
trailing colon, and mypy inferring `current = self` as `Node`, so
`current.parent` didn't fit and `return` became "unreachable". Only one side
of the message used `path()`, so reversing the children printed `LEAF and
LEAF`. The SCPI notation took several attempts: reversing the list but still
prepending, overwriting the path on the last node, `while` where `if` was
meant (an endless loop), reading past the end of the list, and deciding each
piece from its neighbours — until it became a four-row table driven by one
flag, "has a required node appeared yet?". In the tests: a one-element
tuple written without its comma, and module-level nodes shared by
`parametrize` rows again.
Learned: when nested `if`s start contradicting each other, the decision is
being made from the wrong facts — write it as a table. mypy types a variable
from its first assignment; annotate it wider up front. `(x)` is not a tuple,
`(x,)` is. `match=` reads a regular expression, so `re.escape` the expected
text. A mutation check — break one line on purpose, see which test notices —
is how to know a row actually guards something.
Next: common commands leave the current path untouched.

### 2026-10-17 — 3 h
Did: Common commands leave the current path untouched. `walk_message` takes a
third parameter, `common_commands: dict[str, Node]`. A header starting with
`*` is upper-cased and looked up there instead of walked through the tree,
and `current_path` isn't touched; a miss adds `None` and ends the message
like every other failure. `test_walk_message` passes `{}`. New
`test_common_commands`: in `VOLT:DC 10;*CLS;AC`, `AC` must still land under
`VOLTage`. Docstring (written by Claude) documents the key rule.
Decided: common commands live outside the tree — IEEE 488.2 defines them as a
flat set, separate from the SCPI hierarchy. Rejected a container `Node`,
because it would give them a parent. The dict is passed in next to `root`,
not kept as a module-level registry in `tree.py`: a global would leak
between tests and couldn't hold two instrument models with different
optional commands (`*TRG`, `*SAV`) — the same reason the current path must
be per-connection. No default: only one existing call needed updating, and
a default `{}` is created once and shared by every call (ruff B006). Keys
are upper-case and include the `*`; documented, not enforced.
Stuck on: the first version stripped the `*` and walked the rest through the
instrument tree — that was option B, not the A I had chosen — so
`*MEAS:VOLT:AC:RANG` and `*CLE` (through optional `SENSe`) were accepted and
the real `*CLS` wasn't. `header[0]` crashed on the empty header `split_unit`
returns for a lone `?`. An `elif` with no `else` left `landed` stale from
the previous unit (`NPLC*` accepted as `AC:RANG`) or unbound — the 16
September bug again. A `None` from `.get()` went straight into
`helper_parser` (mypy caught it). `rstrip("*")` strips the wrong end. The
key form changed between versions (`*cls`, `CLS`, `*CLS`) and the test fell
out of step each time, because the rule wasn't written anywhere. Deleting
the `upper()` left every test green.
Learned: a row only proves something if a wrong implementation fails it.
With `*CLS` first in the message the path is the root before it, so "left
alone" and "reset to root" give the same answer and the row can't tell them
apart. Mid-message, after `VOLT:DC`, the path is `VOLTage`; a reset sends
`AC` to the root, where it doesn't exist. Found by putting
`current_path = root` into the branch on purpose: the start-of-message row
stayed green, the mid-message row returned `None`. Also: a parameter is the
name in the `def` line, an argument is the value passed; a default is
evaluated once, when the `def` runs; `rstrip`/`lstrip` remove every matching
character at that end; `.upper()` leaves `*` alone.
Next: rows for the upper-casing and the miss path.

### 2026-10-19 — 2 h (across 18 and 19 October)
Did: Tests for the rest of the common-command branch. Wrote a test plan,
then cut it from 21 rows to 7. `test_common_commands` is now a `parametrize`
table on its own small `SOURce:CURRent:DC|AC` tree, with real common
commands and their real flags (`*CLS` has no query form): a common command
between two paths (the committed row), alone, as a query, with a parameter,
a query on `*CLS`, an unknown `*RST` mid-message, and lowercase `*cls`.
Mutation check, one break per line of the `*` branch: deleting the
`upper()` turns only `lower-case-common-command` red; removing the miss
path's `return` only `non-existing-command`; letting `*` units skip the
form check (`header.startswith("*") or helper_parser(...)`) only
`non-queryable-query-common-command`. Every line in the branch now has a
row that fails without it.
Decided: a row earns its place only if some break in the code turns it red
and no other row does. Parked the rows that would lock in the unchecked key
rule (lowercase key, key without `*`, a tree node in the dict, a common node
with a parent) — they belong to that open question.
Stuck on: the first plan crossed every position with every query/parameter
combination — 21 rows, most re-testing `split_unit` and `helper_parser`,
which have their own tables. One "negative" was a positive: a query only
needs `queryable`, so `settable=False` doesn't matter (the 3 October mix-up
again). `SENS:*CLS:VOLT` can't fail: it misses in `walk` whatever the `*`
branch does. To check the rows were sensitive I set `*CLS` to neither
settable nor queryable — every positive row went red at once, which shows
they can fail but not which are redundant, because it changed the test's
input, not the code. The first L181 break deleted L181–183, which also
removed the append every unit goes through: 20 failures instead of one.
Three `assert`s in one function: the first failure hid the rest. Worried
that rows naming module-level nodes was the 10/13 October problem again —
it isn't: that was rows building their own trees; nodes that
`walk_message` only reads are safe at module level.
Learned: the mutation table — rows down the side, one-line breaks across
the top, mark what goes red. A row whose reds are all covered by other rows
adds nothing. A break has to hit only the behaviour under test; breaking a
line every unit shares breaks everything and proves nothing. `or` stops at
the first `True`, so `x or check()` switches a check off for one case. A
column that never changes isn't a parameter. In this codebase a header is
the part before the parameters; a message is the whole line.
Next: decide whether "current path is per-connection state" is already met.

### 2026-10-19 — 1 h (second session)
Did: "Current path is per-connection state, not module-level" — the last
open item in 1.1, so the command-tree section is complete. `current_path` is
a local variable in `walk_message`, created at the start of every message,
so no two messages or connections can share it. New
`test_path_per_connection_state`: `MEAS:VOLT:AC:NPLC`, then `RANGe` in a
second call must give `[None]`. Mutation check: made `current_path` a
module-level variable with `global`, reset to `root` only while it is still
`None` — the test went red, and 15 other tests with it. Also widened
`test_common_commands`' annotation to `list[ParsedUnit | None]`.
Decided: a local variable is the best answer, not a stopgap — give state the
smallest scope that works. Per-connection state becomes a real decision with
the error queue, which has to survive between messages.
Stuck on: first wrote the two messages as two `parametrize` rows — two
separate tests, so `message-two` only follows message one if pytest happens
to run them in order (`-k message-two` runs it alone). The first message,
`MEAS:VOLT:AC`, was rejected by the form check (`AC` isn't settable), not by
the walk as I first guessed; calling `walk` on its own showed it succeeded.
Thought two nodes named `DC` would raise — they don't: ambiguity is only
between nodes typeable from the same parent, and client input never raises.
`DC` couldn't detect a leak anyway, because the leaked `DC` isn't settable
either; `RANGe` under `AC` is, so a leak shows. The break took three tries:
`global root` (a parameter — `SyntaxError`, the file wouldn't load) with a
check on `root is None` (never true); then the reset to `root` was still
unconditional, so the test stayed green.
Learned: to find which stage of a pipeline produced a `None`, call each stage
on its own, in order. A test must never depend on another test having run
first; steps that must happen in sequence go in one test. `global name`
makes assignments inside a function write the module-level variable, and a
parameter can't be global. Module-level state leaks between tests: one
leaking variable turned 16 tests red.
Next: commas between parameters.

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
- Which clause of SCPI-99 or IEEE 488.2 states that common commands leave the
  header path untouched? Not cited in `walk_message`'s docstring yet; add it
  once found.
- Common-command keys must be upper-case, include the `*`, and match their
  node — documented in `walk_message`, enforced nowhere (`{"*IDN": cls_node}`
  is accepted). Decide whether the key should be derived from the node when
  the real instrument definition is built. Parked test rows for it (19 Oct):
  lowercase key, key without `*`, a tree node in the dict, a common node
  that has a parent.
