# Our client discards `bd` warnings on a zero exit — verified, and measured

**Date:** 2026-08-21
**Upgrades:** the code-read claim in `rekey-silent-skip-hazard-2026-08-20.md`
("OUR OWN CLIENT DISCARDS THE WARNING") from a reading to a verified mechanism
plus a live demonstration
**Verdict:** the mechanism is **real and exact**. The current impact is
**latent**, not active, on the read paths measured — and that distinction is the
point of this note.
**Read-only.** Every probe below is a read verb.

## Why re-check something already recorded

The hazard note established this by reading the source. This repo's own rule is
that reading the source is not sufficient on its own, and the distinction turns
out to matter: the claim is correct about the *mechanism* but was never tested
against *which calls actually emit anything*. Both halves are needed before the
defect can be prioritised honestly.

## Leg 1 — the mechanism, exactly

Three lines, all in
`livespec_orchestrator_beads_fabro/effects/_beads_client_shell.py`:

```python
completed = subprocess.run(
    argv,
    capture_output=True,      # stderr goes to completed.stderr, never a terminal
    …
)
```

```python
def raise_for_status(*, completed, argv, tenant) -> None:
    """Map a nonzero `bd` exit onto the typed expected-error surface."""
    if completed.returncode == 0:
        return                # <- returns BEFORE stderr is ever read
    stderr = completed.stderr or ""
    …
```

and in `_beads_client.py`:

```python
def _run_json(self, *, verb_args):
    completed = self._invoke(...)
    return self._parse_json(stdout=completed.stdout, ...)   # stdout only

def _run_void(self, *, verb_args):
    _ = self._invoke(...)                                   # discards it entirely
```

So on a **zero exit**, `completed.stderr` is never read by anything. `_run_void`
discards the whole `CompletedProcess`. The claim is confirmed, and it is not a
near-miss: the early return sits one line above the only `stderr` read in the
function.

## Leg 2 — do such warnings actually occur? Yes. Measured.

Every verb below run against this repo's live tenant, capturing the two streams
separately:

| Verb | exit | stdout | stderr |
|---|---:|---:|---:|
| `list --status all --limit 0 --json` **(what our client sends)** | 0 | 3,538,938 | **0** |
| `list --status all --limit 1 --json` | 0 | 9,930 | **122** |
| `show bd-ib-3kolea --json` | 0 | 3,457 | 0 |
| `comments bd-ib-3kolea.4 --json` | 0 | 16,461 | 0 |
| `sql 'SELECT 1'` | 0 | 21 | **154** |
| `ready --json` | 0 | 3 | 0 |
| `stats` | 0 | 271 | **154** |

The two warning texts, both on a **zero exit**:

```
Showing 1 issues; more results matched but were hidden by --limit.
Use --limit 0 for all, or --limit N to raise the cap.
```

```
Warning: auto-backup failed: register backup remote: add backup backup_export:
Error 1105 (HY000): command denied to user '<tenant>'@'%'
```

## Leg 3 — the honest impact assessment

**The read paths our client actually uses emit nothing today.** `list` with
`--limit 0`, `show`, `comments` and `ready` all produced zero stderr bytes. So
this is **not currently losing information on those calls**, and it would be
wrong to report it as an active data-loss bug on them.

**But the warning class is real and lands on a zero exit**, and two of its
instances are pointed:

1. **The truncation warning is the exact hazard AGENTS.md documents at length.**
   The repo's own guidance devotes a section to `--limit` and `--status all`
   silently returning a partial ledger. `bd` *does* warn about precisely that —
   and the warning goes to the stream we drop. Our client is safe here only
   because it hardcodes `--limit 0`; any caller that ever passes a finite limit
   gets a silently truncated result, with the warning explaining it discarded.
2. **The auto-backup failure is a standing, unnoticed condition.** It fires on
   `sql` and `stats`, exits 0, and says the tenant's SQL user lacks the
   privilege `bd`'s auto-backup wants. Nobody has seen it because nothing
   surfaces it. (This is **not** a claim our backups are broken —
   `bd-ib-3kolea.1` closed `resolution:completed` against three deliberate
   backup layers, and this is `bd`'s own opportunistic extra. It is an example
   of the shape: a real condition, reported correctly by the tool, invisible to
   us.)

**And the instance that matters most for this epic has not happened yet.** The
re-key silent-skip notice is `log.Printf` — Go's `log` writes to **stderr** —
emitted while `MigrateUp` completes and exits **0**. Upstream's own comment says
those three lines "are the only notice". That is this exact shape, on the one
occasion where losing the message means a partial primary-key rewrite is
recorded as a success.

So: latent today, load-bearing during the migration.

## The fix, and why it is not applied here

The minimal change is for the shell client to surface a non-empty `stderr` on a
zero exit rather than drop it — pass it through to the caller's stderr, or log
it, rather than only consulting it on the failure path.

It is **not** implemented in this change, for two reasons:

1. It touches product `.py` and so requires the Red-Green ritual, which makes it
   a work item rather than a ride-along on a research note.
2. It is **not this epic's work.** The hazard note declined to file it because
   adding an unadmitted child would grow the undisposed-children set that gates
   this plan's archive — a correct concern. The resolution is to file it as a
   **standalone** item rather than a child of `bd-ib-3kolea`, which keeps the
   archive gate clean while making the defect tracked instead of buried in a
   research note.

A caution for whoever implements it: the pass-through must not turn every
benign warning into noise on paths that run thousands of times, and it must not
break `_run_json`'s contract. The measurement above is the useful input — the
verbs our client uses are quiet, so surfacing stderr on zero exit should be
close to silent in normal operation, which is what makes it safe to turn on.

## Scope and limits

Seven verbs, one tenant, read verbs only. **Write verbs were not probed** —
deliberately, since probing them means mutating a live tenant — so whether
`comment add` / `update` / `close` emit the auto-backup warning is **unmeasured**.
That gap matters, because write verbs go through `_run_void`, which discards the
`CompletedProcess` outright and is therefore the worst case. Anyone extending
this should probe writes against a disposable tenant, not a live one.
