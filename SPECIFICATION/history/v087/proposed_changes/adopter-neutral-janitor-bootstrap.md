---
topic: adopter-neutral-janitor-bootstrap
author: claude-opus-4-8:homelab-loop-hardening-orchestrator
created_at: 2026-08-29T01:28:00Z
---

## Proposal: The janitor-bootstrap step resolves a DECLARED hook-install recipe, and a one-pass audit disposes the whole step/preflight set against members-and-adopters-identical

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

Amends §"Dispatch preflight and post-merge step discipline" so the
`janitor-bootstrap` step's integration point is what the governed repository
DECLARES — a committed `dispatcher.janitor_bootstrap` key naming the hook-install
recipe — rather than a presumed livespec-dev-tooling recipe. This is the same
declaration-over-assumed-tooling shape v074 gave the `master-ci` step
(`dispatcher.master_ci`): declaration changes WHAT recipe is bootstrapped and
re-verified, never WHETHER absence of proof refuses. Fleet members keep working
unchanged through a declared DEFAULT convention.

Adds one subsection recording a one-pass audit of every step and preflight
obligation in the named closed set against the members-and-adopters-identical
principle (§"Self-contained plugin dispatch", the sentence at "Fleet members and
adopters therefore consume the orchestrator IDENTICALLY"), disposing each: two are
already adopter-neutral, one is fixed here, and the dispatch-time baseline
conformance gate's toolchain coupling is already dispositioned by the ratified
"Target-local workflow" clause.

Adds Scenario 93. Flags the `tests/heading-coverage.json` co-edit the accepting
revise pass must make for that new heading.

### Motivation

The ratified step-discipline clause presumes the governed repository ships
livespec-dev-tooling's commit-refuse-hook recipe. §"Dispatch preflight and
post-merge step discipline" defines the `janitor-bootstrap` step as "the post-merge
janitor's bootstrap of the governed repository's commit-refuse hooks", and its
cross-dispatch re-verification integration point as "the presence of the governed
repository's hook-install recipe" — concretely, the fleet's
`just install-commit-refuse-hooks` recipe, whose canonical implementation is
livespec-dev-tooling's Python packaging.

But §"Self-contained plugin dispatch" ratifies that members and adopters consume
the orchestrator IDENTICALLY — "enabling the plugin is the whole installation" —
and that same section's "Target-local workflow" clause already ratifies that
"Prepare steps are TARGET-TOOLCHAIN facts, not fleet constants ... a non-Python
adopter's equivalent steps are that adopter's own facts." The `janitor-bootstrap`
integration point contradicts that: it can only be provided by a repository that
has adopted the fleet's Python/`just` recipe, so an adopter that is not a fleet
member cannot satisfy the step except by becoming one — or by carrying a waiver.

This is not hypothetical. Adopter homelab is a Talos/Kubernetes repository with no
Python packaging and its own primary-checkout protection; it currently runs under a
`dispatcher.step_waivers` waiver (step id `janitor-bootstrap`, owner
`thewoolleyman`) paired with a restore work-item, because it has no way to PROVIDE
the presumed recipe. The waiver is the sanctioned escape for a repository that
genuinely cannot verify — but it is the wrong default answer for an adopter that DOES
have its own hook-install mechanism and simply names it differently. The obligation
should be satisfiable by DECLARATION, exactly as `master-ci` became.

The `master-ci` step had the identical defect and v074 fixed it: the preflight now
resolves the pipeline "from what the repository DECLARES" (`dispatcher.master_ci`),
uses a declared default convention when the key is absent, and its refusal names
which resolution was attempted and the key that declares it. This proposal applies
that settled pattern to the one remaining step that still presumes fleet tooling, and
records a one-pass audit so the whole closed set is dispositioned against the
principle rather than one step at a time.

### Proposed Changes

**1. Add the declared `dispatcher.janitor_bootstrap` key.** In §"Dispatch preflight
and post-merge step discipline", after the "`dispatcher.step_waivers`" paragraph and
before "Master-CI pipeline resolution", ADD a new paragraph:

> **`dispatcher.janitor_bootstrap`** (committed `.livespec.jsonc`; a `recipe` key —
> the command the post-merge janitor invokes to bootstrap the governed repository's
> commit-refuse hooks, and whose resolvability the pre-dispatch re-verification
> checks). The key describes the repository's hook-install topology, has no per-item
> override, and joins the ratified committed-configuration-only class (§"Control
> surface and audit").

**2. Add "Janitor-bootstrap recipe resolution", mirroring "Master-CI pipeline
resolution".** Immediately after the "Master-CI pipeline resolution" paragraph, ADD:

> **Janitor-bootstrap recipe resolution.** The `janitor-bootstrap` step MUST resolve
> the governed repository's commit-refuse-hook install recipe from what the
> repository DECLARES: the committed `dispatcher.janitor_bootstrap` key's `recipe`
> value. The post-merge janitor MUST invoke that declared recipe to bootstrap the
> hooks, and the pre-dispatch re-verification named above MUST check that the
> declared recipe is resolvable in the governed repository (present and invokable) —
> the integration point whose provision clears a prior degraded outcome and whose
> absence refuses the next dispatch. When the key is absent, resolution MUST use the
> fleet default convention (`just install-commit-refuse-hooks`) — a declared default,
> not a silent assumption: a refusal for an unresolvable recipe MUST say which
> resolution was attempted (declared or default) and name the key that declares it.
> Declaration changes WHAT recipe is bootstrapped and re-verified, never WHETHER
> absence of proof refuses; a repository whose declared or default recipe is
> unresolvable is a journaled degraded/refused outcome under the rules above, and an
> adopter that genuinely provides no such recipe carries a `janitor-bootstrap` step
> waiver (the sanctioned escape, unchanged). This is the same
> declaration-over-assumed-tooling shape §"Master-CI pipeline resolution" gives the
> `master-ci` step.

**3. Amend the re-verification integration-point clause to name the declared
recipe.** In the "Cross-dispatch persistence" bullet, the parenthetical currently
reads:

> for `janitor-bootstrap` that is the presence of the governed repository's
> hook-install recipe

REPLACE it with:

> for `janitor-bootstrap` that is the resolvability of the governed repository's
> DECLARED hook-install recipe (`dispatcher.janitor_bootstrap.recipe`, or the fleet
> default convention when undeclared), per "Janitor-bootstrap recipe resolution"
> below

**4. Add the members-and-adopters-identical audit disposition.** At the END of
§"Dispatch preflight and post-merge step discipline", ADD a new subsection:

> **Members-and-adopters-identical audit of the step and preflight set.** Every
> obligation in the named closed step set, and the dispatch-time preflight chain that
> feeds it, is dispositioned here against the principle that members and adopters
> consume the orchestrator IDENTICALLY (§"Self-contained plugin dispatch"):
>
> - `source-checkout` (pre-dispatch): adopter-neutral as written. It verifies the
>   presence of a source checkout — a generic git fact carrying no fleet-toolchain
>   assumption. No change.
> - `master-ci` (pre-dispatch): made declaration-based by v074 via
>   `dispatcher.master_ci` with a declared default convention. Adopter-neutral. No
>   further change.
> - `janitor-bootstrap` (post-merge, with pre-dispatch re-verification): made
>   declaration-based by this clause via `dispatcher.janitor_bootstrap` with a
>   declared default convention.
> - The dispatch-time baseline conformance gate (§"Dispatch-time baseline conformance
>   gate"): its `uv sync` prepare step, its `livespec_dev_tooling` Verifiers, and the
>   canonical commit-refuse hook it installs are the FLEET toolchain realization.
>   §"Self-contained plugin dispatch" → "Target-local workflow" already ratifies that
>   prepare steps are target-toolchain facts and that an adopter MAY carry its own
>   `implement-work-item` workflow with its own prepare chain; the declared
>   `dispatcher.janitor_bootstrap.recipe` is the janitor-side analogue of that
>   already-ratified disposition. Already dispositioned; no change here.
>
> The set is closed: extending it, or adding a new dispatch-time or post-merge
> obligation, requires ratification and MUST carry its own members-and-adopters
> disposition at that time.

### Scenario additions

Add to `SPECIFICATION/scenarios.md`:

## Scenario 93 — The janitor-bootstrap step resolves a declared hook-install recipe and falls back to a declared default

GIVEN a governed repository whose committed `dispatcher.janitor_bootstrap.recipe` names a hook-install command that is present and invokable
WHEN the pre-dispatch re-verification of the janitor-bootstrap integration point runs
THEN it resolves the declared recipe, observes it provided, and journals a clearing record for any prior degraded janitor-bootstrap outcome
AND a governed repository that declares no `dispatcher.janitor_bootstrap` key is re-verified against the fleet default convention `just install-commit-refuse-hooks`
AND when the declared or default recipe is unresolvable the refusal names which resolution was attempted and the key that declares it, rather than proceeding unchecked
AND an adopter that provides no such recipe satisfies the step through a committed janitor-bootstrap step waiver rather than by adopting the fleet toolchain

### What this proposal deliberately does NOT do

It does NOT remove or weaken the `janitor-bootstrap` step, its degraded-outcome
persistence, or the hard cross-dispatch refusal. The refusal mechanism is unchanged;
only the integration point it verifies becomes declaration-resolved.

It does NOT change the `dispatcher.step_waivers` escape. The waiver remains the
sanctioned answer for a repository that genuinely cannot provide any hook-install
recipe; this proposal adds a declaration route beside it, not in place of it.

It does NOT alter the dispatch-time baseline conformance gate or its
`livespec_dev_tooling` Verifiers. The audit records that gate's toolchain coupling as
ALREADY dispositioned by the ratified "Target-local workflow" clause; making the
adopter's sandbox prepare chain itself declaration-driven is separate work under that
clause, not this one.

It does NOT set the concrete schema or validation of `dispatcher.janitor_bootstrap`
beyond the `recipe` string; the committed-configuration-only class and the absence of
a per-item override are stated, and the rest is an implementation detail carried by
the ratified clause's gap-capture children.

It does NOT touch the other pending proposal under `proposed_changes/`; the
`master-ci` and `source-checkout` steps are amended by reference to their ratified
text only.

### Required co-edit

The accepting revise pass MUST add an entry to `tests/heading-coverage.json` for the
new H2 heading "Scenario 93 — The janitor-bootstrap step resolves a declared
hook-install recipe and falls back to a declared default", per the revise co-edit
discipline. No existing H2 heading in `contracts.md` is added, renamed, or removed by
this proposal — the `contracts.md` amendments insert paragraphs and one subsection
under the existing §"Dispatch preflight and post-merge step discipline" heading.
