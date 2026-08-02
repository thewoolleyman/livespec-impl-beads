---
topic: pin-host-direct-dispatch-to-release
author: claude-opus-5
created_at: 2026-08-02T02:29:27Z
---

## Proposal: Pin host-side Dispatcher execution to a released payload and make self-update a version comparison

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

Pin host-direct Dispatcher execution to a RELEASED payload, define self-update as a running-release vs latest-release comparison with a canary of the new release before promotion, and retire the clause that specifies a self-update canary skip for the no-writable-orchestrator-checkout case. `contracts.md` §"Self-contained plugin dispatch" already ratifies self-containment and identical consumption by fleet members and adopters; what it does not yet say is that the payload the host-side Dispatcher executes must have passed versioning and the release gates. This change says it, and in doing so retires the writable-orchestrator-checkout execution mode the current degradation clause accommodates. One new `scenarios.md` scenario and its `tests/heading-coverage.json` entry are added, because the change introduces BCP14 clauses about observable behavior.

### Motivation

Maintainer ruling, 2026-08-02, recorded on ledger epic `bd-ib-4zif` and its spec slice `bd-ib-4zif.1`: the orchestrator has standardized releases — semantic commits, versions, release-please, CI gates before a release is cut — and a dispatcher version should only be usable once it is past all of that. Comparing git SHAs and merged file lists against a local checkout should therefore be irrelevant; the only comparison that should matter is the currently running RELEASE against the proposed RELEASE.

WHAT IS ACTUALLY TRUE OF THE SPEC TODAY, stated precisely so this proposal is not read as claiming more than it can support. §"Self-contained plugin dispatch" DOES ratify self-containment: the host-side Dispatcher "MUST run on the packaged payload alone ... with no dependency on an orchestrator working checkout and no `pyproject.toml` / lockfile install step". It DOES ratify identical consumption: "Fleet members and adopters therefore consume the orchestrator IDENTICALLY — enabling the plugin is the whole installation." It does NOT mention releases, versions, or tags anywhere. And its degradation sentence PRESUPPOSES that a writable checkout may exist — requiring checkout-presupposing behaviors to no-op when one is ABSENT implies they may act when one is PRESENT. So the current host-direct behavior is ACCOMMODATED by the ratified text, not forbidden by it. This proposal therefore RETIRES AN ACCOMMODATION rather than correcting a violation.

THE TENSION THAT JUSTIFIES RETIRING IT is the identical-consumption sentence. There are two execution paths today, and they are not the same product. `_dispatcher_paths.plugin_root()` returns `$CLAUDE_PLUGIN_ROOT` when set, else `Path(__file__).resolve().parents[3]`. Under the plugin cache that root has no `.git`, so `is_writable_orchestrator_checkout()` is False and the self-update layer returns immediately at its read-only guard — no self-merge detection, no canary, no SHA comparison. Invoked from a source tree with the variable unset, the same function resolves into a writable checkout, the guard does not fire, and a second checkout-dependent mode runs instead. An adopter and a fleet member are therefore not consuming the orchestrator identically, which is the thing the section says they do.

WHAT CHANGES IS THE TRIGGER, NOT THE SAFETY GATE — and the distinction is load-bearing. The self-update layer was built (work-item 0jxs) because the post-merge stage runs `git pull --ff-only origin <default-branch>` against the dispatch TARGET, and when the target IS this orchestrator that pull fast-forwards the very tree the running dispatcher's code is loaded from — swapping code mid-loop before any release is cut. Release pinning removes THAT hazard at its source. It does NOT make the layer's canary redundant, and this proposal does not treat it as redundant.

THE CANARY IS KEPT, AND STATED MORE PLAINLY THAN TODAY, because nothing else covers what it covers. `canary_self_check_argv` runs `python3 <candidate>/bin/dispatcher.py ledger-check --json --project-root <empty scratch>` — by its own docstring touching no real ledger, no fabro, and no network. It is a smoke test of the import graph, argument parsing, and check pipeline. Thin, but it is the ONLY thing that executes the actual artifact, on the actual host, with the actual `python3`, before that artifact takes over the loop. Scope searched — all of `.github/` and the `justfile`: `ledger-check` appears in ZERO gates; `dispatcher.py` is executed by exactly one gate line (`justfile:742`), which runs a DIFFERENT subcommand (`ledger-normalize --gate`) from the repo layout rather than from a staged candidate; and `acceptance-live-golden-master.yml` is `workflow_dispatch` / `repository_dispatch` only, requires a privileged DinD host, and is referenced by nothing, so it is not in the release path. CI therefore never runs the candidate binary and never exercises the packaged-payload layout. Retiring the canary on the theory that the release pipeline supersedes it would be false and would reduce coverage; only the TRIGGER is retired.

AND THE MITIGATION HAS NEVER WORKED ON THE PATH IT PROTECTS, which is why repairing it is not the answer. `resolve_merged_paths` derives the PR to inspect from the checkout's current HEAD branch, but the post-merge pull has already moved HEAD to the default branch, so it runs `gh pr view <default-branch> --json files`, which exits 1 ("no pull requests found for branch ..."), which yields an empty tuple, which `is_self_merge` reports as not-a-self-merge. Measured 2026-07-30: the dispatch of `bd-ib-vmve.2` — whose merge changed five files under the first `DISPATCHER_SCRIPT_PREFIXES` entry — journalled "merge did not touch the dispatcher's own scripts". The module's own comment states the stakes: "a false NEGATIVE would let a bricking self-merge promote unguarded." A second defect compounds it: the empty tuple means both "touched nothing of ours" and "could not observe", and both journal the same confident sentence, so the layer reports a definite finding it does not have.

SCOPE. This proposal does not redesign the release pipeline, does not touch release-please or any workflow, and does not change the plugin-cache path, which already behaves as specified. It also does not specify a repair to the detector: the point is to make the detector unnecessary so the implementation slice can delete it. Full analysis and the evidence for every measurement above: ledger epic `bd-ib-4zif`.

### Proposed Changes

All anchors below were verified byte-exact against `SPECIFICATION/contracts.md`
on `origin/master` (`8e5a24e`) on 2026-08-02; each quoted block matches exactly
once. Line numbers are navigational only.

Every edit is inside `## Self-contained plugin dispatch` (H2 at line 1094). The
H2 heading text is NOT changed, so its existing `tests/heading-coverage.json`
entry needs no edit; the new scenario in edit (D) DOES require a new entry.

---

### (A) Replace the degradation paragraph: state release-pinned execution and
retire the canary-skip clause

Replace verbatim:

> The host-side Dispatcher MUST run on the packaged payload alone — the
> Python standard library plus the vendored runtime under
> `scripts/_vendor/` — with no dependency on an orchestrator working
> checkout and no `pyproject.toml` / lockfile install step. Behaviors that
> presuppose a writable orchestrator checkout or fleet context MUST degrade
> to clean no-ops rather than failing the dispatch: the post-merge
> self-update canary records an explicit skip when there is no writable
> orchestrator checkout to promote, and the fleet-manifest sibling-clone
> projection renders empty when no fleet manifest is present.

with:

> The host-side Dispatcher MUST run on the packaged payload alone — the
> Python standard library plus the vendored runtime under
> `scripts/_vendor/` — with no dependency on an orchestrator working
> checkout and no `pyproject.toml` / lockfile install step. That payload MUST
> be a RELEASED version: one that has passed semantic-commit versioning, the
> repository's CI gates, and the release cut. The Dispatcher MUST NOT execute
> from an orchestrator working tree, and MUST NOT treat the presence of a
> writable orchestrator checkout as a reason to behave differently. Release
> pinning is the single execution mode — there is no second, checkout-dependent
> mode to degrade from.
>
> The pin is the installed plugin payload the operator has provisioned (the
> plugin root, `${CLAUDE_PLUGIN_ROOT}`), which is keyed by the released commit.
> It satisfies the packaged-payload rule by construction: it carries
> `scripts/bin/`, the vendored runtime, and the `.fabro/` workflow, and it
> carries no `pyproject.toml` and no lockfile, so it cannot require an install
> step. Because that payload is not a git working tree, no promotion into it is
> possible and none is attempted.
>
> Behaviors that presuppose fleet context MUST still degrade to clean no-ops
> rather than failing the dispatch: the fleet-manifest sibling-clone projection
> renders empty when no fleet manifest is present.

Three things this does: it adds the released-version requirement; it deletes the
self-update-canary skip clause, which describes a branch that no longer exists
once there is no writable-checkout mode; and it keeps the fleet-manifest sibling
clause, which is unrelated and still true.

### (B) Add a paragraph defining self-update as a version comparison

Insert immediately after the paragraph replaced in (A):

> **Self-update triggers on a version comparison, and every promotion is
> canaried.** When the Dispatcher considers updating itself it MUST compare the
> RUNNING RELEASE against the latest available RELEASE. It MUST NOT compare git
> commit SHAs, branch names, or merged file lists against a local checkout —
> those are properties of a working tree, which the Dispatcher no longer executes
> from.
>
> A candidate release MUST NOT become the running version until a CANARY of that
> candidate has passed. The canary MUST execute the CANDIDATE ARTIFACT ITSELF, on
> the host that will run it, using the same interpreter and the same packaged
> layout it will run under, and it MUST exercise at minimum the candidate's
> import graph, its argument parsing, and its check pipeline end-to-end. It MUST
> remain side-effect-free: no real ledger, no engine run, no network. A PASSING
> canary is the only thing that MAY promote a candidate. A FAILING canary MUST
> keep the last-known-good running release AND MUST alarm a human; it MUST NOT
> promote, and it MUST NOT be downgraded to a warning or skipped.
>
> The Dispatcher MUST NOT infer that an update is unnecessary from an
> unobservable signal: when it cannot determine the available release, it MUST
> record that it could not determine it, distinctly from recording that no update
> was available.

Two of these sentences are deliberate and should not be softened in review.

The canary requirement is stated more strongly than the text it replaces, not
less. Nothing else in this repository executes the candidate artifact before it
takes over the loop: `ledger-check` appears in no CI gate, the single gate line
that runs `dispatcher.py` (`justfile:742`) runs a different subcommand from the
repo layout rather than from a candidate, and the only end-to-end workflow is
manual-only and unreferenced. Whatever else changes, this coverage must not
shrink.

The unobservable-signal sentence closes the defect that hid the old mechanism:
it collapsed "nothing to do" and "could not tell" into one indistinguishable
journal outcome, so a permanently-blind detector looked healthy for its entire
service life.

### (C) State the operator consequence

Append to the same paragraph block, so the behavior change is stated rather than
discovered:

> Operator consequence: a host-side dispatch runs the last RELEASE the operator
> has provisioned, not the current working tree. An unreleased local edit does
> NOT take effect on the dispatch path until it is released and the operator's
> payload is updated. This is intended — a dispatcher version becomes usable only
> once it is past versioning and the release gates — and it applies to fleet
> members and adopters identically.

### (D) Add a paired scenario

Edits (A)–(C) introduce BCP14 clauses about observable behavior, and behavioral
prose with no scenario is malformed under this project's authoring discipline.
No existing scenario covers self-contained plugin dispatch, self-update, or the
canary (verified across `scenarios.md` on `origin/master` 2026-08-02; the only
"canary" match is Scenario 21's Codex companion canary, which is unrelated).

Append to `scenarios.md`, using the file's dominant fenced-gherkin convention:

> ## Scenario 54 — Host-side dispatch runs a released payload, never the working tree
>
> ```gherkin
> Feature: The host-side Dispatcher executes a released payload, so a dispatcher
>   version is usable only once it is past versioning and the release gates
>
>   Scenario: An unreleased working-tree edit does not take effect on the dispatch path
>     Given an orchestrator working checkout carrying an unreleased local edit
>     And a provisioned released payload that does not carry that edit
>     When a host-side dispatch runs
>     Then the dispatch executes the released payload
>     And the unreleased working-tree edit has no effect on it
>     And no promotion into an orchestrator working tree is attempted
>
>   Scenario: A newer release is canaried before it is promoted
>     Given a running release and a newer available release
>     When the Dispatcher evaluates whether to update itself
>     Then it compares the running release against the available release
>     And it validates the newer release with a canary before promoting it
>     And a failing canary keeps the running release and surfaces the failure to a human
>
>   Scenario: An undeterminable available release is recorded as undetermined
>     Given the available release cannot be determined
>     When the Dispatcher evaluates whether to update itself
>     Then it records that the available release could not be determined
>     And that record is distinguishable from recording that no update was available
> ```

54 is the next free number (the highest live scenario is 53).

### (E) Required co-edit — `tests/heading-coverage.json`

Adding one `## ` heading to `scenarios.md` requires the map to be updated in the
SAME change via the revise pass's `resulting_files[]` mechanism. Add ONE entry
for `"## Scenario 54 — Host-side dispatch runs a released payload, never the
working tree"` with `spec_root` `SPECIFICATION`, `spec_file` `scenarios.md`,
`test` `"TODO"`, and a non-empty `reason` recording that the exercising test
lands with the implementation slice `bd-ib-4zif.2`.

No entry is removed. The existing `## Self-contained plugin dispatch` entry is
untouched because that H2's text does not change. The map is H2-keyed (89 entries
as of 2026-08-02).

Note for whoever applies this: `resulting_files[].path` is spec-target-relative,
so the map is reached as `../tests/heading-coverage.json`.

---

### Explicitly NOT changed

- The release pipeline, `release-please`, and every file under
  `.github/workflows/`. This proposal consumes releases; it does not alter how
  they are produced.
- The plugin-cache execution path, which already behaves as specified.
- The post-merge refresh of the dispatch TARGET repository
  (`git pull --ff-only origin <default-branch>` against the target). That
  refresh is correct and stays; the hazard was only that on a self-dispatch the
  running dispatcher's own code lived in that same tree, which release pinning
  removes.
- §"Default-branch resolution", §"Target-local workflow", §"Per-tenant engine
  identity", and the credential paragraphs of this section.
- Any prescription for repairing the retired detector. The implementation slice
  DELETES it; specifying a repair would defeat the purpose.
