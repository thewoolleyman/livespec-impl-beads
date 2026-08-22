---
topic: factory-headroom-preflight
author: claude-opus-5
created_at: 2026-08-22T13:46:55Z
---

## Proposal: Dispatch MUST refuse a factory with no storage headroom, and an unreadable headroom gauge is keyed on human presence rather than defaulted

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

Adds a storage-headroom precondition to the Dispatcher's admission valve: an item whose dispatch would target a factory observed to be below its free-space threshold MUST NOT be admitted, and the refusal MUST name the factory, the observation, and the alternate-factory route. Adds §"Factory storage headroom precondition" carrying the gauge definition, the unobservable-gauge disposition, the threshold-derivation obligation, and the claim-release rule that removes the phantom claim this failure currently leaves behind. Reconciles the new precondition with §"Host concurrency belongs to the Fabro scheduler" and ratified Scenario 53 explicitly, on the ground that the retired host dispatch cap DUPLICATED a ceiling the Fabro server already enforces whereas Fabro enforces no disk precondition at all — it accepts the run and then fails at run-directory creation. The unobservable-gauge question is answered by reusing this specification's already-ratified fail-closed cost-gate keying (`--item` presence as the proxy for a human being present) rather than by inventing a new posture: an unattended drain refuses, a hand-picked dispatch warns, and an unreadable gauge is NEVER silently read as healthy. Adds Scenarios 62 and 63.

### Motivation

Delivers requirement R3 of the `factory-host-storage-reclamation` plan (ledger epic `bd-ib-bdcmok`, child `bd-ib-bdcmok.4`), carried forward from the incident item `bd-ib-gr9f`. Every measurement below was taken on 2026-08-22 against the `hp` and `vps` factories.

THE OBSERVED FAILURE. Dispatching `overseer-temi26.2` at 2026-08-22T00:51Z produced this Dispatcher envelope: stage `fabro-run`, status `failed`, `fabro_run_id: null`, detail `could not create run / Failed to persist run state: I/O error: creating run directory /home/cwoolley/.fabro/storage/scratch/20260821-01M0KF5BCQW9QA356D40AR9NYY: No space left on device (os error 28)`. The factory host was at 100% — `/dev/sda1 458G size, 435G used, 0 available`.

THE BLAST RADIUS IS THE FACTORY, NOT THE ITEM. The failure is in run-directory creation, so it precedes any item-specific processing: nothing about a work-item can cause or avoid it, and every repo routed to that factory fails identically. Two different repositories hit this signature within 44 seconds of each other.

THE DIAGNOSIS IS ACTIVELY MISLEADING WITHOUT A NAMED CONDITION. The path `/home/cwoolley/...` does not exist on the dispatching host, whose local user is `ubuntu` and whose local filesystem read 127G free at 82% used. A local `df` therefore reads perfectly healthy while every dispatch fails, and an investigator who checks local disk clears the host and goes looking at the item. Naming the condition at the valve is what converts a confusing remote failure into an actionable one.

IT LEAVES A PHANTOM CLAIM. After the failure `overseer-temi26.2` read `status: active`, `assignee: fabro`, `fabro_run_id: null`, with no run in existence; it had to be released to `ready` by hand. `bd-ib-gr9f` records this as a SIXTH way to acquire a phantom claim beyond the five catalogued in `livespec-overseer`. A refusal message alone would not have prevented it, which is why this proposal also states the claim-release obligation.

THE PRECEDENT ALREADY EXISTS IN THIS SPECIFICATION. Scenario 19 has the Dispatcher refuse BEFORE sandbox launch when a credential cannot outlive the run, naming the condition; Scenario 48 refuses a not-factory-safe item at the same valve, leaves it `ready` rather than `blocked`, and names the route. A factory with no room to create a run directory is the same class of precondition, observable at the same moment, and is presently the only one of the three that is discovered by failing.

WHY FABRO DOES NOT ALREADY COVER THIS. The `bd-ib-bdcmok.1` spike established by direct measurement that the pinned build (`fabro 0.254.0 (8de6611)`) exposes NO declarative retention or TTL configuration, and that a v0.310 nightly — 56 minor versions ahead of the pin — does not add one either. Fabro applies no disk-headroom precondition of any kind: it accepts the run, then fails while persisting run state. There is nothing here for the Orchestrator to duplicate.

THE GAUGE TRAP, MEASURED, AND WHY THE SPECIFICATION MUST NAME WHAT IS GAUGED. `fabro system df --server <factory>` exists on the pinned build, is remote-capable, and returns in seconds — it is the obvious candidate and it is the WRONG instrument. Run against `hp` on 2026-08-22 it reported 356 runs at 67.8 MB, logs at 2.0 KB, database and artifacts at 230.0 MB, and a data directory of `/home/cwoolley/.fabro/storage`. It carries NO free-space figure at all. It reports what Fabro HOLDS, which the same spike measured as roughly 430 MB on `vps` and 220 MB on `hp` — about 0.018% of the used space on the fuller host. A headroom check built on it would have reported a healthy few hundred megabytes while the host had zero bytes available. It is nonetheless the correct way to RESOLVE the path whose filesystem must be measured, which is why the clause separates the two roles. `docker system df` is likewise unusable: measured independently by two sessions, it HANGS on both factory hosts rather than returning.

AND THE PATH MUST NOT BE ASSUMED. The two factory hosts invert their container storage layout (`hp`: `/var/lib/containerd` 49G, `/var/lib/docker` 3.0M; `vps`: the mirror image), and `hp`'s store lives on a separate 1.4T volume bind-mounted into place. A path-keyed probe measures a few megabytes on the other host and reports success. `hp`'s store also filled while `/` stayed healthy during the very incident that motivated this item, so scraping `/` is not a substitute either.

THE HARD QUESTION THIS PROPOSAL MUST NOT LEAVE OPEN. The factory is remote and may be unreachable. Refusing all dispatch on an unreadable gauge converts a network blip into an outage; proceeding on an unreadable gauge is precisely the fail-open pattern this repository's agent instructions warn about at length. Neither default is right on its own — so this proposal takes neither, and instead reuses the keying this specification ALREADY ratified for exactly this shape of question in §"Fail-closed cost gate (keyed on `--item` presence)": whether the invocation named an `--item` is the contract's existing proxy for whether a human is present. That makes the disposition a reuse of a ratified pattern rather than a new invention, and it is named here as a deliberate choice rather than left to fall out of an implementation.

THE SCENARIO 53 TENSION IS REAL AND IS NOT PAPERED OVER. Ratified Scenario 53 says in three separate clauses that no host-level check is performed, that the dispatch is not refused on host-concurrency grounds, and that the Dispatcher does not exit with a host-capacity refusal. It exists because `bd-ib-vmve` deliberately RETIRED a client-side host dispatch cap. Read at its most literal, its first clause forecloses this proposal. The distinction this proposal asserts — and it is the maintainer's call at revise time whether it is sufficient — is that the retired cap re-decided `server.scheduler.max_concurrent_runs`, a ceiling the Fabro server already owns and enforces, and that queueing at that scheduler is a real and sanctioned outcome: the server accepts the run and promotes it in FIFO order when capacity frees. There is no analogous queue for disk. The run is accepted and then destroyed. A headroom precondition therefore duplicates nothing and displaces no server-side mechanism, which is why the reconciliation below narrows Scenario 53's wording to the concurrency question it was written to settle rather than leaving two ratified statements in contradiction.

### Proposed Changes


### Amend §"Admission valve (`ready → active`)" — add the headroom condition

Add one bullet to the existing condition list, after the `Factory-safe` bullet:

    - **Target factory has storage headroom:** an item whose dispatch would
      target a factory observed to be below its free-space headroom threshold
      MUST NOT be admitted. See §"Factory storage headroom precondition"
      below. The item is NOT marked `blocked` on these grounds (the condition
      is a transient property of a host, not of the work) and MUST NOT be
      auto-disposed; it remains `ready` and is admitted on a subsequent pass
      once the factory is observed to have recovered.

And amend the eligibility conjunction sentence in the same section so it stays
exhaustive. The sentence today reads:

    (eligible = dependencies clear AND an assignee is resolvable AND
    `factory_safety` is null — `admission_policy` plays no part at this valve)

This proposal appends one conjunct to it. NOTE FOR THE ACCEPTING REVISE PASS:
the pending `factory-spend-containment` proposal amends the SAME sentence,
appending its own conjunct. The two are additive and MUST be merged rather than
applied in sequence with the second overwriting the first. With both accepted
the sentence MUST read:

    (eligible = dependencies clear AND an assignee is resolvable AND
    `factory_safety` is null AND no unexpired observed provider-exhaustion
    record covers the provider the item would dispatch against AND the target
    factory is not observed to be below its storage headroom threshold —
    `admission_policy` plays no part at this valve)

If `factory-spend-containment` is NOT accepted, the provider-exhaustion conjunct
MUST be omitted and only the headroom conjunct appended.

### Add `SPECIFICATION/contracts.md` §"Factory storage headroom precondition"

Add as a new `###` subsection of §"Dispatcher admission, WIP cap, and post-merge
acceptance", placed immediately after §"Host concurrency belongs to the Fabro
scheduler" (or, if the pending `factory-spend-containment` proposal is accepted
first and takes that position, immediately after its §"Provider spend
containment"):

    ### Factory storage headroom precondition

    A factory with no room to create a run directory cannot execute any
    dispatch. The Fabro server applies no disk-headroom precondition of its
    own: it ACCEPTS the run and then fails while persisting run state, so the
    condition is discovered by failing rather than by being refused. The
    Dispatcher MUST therefore refuse admission when it observes the target
    factory below its headroom threshold, BEFORE launching any sandbox run and
    BEFORE writing any claim — the same moment, and the same discipline, as the
    credential-freshness gate (Scenario 19) and the factory-safety refusal
    (Scenario 48).

    **What is gauged, stated exactly, because the obvious instruments are
    wrong.** The gauged quantity is the FREE SPACE ON THE FILESYSTEM BACKING
    THE TARGET FACTORY'S FABRO RUN-STATE DIRECTORY. Three consequences are
    normative:

    - The observation MUST be of the TARGET FACTORY. The dispatching host's own
      free space MUST NOT be read as the factory's; the two are routinely
      different, and a local reading of a remote condition is the failure this
      precondition exists to prevent.
    - The run-state directory MUST be RESOLVED from the factory rather than
      assumed from a hard-coded path, and the filesystem backing it MUST be the
      one measured. The Orchestrator MUST NOT gauge headroom by measuring `/`,
      nor any fixed container-store path: factory hosts differ in where that
      state lives, and a path-keyed probe reads a healthy figure off the wrong
      filesystem and reports success. `fabro system df --server <factory>` is a
      sanctioned way to resolve that directory.
    - A gauge that reports what Fabro HOLDS MUST NOT be used as the headroom
      gauge. `fabro system df` reports Fabro's own layer and carries no
      free-space figure; the Fabro layer is a small fraction of a factory
      host's used space, so it reports a healthy figure on a host with zero
      bytes available. `docker system df` MUST NOT be used either — it does not
      reliably return on a large store.

    **Refusal effect.** A refused item MUST NOT be admitted to `active`, MUST
    NOT have an assignee set, and MUST NOT have a Fabro run launched for it. It
    stays `ready` and is NOT marked `blocked`. The refusal MUST name the
    factory, the observed headroom, the threshold it failed, and the route to
    another declared factory where one is configured. The refusal MUST identify
    itself as a factory-host STORAGE headroom refusal, distinct BOTH from the
    per-repo ledger WIP cap (§"Per-repo WIP cap") AND from Fabro scheduler run
    concurrency (§"Host concurrency belongs to the Fabro scheduler"); an
    operator reading it MUST be able to tell which of the three conditions
    refused.

    **The Dispatcher MUST NOT silently reroute.** A headroom refusal names the
    alternate-factory route; it MUST NOT substitute another factory on its own.
    Where a dispatch executes is an operator-visible property of the run, and
    the declared factories are not interchangeable.

    **An unreadable gauge is a disposition, never a default.** When the
    headroom of the target factory CANNOT be observed, the Dispatcher MUST NOT
    treat the factory as healthy. The verdict is keyed on whether the
    invocation named an `--item` — the same proxy for human presence that
    §"Fail-closed cost gate (keyed on `--item` presence)" already uses:

    - **No `--item` — an unattended queue drain, no human present.** An
      unobservable headroom is a FAIL-CLOSED REFUSAL: the Dispatcher MUST stop
      picking rather than keep dispatching blind into a factory that may have
      no room.
    - **One or more `--item` — a hand-picked dispatch, a human present.** The
      same condition is a WARNING naming the unobservability, and MUST NOT
      refuse.

    An OBSERVED headroom above the threshold never trips this gate. Every
    evaluation — observed-pass, observed-refusal, and unobservable in either
    arm — MUST be journaled on the existing Dispatcher journal carrying at
    minimum the work-item id, the factory, whether the headroom was observable,
    the observed value where there was one, the threshold, the severity, and
    whether the dispatch refused. No evaluation goes unrecorded.

    **The warning arm MUST NOT be manufactured.** Deliberately rendering the
    gauge unobservable in order to obtain the warning arm — by removing the
    observation route, by pointing the probe at a host that cannot answer, or
    by any equivalent means — is a defeat of a live check and is forbidden. An
    unobservable reading that a session did not engineer is a finding to
    surface, not a path to ride through.

    **The threshold MUST be derived, and it is not a concurrency key.** The
    headroom threshold MUST be derived from an observed bound on what a run
    needs — the working-set size of a run's own state together with the number
    of runs the factory admits concurrently — and the derivation MUST be
    recorded where the threshold is configured. A value chosen under incident
    pressure MUST NOT be carried forward as though it were derived. The
    threshold is a per-factory storage figure; it neither bounds nor purports
    to bound how many runs may execute on a host, so it is NOT the committed
    host-wide dispatch-concurrency key that §"Host concurrency belongs to the
    Fabro scheduler" forbids.

    **A storage failure MUST NOT leave a phantom claim.** No gate observes
    perfectly, and a factory can exhaust its space between the observation and
    the run. When a dispatch that HAS been admitted fails at run creation with
    a storage-exhaustion cause and no run comes into existence, the Dispatcher
    MUST release the claim it wrote — returning the item to `ready` and
    clearing the assignee it set — rather than leaving it at `active` with an
    assignee and a null run id. The release MUST be journaled naming the
    work-item, the factory, and the storage-exhaustion cause. An item left
    `active` with no run is invisible to every liveness surface that keys on a
    run existing, and it consumes a WIP slot that no work occupies.

### THIS CLAUSE RATIFIES SHIPPED BEHAVIOR — read before scoping any implementation

The claim-release clause immediately above is the one part of this proposal that
does NOT describe work to be built. It describes behavior that is ALREADY ON
`master` and unratified, and it is recorded here so that the accepting revise
pass and any implementer treat it as a drift closure rather than as a feature
request. Measured 2026-08-22 against `master`:

- `commands/_dispatcher_pre_run_claim.py` implements
  `release_pre_run_claim_if_needed`, which — for an item at `active` whose
  dispatch outcome is `failed` with `fabro_run_id is None` at one of six
  enumerated pre-run stages, `fabro-run` among them — writes the item back to
  `ready` with `clear_assignee=True` and appends a journal record at stage
  `ledger-admit-release` carrying the work-item id, the resulting status, the
  reason `pre-run-failure-without-fabro-run-id`, and the outcome stage.
- It is wired into the live dispatch path at `commands/_dispatcher_loop.py:126`.
- It landed in commit `52d826fc` ("fix: release pre-run dispatch claims") on
  2026-08-22, AFTER `bd-ib-gr9f` recorded the phantom claim from the ENOSPC
  dispatch, and its `fabro-run` arm is exactly the stage that failure reports.
- The specification carries NO clause for it. A search of every file under
  `SPECIFICATION/` for `ledger-admit-release`, "phantom claim", and "pre-run
  claim" returns nothing.

Two consequences the revise pass MUST NOT miss. First, the shipped behavior is
keyed on the ABSENCE OF A RUN ID at a pre-run stage, not on the cause being
storage exhaustion — it is broader than this clause, and this clause MUST NOT be
read as narrowing it to the storage case. Second, ratifying it here is the point:
shipped-unratified behavior is invisible to the spec's own drift surfaces, and an
implementer scoping this proposal from the clause alone would build a second
release path over the top of a working one.

### Amend §"Host concurrency belongs to the Fabro scheduler" — explicit reconciliation

This section, and ratified Scenario 53 which realizes it, currently state
without qualification that no host-level check is performed and that the
Dispatcher does not exit with a host-capacity refusal. Read literally that
forecloses the precondition above. Append the following, which narrows the
section to the concurrency question it was written to settle:

    This section governs host CONCURRENCY, and its prohibitions MUST be read as
    scoped to it. The Orchestrator owns no host-level concurrency limit and MUST
    NOT refuse a dispatch on host-concurrency grounds; that is unchanged, and
    §"Factory storage headroom precondition" MUST NOT be read as reopening it.

    The distinction is that the retired client-side cap DUPLICATED
    `server.scheduler.max_concurrent_runs` — a ceiling the Fabro server already
    owns and enforces — and that queueing at that scheduler is a real, sanctioned
    outcome: the server accepts the run and promotes it in FIFO order as capacity
    frees, so the client-side refusal removed nothing but added a second decider.
    Fabro enforces no disk-headroom precondition at all, and there is no
    analogous queue for disk: a run submitted to a factory with no room is
    accepted and then destroyed while its run state is persisted. A headroom
    precondition therefore duplicates no server-side mechanism and displaces no
    server-side queueing.

    Two prohibitions from this section survive that distinction intact and bound
    how a headroom precondition MAY be realized. It MUST be a read-only,
    per-dispatch observation of the factory the dispatch would target. It MUST
    NOT be realized as a host-global admission gauge, claim, mutex, or lock
    artifact shared across repositories, and it MUST NOT bound how many runs may
    execute on a host. A headroom observation that acquires cross-repository
    state is the retired cap rebuilt under another name.

NOTE FOR THE ACCEPTING REVISE PASS — A COLLISION WITH A PENDING SIBLING THAT
CANNOT BE MERGED SILENTLY. The pending `wip-cap-bound-honesty` proposal appends a
clause to THIS SAME section stating that the counted-claim definition "MUST NOT be
read as licensing any host observation" and that correcting the counter "would
require host observation, which this section forbids". This proposal AGREES with
that clause's intent — the WIP counter MUST remain computed entirely from local
state, and this proposal does not license teaching it about remote run liveness —
but its parenthetical generalizes to a blanket prohibition on host observation,
and this proposal's headroom probe IS host observation for a different purpose.
Both cannot stand as written. If `wip-cap-bound-honesty` is accepted first, the
pass accepting THIS proposal MUST amend that parenthetical to be scoped, e.g.
"which this section forbids FOR THE PURPOSE OF COUNTING CLAIMS; a read-only
storage-headroom observation under §'Factory storage headroom precondition' is a
different purpose and is not licensed by, nor forbidden by, this clause". If this
proposal is accepted first, the pass accepting `wip-cap-bound-honesty` MUST make
the equivalent narrowing at that time.

### Add two scenarios to `SPECIFICATION/scenarios.md`

Numbered from 62, because the pending `wip-cap-naming-collision`,
`wip-cap-bound-honesty` and `factory-spend-containment` proposals claim 57
through 61.

NUMBERING HAZARD, verified against `SPECIFICATION/scenarios.md` at master on
2026-08-22 rather than carried from a sibling's note: the file holds 53 scenarios
numbered 1 through 56, and 2, 3 and 49 are RETIRED — absent while every number
around them is present. Those three are "free" by a literal reading and MUST NOT
be reused, because a retired number is cited by history and prior revisions and
re-issuing one silently aliases new behavior onto an old citation. If the
acceptance order differs from the assumption above, the accepting revise pass
MUST renumber by appending ABOVE the current maximum, never into a gap, and MUST
re-verify that maximum at revise time rather than trusting the number recorded
here.

    ## Scenario 62 — A factory below its storage headroom refuses admission and leaves no claim

    Feature: The Dispatcher refuses a dispatch to a factory with no room,
      naming the condition, rather than submitting a run that the factory
      accepts and then destroys

      Scenario: An observed-exhausted factory refuses at the admission valve
        Given an admission-eligible `ready` work-item with a free WIP slot,
          cleared dependencies, a resolvable assignee, and null `factory_safety`
        And the target factory's observed free space on the filesystem backing
          its Fabro run-state directory is below the configured headroom threshold
        When the Dispatcher's admission valve evaluates it
        Then the item is not admitted to `active`
        And no Fabro run is launched for it and no assignee is set
        And the item stays `ready` and is not marked `blocked`
        And the refusal names the factory, the observed headroom, the threshold,
          and the route to another declared factory
        And the refusal identifies itself as a factory-host storage headroom
          refusal, distinct from the per-repo ledger WIP cap and from Fabro
          scheduler run concurrency
        And a journal record carries the work-item id, the factory, the
          observability of the headroom, the observed value, the threshold, and
          the refusal

      Scenario: The Dispatcher does not reroute to another factory on its own
        Given a headroom refusal against the default factory
        And a second declared factory with sufficient headroom
        When the Dispatcher surfaces the refusal
        Then the dispatch is not resubmitted against the second factory
        And the refusal names that factory as an operator-selectable route

      Scenario: An admitted dispatch that fails on storage exhaustion releases its claim
        Given an item admitted to `active` with an assignee set
        And its dispatch fails at run creation with a storage-exhaustion cause
          and no run comes into existence
        When the Dispatcher handles that failure
        Then the item is returned to `ready` and the assignee it set is cleared
        And no item remains at `active` carrying an assignee and a null run id
        And the release is journaled naming the work-item, the factory, and the
          storage-exhaustion cause

      Scenario: An observed-healthy factory is admitted normally
        Given an admission-eligible `ready` work-item
        And the target factory's observed free space is at or above the threshold
        When the Dispatcher's admission valve evaluates it
        Then the headroom precondition does not refuse
        And the item is admitted to `active`

    ## Scenario 63 — An unreadable headroom gauge refuses unattended and warns when hand-picked

    Feature: An unobservable factory headroom is keyed on human presence, so an
      unattended drain never dispatches blind while a hand-picked dispatch is not
      blocked by an unreachable factory

      Scenario: Unobservable headroom on an unattended drain refuses
        Given the Dispatcher loop was invoked with no `--item` (an unattended
          queue drain)
        And the target factory's headroom cannot be observed
        When the Dispatcher's admission valve evaluates a ready item
        Then the verdict is a fail-closed refusal and the Dispatcher stops picking
        And the factory is not treated as healthy
        And a journal record carries the work-item id, the factory, the
          unobservability, the severity, and the refusal

      Scenario: Unobservable headroom on a hand-picked dispatch warns rather than refusing
        Given the Dispatcher loop was invoked with `--item` naming a single
          work-item (a human is present)
        And the target factory's headroom cannot be observed
        When the Dispatcher's admission valve evaluates that item
        Then the verdict is a warning naming the unobservability
        And the Dispatcher does not refuse on headroom grounds
        And a journal record is written

      Scenario: An observed headroom never trips the unobservable gate
        Given the target factory's headroom is observable
        When the admission valve evaluates a ready item
        Then the unobservable-headroom gate does not refuse, whether or not
          `--item` was passed

### Co-edit required at revise time

The accepting revise pass MUST add one `tests/heading-coverage.json` entry per
new `## Scenario` H2 in `scenarios.md`, per this repo's revise co-edit
discipline. The `test` value MAY be the literal `"TODO"` with a non-empty
`reason`.

Verified against `tests/heading-coverage.json` at master on 2026-08-22: the map
holds 95 entries and ALL of them are H2 headings — it carries no `###` entries at
all. The new `### Factory storage headroom precondition` subsection therefore
needs NO entry of its own, and its parent H2, `## Dispatcher admission, WIP cap,
and post-merge acceptance`, is already present in the map. Only the two scenario
H2s below are required. (Note the em dash in each `heading`, U+2014, which MUST
match the scenario title byte-for-byte or the heading-coverage check fails on a
near-miss string.)

```json
{
  "heading": "## Scenario 62 — A factory below its storage headroom refuses admission and leaves no claim",
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "test": "TODO",
  "reason": "Ratified with the factory-headroom-preflight revision; the Dispatcher refuses a storage-exhausted factory at the admission valve and releases a claim when an admitted dispatch fails on storage exhaustion. Real test ID to follow."
},
{
  "heading": "## Scenario 63 — An unreadable headroom gauge refuses unattended and warns when hand-picked",
  "spec_root": "SPECIFICATION",
  "spec_file": "scenarios.md",
  "test": "TODO",
  "reason": "Ratified with the factory-headroom-preflight revision; an unobservable factory headroom is keyed on --item presence, fail-closed unattended and warning when hand-picked. Real test ID to follow."
}
```

If a scenario title is changed when the pass settles wording, the matching
`heading` value MUST be updated with it.

### What this proposal deliberately does NOT do

It does NOT specify the ROUTE by which the factory is observed, and that omission
is deliberate rather than an open question: the clause states what MUST be gauged
and what MUST NOT be used as a proxy, and any route that observes the target
factory's own filesystem satisfies it. Binding the specification to a particular
transport would couple it to `bd-ib-bdcmok.3`, whose telemetry work is presently
held on a maintainer decision, and would forbid a simpler route that already
works.

It does NOT set the threshold value. The threshold is configuration, and the
derivation obligation above is what the specification owns.

It does NOT introduce a host-level dispatch CONCURRENCY ceiling, does not
reinstate the retired client-side host dispatch cap, and MUST NOT be read as
licensing either; the reconciliation above states which of §"Host concurrency
belongs to the Fabro scheduler"'s prohibitions survive intact and bind this
precondition's realization.

It does NOT change the per-repo WIP cap, its counted-claim definition, or the
rule that the counter is computed entirely from local state.

It does NOT propose automatic reclamation, retention horizons, or headroom
telemetry. Those are the separate children `bd-ib-bdcmok.2`, `.3` and `.6` of the
same plan; this proposal covers R3 only.

It does NOT specify how the released claim is journaled beyond the fields named,
nor add a new journal surface; the existing Dispatcher journal carries it.

### Relationship to the pending sibling proposals (2026-08-22)

Three proposals are pending against §"Dispatcher admission, WIP cap, and
post-merge acceptance": `wip-cap-naming-collision`, `wip-cap-bound-honesty` and
`factory-spend-containment`. This proposal ALIGNS with all three and supersedes
none. Two mechanical interactions and one substantive one are called out above
and are repeated here so a `--only-topic` pass processing them independently does
not miss them:

1. `factory-spend-containment` amends the SAME eligibility conjunction sentence
   in §"Admission valve"; the two conjuncts are additive and MUST be merged.
2. `wip-cap-naming-collision` imposes the obligation that a capacity surface name
   which ceiling it means; this proposal's refusal text carries that obligation
   for the third ceiling, and its scenario asserts it.
3. `wip-cap-bound-honesty` appends a clause to §"Host concurrency belongs to the
   Fabro scheduler" whose parenthetical reads as a blanket prohibition on host
   observation. That is the one genuine collision, it cannot be merged silently,
   and the required narrowing is stated in full in the reconciliation section
   above.

Scenario numbering assumes all three land first, taking 57 through 61; this
proposal takes 62 and 63.

