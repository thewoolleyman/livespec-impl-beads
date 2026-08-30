# Live-exercise acceptance admission

Measured origin: `overseer-4z97.6` in the `livespec-overseer` tenant, under plan epic `overseer-4z97`. On 2026-08-23 the repo-local seat guard refused a live-exercise item with no parking acceptance label; seventeen seconds later the central autonomous dispatcher admitted the same item because the loop path never reached that guard.

The owning implementation is this repository's central dispatcher, especially `_dispatcher_admission.py`, `_dispatcher_loop_selection.py`, and their policy/acceptance collaborators. `livespec-overseer` owns only the adopter-local guard and seat wrapper, so its work-item cannot be dispatched in its own tenant for this change. The target implementation needs a cross-tenant execution mirror.

This behavior is contract-tier as well as code-tier. The current specification governs effective acceptance policy and central-loop admission, but does not state that an item whose criteria require live exercise must carry a policy that parks for evidence before autonomous dispatch. Ratification must precede implementation; do not file one mixed-tier factory item.

A thematically nearby ledger epic, `bd-ib-vq6z` (`acceptance-evidence-admissibility`), was re-measured before this thread was created. It owns unevidenceable-criterion intake and verdict classes, and its own handoff restricts its next action to `bd-ib-vq6z.1`. More importantly, no `plan/acceptance-evidence-admissibility/` directory exists on fetched `origin/master`, any fetched ref, any registered worktree, or any matching forge PR. A positive control found `plan/plan-archive-completion-gate/` with the same `git ls-tree` query. That ledger-only anchor is not a valid plan target and was not mutated.

## Initial scope

- Ratify one central-dispatch rule: when effective acceptance would autonomously close work whose criteria require live exercise, admission refuses until a parking acceptance policy is explicit.
- Implement one dispatcher-side predicate reached by direct dispatch and autonomous loop paths, with refusal and both admitting controls.
- Mirror `overseer-4z97.6` into this tenant for execution, retaining cross-references on both records.

## Explicit deferrals

- No change to the `livespec-overseer` seat guard is required unless later verification proves semantic drift; it is the measured reference behavior, not the missing call path.
- No implementation dispatch occurs before the spec-tier child ratifies the rule.
- The ledger-only `bd-ib-vq6z` plan repair is separate hygiene and is not silently absorbed here.
