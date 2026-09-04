---
topic: host-rendered-prepare-step-inputs
author: fable (livespec-dev-tooling plan ci-runner-cache-tiers)
created_at: 2026-09-04T15:35:00Z
---

## Proposal: A workflow input token may be resolved by the engine or by the Dispatcher's overlay, and the seam check must say which

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

The typed-workflow-inputs clause requires that every `inputs.*` token "sit in a position the engine renders". That criterion is too narrow to describe how the payload actually works, and the gap between it and the shipped check hid a total dispatch outage for four days. Widen the criterion to "a position resolved before the sandbox executes it", admit exactly two resolvers — the engine at run-create time, and the Dispatcher's run-config overlay host-side — and require the check to record which resolver each position depends on rather than treating them as one undifferentiated class.

### Motivation

Measured 2026-09-04. Every dispatch through the released `implement-work-item` payload failed after five seconds, before any agent node ran:

```text
Setup command failed (exit code 127):
set -- {{ inputs.prepare_toolchain_mise }}; test $# -eq 0 || "$@"
/bin/bash: line 1: {{: command not found
```

fabro 0.254.0 renders `inputs.*` in graph node attributes at run-create time and leaves `run.prepare` commands verbatim. Proven in isolation, away from this payload: a three-node graph whose only content is one templated prepare command and one templated node script reading the SAME input, created with `fabro create --input probe_value=RENDERED_FROM_FLAG` and never started. The persisted spec held the value in the node and the raw token in the prepare command. An empty value is not the trigger.

The specification is implicated, not merely the code. `39526e5c` (2026-08-31) templated the prepare steps and the seam check's scan admitted the `[[run.prepare.steps]]` `script` position into its rendered set, while the maintainer confirmation recorded that day covered a parallelogram node's `script`. From that moment the shipped check classified a position as rendered that the engine does not render, which is the opposite of what this clause requires — a divergence that predates and caused the outage rather than following from its fix. `79066c79` made the underlying claim TRUE by having the Dispatcher's overlay substitute the resolved contract values host-side, so the behaviour is now correct while the ratified wording still says the engine must be the renderer. This proposal closes that, in the direction the evidence supports.

Two further observations belong in the motivation because they explain why a static check could not catch this:

- The check compares three HOST-SIDE artifacts — the `[run.inputs]` declarations, the tokens the payload references, and the inputs the Dispatcher renders. All three agreed throughout. The engine, the only party that could disagree, was never consulted.
- `orchestrator-image/fresh-clone-setup-gate.sh` already resolved the same tokens host-side, substituting them itself before replaying the steps on a fresh clone. It reported that every conformance setup step passes, and it was right: it proved the COMMANDS work while nothing proved their DELIVERY did. A gate that reimplements a production step to test it has become a second implementation, and the divergence is invisible to it by construction.

### Proposed Changes

Amend the "Typed workflow inputs and the seam-equivalence check" clause in `SPECIFICATION/contracts.md`. The set-equality obligations are unchanged. Replace the position obligation so that every `inputs.*` token MUST sit in a position RESOLVED BEFORE THE SANDBOX EXECUTES IT, and admit exactly two resolvers: the engine, which renders declared graph attributes at run-create time; and the Dispatcher's run-config overlay, which substitutes resolved contract values into the committed run config host-side. A position resolved by NEITHER MUST fail the check.

Require the check to be resolver-aware rather than resolver-blind. For each admitted position the check MUST record which resolver it depends on, and an overlay-resolved position MUST be backed by an actual host-side substitution in the Dispatcher — so that removing that substitution turns the position back into a failing one instead of leaving a silently false classification. The engine-resolved set MUST remain evidence-bearing: a position enters it only on recorded evidence that the pinned build expands that attribute, and a numeric or typed attribute MUST NOT be admitted on the grounds that it looks like a string.

Require that overlay substitution be a projection of the SAME `ResolvedIntegrationContract` the `fabro run --input` pairs are rendered from, so the run config and the run's bound inputs cannot disagree, and that a substituted value be escaped for the syntactic context it lands in.

State the residual limit honestly in the clause rather than leaving it implied: this check answers the templating question statically for positions whose resolver is known, and it CANNOT establish that the pinned engine renders a position. That obligation belongs to recorded evidence about the engine build, and a change of pinned engine invalidates it.

Amend the scenario block in `SPECIFICATION/scenarios.md` that currently reads "A token in a position the engine does not render fails the seam-equivalence check" so that the failing condition is a position NEITHER the engine renders NOR the overlay substitutes. Add two scenarios beside it: a token in a prepare-step position is admitted and the check records the overlay as its resolver; and an overlay-resolved position whose host-side substitution has been removed fails the check naming the position and the missing substitution.

### Non-goals

This proposal does not widen the engine-rendered attribute set, does not change the set-equality obligations, and does not relax the closed-set rule on schema fields. It does not ratify the separate, still-open question of whether an unadopted repository should inherit the fleet's conformance invocations rather than the ratified no-op.
