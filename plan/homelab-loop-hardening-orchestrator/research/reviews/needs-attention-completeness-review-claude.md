# Adversarial review of needs-attention-completeness — reviewer claude

(Commissioned 2026-08-25 by the homelab-loop-hardening-orchestrator
session over the pending PR #1852 proposal; received verbatim and landed
during the session's overseer wind-down. The paired codex leg was
dispatched as a detached Codex task — task-mt8q8r7j-un7x1y, agent
aedb432a6a1c52356 — and had not reported at wind-down; the successor
recovers its result from
tmp/overseer/homelab-loop-hardening-orchestrator/nac-review-codex-result.md
if written, else re-commissions.)

## Executive verdict

Do not ratify as written. The central technical claim is sound and
verified end-to-end: `hygiene:<type>:<resource>` is ratified grammar in
livespec-runtime v012, the kind↔prefix bijection is satisfied, and no
runtime change or pin bump is needed. Charge fidelity to homelab
research/002 §§03/10/11 and research/009 R1 is good. What fails is the
layer below the grammar: three clauses cannot be implemented without
breaking ratified text in THIS repository.

## Findings

### 1. Blocker — the stale-claim fact duplicates the shipped, ratified, separately-owned stranded-dispatch class

`hygiene:stale-claim:<id>` re-composes a population already composed
today as `host-only:stranded-dispatch:<id>`
(`_needs_attention_stranded_dispatch.py:59-85, 236, 269-276`; the
green-terminal exclusion routes into that population via
`_record_evidence` lines 141-145). The ratified §"Rework-pending
re-dispatch" → "Stranded-state discrimination" names the population's
owner (`bd-ib-zp3u7y`). One work-item would produce two ids of two
kinds with two handoffs — one a completion route (`reconcile-merged`),
one a re-queue route — breaking the v077 stable-id diffing guarantee.
The proposal never mentions the class (search for
stranded/untriaged/host-only over the proposal: 0 hits). Fold the
per-item surfacing into the existing class or state the partition and
coordinate with bd-ib-zp3u7y.

### 2. Blocker — the "release handoff" contradicts the ratified per-lane verb vocabulary, and its plausible realization re-queues merged work

The `active` lane is observe-only (§"Per-state operator verb
vocabulary") except the marked-item dispatch verb. The only shipped
release candidate renders the move-to-ready drive action; `move_item`
(`_drive_policy_valves.py:196-224`) validates only the target
(`_MOVE_ALLOWED = {backlog, ready, blocked}`) and never the source, so
the handoff EXECUTES — and on a green-terminal claim re-queues work
whose PR already merged. The correct action for that evidence shape is
`reconcile-merged`, which the shipped stranded-dispatch handoff already
picks. The rework-pending leg is fine (`dispatch --item` is ratified
for marked items).

### 3. Blocker — "consume the accounting directly" mandates a journal mutation from a contractually query-only surface

`claimed_active_accounting` (`_dispatcher_claim_reclaim.py:46-73`)
appends a `dispatch-claim-abandoned` journal record for every lock-less
readable-journal active row on every call — not idempotent. Ratified
collisions: the thin-transport skills (needs-attention included) are
query-only by contract; §"Control surface and audit" makes the journal
the published per-decision audit surface (snapshot-time appends put
records there behind which no dispatcher decision stands); and the v071
claim-accounting clause forbids recording a marked item as abandoned.
The "consume this composition" branch is unspecified (where persisted,
how read, what when absent/stale). Note homelab research/002 §03's own
fix row offered the dry-run drain as the licensed instrument; narrowing
to "the accounting directly" is what creates the conflict.

### 4. Major — the capacity fact has no trigger and no clearing rule, so it emits on every snapshot with no action to offer

Unlike the well-drafted aging bullet, `hygiene:capacity:<repo>` is
unconditional — it appears when five of five slots are free. The
runtime's ratified Handoff rule requires an executable action
(`command: str` required), and there is none for "slots are free"; an
unconditional row also makes the renderer's "No attention items."
branch unreachable, converting an attention list into a dashboard. The
capacity-deferred wait has the same defect: no operator action frees a
WIP slot, and the nearest shipped handoff (the drive impl action)
routes through the cap-enforcing loop path, which refuses at a full cap
— the bd-ib-dohu2g shape v077 forbids.

### 5. Major — wait completeness pairs a universal MUST with a list that already omits a ratified wait

§"Provider spend containment" creates a fifth orchestrator-owned wait
(an item held by an unexpired observed-exhaustion record "stays
surfaced through the needs-attention awareness surface") — none of the
four enumerated, and excluded from the aging fact by construction
(admission-eligibility excludes covered providers). Homelab's four-item
list drew the R1 boundary, not an exhaustiveness claim; the universal
MUST is the proposal's own escalation. Close the list explicitly or
enumerate the containment wait (and the headroom wait if
factory-headroom-preflight ratifies).

### 6. Major — the aging fact has no clock source in the ratified data model

No ready-dwell instant exists: the materialized work-item carries only
`captured_at` (filing time); beads `updated_at` moves on any edit;
journal admit/approve records are machine-local
(tmp/fabro-dispatch-journal.jsonl), absent on a fresh clone, and record
nothing for a human-moved item — and journal absence is silent, so a
fresh clone would emit no aging fact while items age, the exact
absence-reads-as-resolution direction v077 forbids. Name the instant,
its persistence, and the age-unknowable posture. "No dispatch in
flight" is likewise undefined (lock vs journal vs fabro ps — all three
live candidates with different failure modes).

### 7. Major — false premise about what the accounting's verdict actually contains

`ActiveClaimAccounting` has three classes (live-lock,
journal-unreadable, green-terminal), not four: no rework-pending member
exists — the rework marker appears in ZERO `.py` files repo-wide (v071
is ratified-unimplemented; children bd-ib-mrsply / bd-ib-tokosl). And
the exclusion set is incomplete: rows journaled
no-outcome-since-ledger-admit or terminal-outcome-non-green are
excluded from the count but appear in NO exposed tuple, so "each
excluded stale claim" cannot be composed from the verdict as shipped.
Either the accounting grows members or the clause names which
exclusions it means. Record the ordering dependency.

### 8. Major — unreconciled with the pending wip-cap-naming-collision proposal, which governs exactly this surface

That sibling would bind "any status, doctor, or attention surface that
echoes the cap" to identify it as the per-repo LEDGER cap. The capacity
fact reports the free-slot count against wip_cap and says neither.
One sentence fixes it. (Checked the other two siblings: bound-honesty
is mutually reinforcing; factory-headroom feeds finding 5. Scenario
numbers 83/84 are free; sibling reservations 57-59/62-63 intact.)

### 9. Minor — the parked-acceptance leg adds nothing observable, and its handoff arity is ambiguous

The human-valve composition already emits an accept lane for any
acceptance item; a NEEDS_ATTENTION park is indistinguishable from
routine parking. If distinguishability is intended (the verdict plus
absent evidence leg in the summary), say so. "The accept/reject valves"
is plural against a single-handoff item model; the shipped chain emits
at most one lane per item.

### 10. Minor — the heading-coverage co-edit instruction omits the ownership the gate requires

A literal reading arms the owned-TODO release tier
(dev-tooling/just-check-pre-commit-doc-only.sh:50-54). Name the owner
(bd-ib-w3if5j) and the integration-tier reason phrase, as the v078
entry does.

### 11. Minor — Scenario 83 has no negative control and ends on a vacuous assertion

"reflects the accounting's verdict" asserts no value (no wip_cap
given; a binding can only compare the verdict to itself). Add the cap,
assert the count, and add the negative controls the Given already
contains: the live-lock item is NOT a stale claim; the rework-pending
item is NOT reported stranded/abandoned (the ratified discrimination
rule). The journal-unreadable class is exercised by neither scenario.
Scenario 84's inline "And when" negative control is fine (4 precedents).

### 12. Minor — "positive number" introduces the first non-integer numeric setting without saying so

§"Per-repo WIP cap": "Every other integer setting remains a POSITIVE
integer." Use positive integer or declare the new domain deliberately.
"Effective" is vestigial where no per-item override exists (inherited
from the v078 bullet).

### 13. Minor — the API-configurable key set still has no ratified definition covering keys like this one

§"Control surface and audit" defines the set as the policy settings
minus the committed-only class; drift_capture_merge_threshold (v078)
and this key are in neither. This proposal is the natural place to add
the clause naming the declared-API-configurable class.

### 14. Minor — the boundary clause binds a surface this spec does not own, and leaves the foreman seat identity unaddressed

Phrase the console MUST NOT as what the orchestrator emits. And say
that rendering a foreman-attributed assignee or invoker from THIS
repo's own journal is inside the boundary — "holder" is otherwise
undefined.

## Unverified observations

Homelab incident measurements cited faithfully but not re-measured
(read at research/002:92-227); R1 restated faithfully
(research/009:29-50). Edge case: the id validator rejects purely
decimal components and the shipped composer drops invalid ids silently
— a numerically-named checkout would silently lose the repo-keyed
facts (probably the runtime's recorded silent-drop non-conformance, but
this proposal first makes repo-name-keyed ids normative). Whether
hygiene items may be producer-constructed: permitted by shipped
precedent (the untriaged-backlog fact is direct-constructed), but the
proposal should name its construction route.

## What the proposal gets right

The grammar claim verified end-to-end (v012 three-part hygiene ids;
vendored validator implements it; the new kind↔prefix bijection
satisfied; no pin bump needed). The v077 ownership cut applied exactly
as intended. The deferral discharged correctly against ratified text.
Scenario numbering coordinated. The aging bullet is the best-drafted
clause — apply its trigger/clearing discipline to the capacity bullet
and finding 4 resolves. The R1 boundary is genuinely load-bearing and
correctly placed; objections are phrasing, not substance.
