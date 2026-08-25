# 005 — Triage of the ninth proposal's two adversarial review legs

Scope: the pending `SPECIFICATION/proposed_changes/needs-attention-completeness.md`
(PR #1852), the final Phase 2 filing. Two independent adversarial reviewers were
commissioned under the same pattern as research/003. Both legs are landed beside
this note:

- `reviews/needs-attention-completeness-review-claude.md` (landed PR #1855)
- `reviews/needs-attention-completeness-review-codex.md` (recovered from the
  detached Codex task `task-mt8q8r7j-un7x1y`, agent `aedb432a6a1c52356`, written to
  `tmp/overseer/homelab-loop-hardening-orchestrator/nac-review-codex-result.md`
  and landed here verbatim)

**Both legs reported.** Neither was written off as silence. Recording that
explicitly because the wind-down handoff left the codex leg's delivery unknown,
and a missing answer counts as absent rather than as assent.

Both verdicts: do not ratify as written.

## Verification posture

Every load-bearing claim below was re-measured against this repository's primary
sources before disposition, per this thread's standing practice. Two verification
notes worth keeping, because each is a trap this repo's catalogue already names:

1. **`grep -rn "host-only:stranded-dispatch"` over `.claude-plugin/scripts/`
   returned ZERO** — and the class exists. The id is composed as
   `id=f"host-only:{_STRANDED_REASON}:{work_item.id}"`
   (`_needs_attention_stranded_dispatch.py:236`), so a literal search for the
   assembled string cannot match. A reviewer's Blocker was nearly dismissed on an
   instrument that could not have returned a hit. The discriminating query was to
   open the cited file rather than to search for the rendered value.
2. `is_unattended_session` reports **False inside the credential wrapper**: the
   `with-livespec-env.sh` prefix strips `LIVESPEC_PLAN_UNATTENDED`. Measured
   2026-08-25: `printenv` direct = `1`, through the wrapper = unset. An overseer
   resume evaluating the flag inside the wrapper therefore flips to the attended
   picker and parks on a question nobody answers. Worked around here by reading
   the flag outside the wrapper and passing it in; filed as a real defect below.

## Convergence

The legs were independent and agree on substance. Codex's numbered findings map
onto claude's as: C1→claude 5 (widened), C2→claude 6, C4→claude 8 (widened),
C5→claude 7, C6→claude 9 (widened), C7→claude 11. Codex contributed one finding
claude did not reach — **C3, the machine envelope has no structured payload** —
and it is the finding that forces the largest single repair. Claude contributed
the three Blockers, none of which codex reached in that form.

## Dispositions

Every finding is accepted except where a reason is recorded. "Repaired in place"
means the proposal text changed in this same change.

### Blockers

**B1 — the stale-claim fact duplicates the ratified stranded-dispatch class.**
ACCEPTED, repaired in place. Verified: `_needs_attention_stranded_dispatch.py`
composes `host-only:stranded-dispatch:<id>` with `kind="host-only"` for exactly
the lock-less active population, and `contracts.md:2302` names `bd-ib-zp3u7y` as
that population's owner. `hygiene:stale-claim:<work-item-id>` is **dropped from
the proposal entirely**; one work-item can no longer produce two ids of two kinds
with two handoffs. The capacity clause now cross-references the existing class and
forbids re-composing its population.

**B2 — the blanket "release handoff" would re-queue merged work.** ACCEPTED,
resolved by B1's drop, plus a guard retained. Verified:
`release_to_ready_command` renders `drive move:<id>:ready`
(`_needs_attention_handoffs.py:155-156`), `_MOVE_ALLOWED = {backlog, ready,
blocked}` validates the TARGET only (`_drive_policy_valves.py:41,207`), and the
shipped stranded composer already discriminates by evidence shape —
`reconcile_merged_command` for PR+merge-SHA, `pr_view_command` for PR-only,
`release_to_ready_command` only for no-PR. The repaired text keeps an explicit
prohibition on advertising a status-move handoff against green-terminal evidence,
so the discrimination cannot regress.

**B3 — "consume the accounting directly" mandates a journal mutation from a
query-only surface.** ACCEPTED, repaired in place. Verified:
`claimed_active_accounting` calls `journal.append(record=_abandoned_record(...))`
inside its per-item loop for every lock-less readable-journal active row
(`_dispatcher_claim_reclaim.py:46-73`) — a write on every call, not idempotent.
The "or the accounting directly" branch is removed; the repaired clause requires a
**side-effect-free projection** and records the ordering dependency that such a
projection must exist before the fact can compose.

### Majors

**M4 / claude 4 — the capacity fact was unconditional, with no clearing rule and
no executable handoff.** ACCEPTED, repaired by narrowing the trigger. This is the
disposition that changed the proposal's shape most, so the reasoning is recorded
rather than only the outcome.

The incident this clause answers (matrix 03) is that three surfaces re-derived
capacity from raw statuses and agreed on a wrong answer. The remedy for THAT is a
single-authority rule, which is normative text — not an attention item. An
attention item additionally needs an operator action, and "slots are free" has
none; an unconditional row also makes the renderer's "No attention items." branch
unreachable, converting an attention list into a dashboard.

So the two are separated. The single-authority rule is kept in full force. The
attention ITEM is narrowed to the actionable residue: it composes only when the
cap is reached AND at least one counted hold is not backed by a live watchable
run. Where every counted hold is a live run, capacity is legitimately busy and
nothing is emitted. The lock-less residue is already the stranded class (B1), so
the remaining actionable class is the unreadable-journal hold, whose handoff is an
inspection route. This also keeps the fact clear of the `bd-ib-dohu2g` shape v077
forbids — no handoff routes through the cap-enforcing path that would refuse.

**M5 / C1 — a universal MUST paired with a list that already omits ratified
waits.** ACCEPTED, repaired in place. Verified two additional orchestrator-owned
waits in ratified text: a factory-unsafe item is surfaced for host routing and
stays `ready`, not `blocked` (`contracts.md:2203`), and a provider-exhaustion
refusal leaves the item `ready` and "surfaced through the needs-attention
awareness surface" (`contracts.md:2607`). Both are enumerated now. The universal
MUST is replaced by the enumerated set plus a **forward-registration rule**: any
future contract that leaves work parked must register its attention derivation and
unblock handoff. That covers `factory-headroom-preflight` if it ratifies, without
this proposal depending on a pending sibling.

Codex additionally proposed enumerating the non-convergence `backlog` bounce.
NOT ACCEPTED as a wait, and named as an explicit exclusion with its reason instead
of being silently omitted: a bounced item routes to grooming/re-decomposition
(`contracts.md:1255`), which is a work route rather than a wait on a person or a
slot. Recorded below as a follow-up candidate, because a bounced item carries
`intake:triaged` and therefore does not reach the untriaged-backlog lane either —
a real surfacing gap, but one outside matrix 03/10/11.

**M6 / C2 — the aging fact has no clock source.** ACCEPTED, repaired in place.
Verified: the vendored `WorkItem` carries `captured_at` and nothing else
(`_vendor/livespec_runtime/work_items/types.py:187`); `store.py:170` maps it from
beads `created_at`. No `ready_since`, `ready_at`, or transition timestamp exists
anywhere in the materializer. The repaired text names the instant (the latest
transition into `ready`), requires a durable clone-independent source, explicitly
disqualifies the machine-local dispatch journal (a fresh clone would emit no aging
fact while items age — the absence-reads-as-resolution direction v077 forbids),
defines the **age-unknowable posture** (report the item as age-unknown, never omit
it), and defines "no dispatch in flight" as the live dispatch lock plus watchable
run rather than leaving three candidate sources open. The durable instant is
recorded as an implementation prerequisite.

**M7 / C5 — false premise about what the accounting's verdict contains.**
ACCEPTED, repaired in place. Verified: `ActiveClaimAccounting` has exactly
`active_count`, `live_lock_active_ids`, `green_terminal_active_ids`,
`journal_unreadable_active_ids` — three classes, no rework member; and the rework
marker appears in no `.py` file repo-wide (v071 is ratified-unimplemented, children
`bd-ib-mrsply` / `bd-ib-tokosl`). The proposal no longer claims four classes. The
ordering dependency on `bd-ib-mrsply` is stated normatively: the accounting grows
the ratified rework class, and needs-attention consumes that verdict — it does not
re-derive from the raw label, which would breach the single-authority rule.

**M8 / C4 — unreconciled with the pending WIP-cap siblings.** ACCEPTED with a
deliberate narrowing. Verified: `wip-cap-naming-collision` binds "any status,
doctor, or attention surface that echoes the cap" to identify it and to state that
host concurrency is governed separately; and it carries a 2026-08-22 rider warning
that the recommended label CONTAINS THE UNSETTLED SCOPE WORD, which
`wip-cap-bound-honesty` must decide. So the repair adopts the **obligation** and
NOT a literal label: the capacity fact must identify the value as whatever
§"Per-repo WIP cap" ratifies and must state the separate host governance. Adopting
a label here would pre-empt a decision another proposal owns. Also accepted:
the count is scoped to cap-enforcing admission paths, with the hand-picked
`dispatch --item` bypass and the separate Fabro scheduler ceiling disclaimed.

Verified against `wip-cap-bound-honesty`: its counted-claim definition (live local
lock, or unreadable journal) already matches the shipped
`active_count = len(live_lock) + len(journal_unreadable)`, so the repaired text
counts COUNTED CLAIMS rather than rows at `active`.

**C3 — the aggregate capacity payload does not fit the ratified envelope.**
ACCEPTED, repaired in place; this is codex's unique finding and it forced the
representation decision. Verified the envelope permits exactly `id`, `kind`,
`urgency`, one-line `summary`, `source_ref`, and one `handoff`
(`contracts.md` §"The needs-attention machine envelope"), and the ratified runtime
v012 `HygieneScanFinding` is equally flat. "Every holder with its reason, as data"
therefore had only three realizations, all bad: prose hidden in `summary`, an
invented `summary` parser, or an unratified field contradicting the proposal's own
"no runtime field is changed".

Resolution: **flat items, not a payload.** Per-hold detail rides as its own
`hygiene:capacity-hold:<work-item-id>` item with its own stable id, summary and
handoff; the aggregate carries a deterministic one-line summary. Machines diff by
id, which is what the envelope already guarantees, and no runtime field changes.
The phrase "composed as data" is dropped wherever it implied a structured payload.

**C6 second half — no scenario falsifies wait completeness.** ACCEPTED. Scenario
85 is added, exercising every declared wait class plus a non-wait control.

### Minors

- claude 9 / C6 first half — parked-acceptance arity. ACCEPTED with a narrowing.
  Verified: shipped `human_valves` emits an `approve` lane, then `accept` for
  `status == "acceptance"`, and no reject branch exists
  (`_needs_attention_work_items.py:74+`). But ratified v072 says the parked
  acceptance composes "through the EXISTING composition classes" and "introduces
  no new attention kind". Codex proposed one item per disposition; that would BE a
  new composition. Repaired as **one item per parked acceptance**, handoff
  `accept:<id>`, summary naming both `reject:<id>:rework|regroom` dispositions,
  plus the distinguishability requirement claude asked for (a NEEDS_ATTENTION park
  must be distinguishable from routine parking).
- claude 10 — heading-coverage co-edit omits the ownership the gate requires.
  ACCEPTED; owner `bd-ib-w3if5j` and the integration-tier reason phrase named, as
  the v078 entry does.
- claude 11 / C7 — Scenario 83 vacuous. ACCEPTED; the scenario now sets a concrete
  cap, asserts exact held and free counts, includes the journal-unreadable row, and
  carries the negative controls (a live-lock item is not a stale claim; a
  rework-pending item is not reported abandoned; an unreadable journal never
  increases free capacity).
- claude 12 — "positive number". ACCEPTED; `contracts.md:2334` says every other
  integer setting remains a POSITIVE integer. Changed to positive integer.
- claude 13 — the declared-API-configurable class has no ratified definition.
  ACCEPTED; a clause naming the class is added, as claude suggested this proposal
  is the natural place for it.
- claude 14 — the boundary binds a surface this spec does not own. ACCEPTED;
  rephrased producer-side ("the orchestrator MUST NOT emit"), "holder" defined, and
  the inside-the-boundary case stated (foreman-attributed data read from THIS
  repo's own journal).

### Unverified observations

Both legs flagged observations they did not verify; neither is dispositive.
Codex did not check the overseer's ratified contract for the claim that foreman
and overseer waits publish as plan-epic ledger state. Not verified here either:
that repository is not this one's to read, and the R1 boundary is exactly the rule
that keeps the orchestrator overseer-unaware. Recorded as an assumption the
boundary clause rests on rather than as a fact this proposal establishes.

Claude's edge case — a numerically-named checkout would fail the id validator and
be silently dropped — is real but is the runtime's recorded silent-drop
non-conformance, not this proposal's. Noted, not repaired here.

## Follow-up candidates (not filed by this note)

1. **The credential wrapper strips `LIVESPEC_PLAN_UNATTENDED`.** An unattended
   overseer resume that evaluates `is_unattended_session` inside
   `with-livespec-env.sh` raises the attended picker and parks. Measured directly
   (see Verification posture). This is a live defect in the hands-off restart path.
2. **A non-convergence `backlog` bounce reaches no attention surface.** It carries
   `intake:triaged`, so the untriaged-backlog lane does not compose it, and this
   proposal deliberately excludes it as a work route rather than a wait. Outside
   matrix 03/10/11; worth its own filing.
