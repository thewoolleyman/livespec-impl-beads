# 004 — Ratifications v071–v078, the implementation children, and what remains

Written 2026-08-25 by the `homelab-loop-hardening-orchestrator` session,
closing the same-day arc research/001–003 opened. All EIGHT Phase 2
propose-changes are RATIFIED through the delegated in-session revise
lifecycle (authority recorded on the epic, citing homelab/hl-nkuzaz;
`spec_governance` arms `revise_decision_mode: delegated` +
`ratification_review: auto-spawn`/sonnet), each with an independent
sonnet ratification review at literal NO BLOCKERS on the exact final
bytes, each cut as its own history snapshot through its own PR:

| vNNN | Topic | PR |
|---|---|---|
| v071 | acceptance-rework-state-machine — §"Rework-pending re-dispatch" + one-meaning-of-`active` co-edits + door-rules refresh | #1836 |
| v072 | needs-attention-verdict — four verdicts + evidence rule, §"Effective acceptance criteria", walls (exit 5), §"Dispatcher exit codes" | #1838 |
| v073 | journal-invoker-attribution — §"Journal invoker attribution" + Control-surface scoping amendment | #1840 |
| v074 | dispatch-preflight-persistence — §"Dispatch preflight and post-merge step discipline" + declared master-CI | #1842 |
| v075 | temporary-setting-restore — §"Temporary setting postures carry an owned restore item" | #1844 |
| v076 | loop-probe — §"The loop probe (`probe --item`)" | #1846 |
| v077 | needs-attention-envelope — §"The needs-attention machine envelope" (runtime-baseline gate satisfied by livespec-runtime v012, 970eea1; citations re-verified) | #1848 |
| v078 | detector-coverage-records — §"Detection coverage records and staleness facts" (reviewer blocker on the committed-marker phrase fixed and re-checked) | #1850 |

Process notes a successor should know:

- The owned-TODO release tier the runtime session warned about DOES arm
  here when a changeset AUTHORS an unowned heading-coverage TODO
  (`dev-tooling/just-check-pre-commit-doc-only.sh`); every scenario TODO
  this arc authored is owned by `bd-ib-w3if5j` and carries the
  integration-tier reason phrase the heading-coverage check requires.
- The per-pass LLM doctor and capture-impl-gaps post-steps were
  explicitly skipped per pass (sanctioned flags) in favor of one
  consolidated disposition, recorded next.
- The DCR ratification reviewer found one REAL blocker (the
  committed-marker phrase applied to an API-configurable key) — evidence
  the auto-spawn review is load-bearing, not ceremonial.

**The consolidated detection disposition.** `detect-impl-gaps
--since-version v070 --json` returns **397** gap candidates — the
changed-file scoping blow-up the ratified v078 caution predicts
(contracts.md and scenarios.md changed, so every live clause in both
resurfaces). Per the v078 contract itself, NO completed-coverage point
is claimable from this: a completed record requires every surfaced
candidate durably disposed, which a 397-candidate set does not get
today. The implementation children below were therefore filed
EXPLICITLY (freeform, plan children, scope event of 2026-08-25) rather
than through a 397-consent dialogue; the gap-staleness backstop, once
implemented (bd-ib-e74ugp), will correctly keep detection staleness
visible until a full pass disposes its scope.

**The ten implementation children** (all `backlog`, parent
bd-ib-ujihbw, factory-safe; edges: bd-ib-tokosl blocks-on bd-ib-mrsply;
bd-ib-qtuvin blocks-on bd-ib-tfpdya per the ratified wall gate):

- bd-ib-mrsply — stamp + materialize rework:pending (v071)
- bd-ib-tokosl — execute rework re-dispatch (v071)
- bd-ib-i475z7 — widen acceptance verdicts to the evidence rule (v072)
- bd-ib-qtuvin — effective-criteria primitive + walls (v072)
- bd-ib-vwwlwp — invoker attribution + append chokepoint (v073)
- bd-ib-6mnyq4 — step discipline: ids, persistence, waivers (v074)
- bd-ib-u7nrue — master-CI declared resolution + fail-open retirement (v074)
- bd-ib-mvvx5y — the loop probe subcommand (v076)
- bd-ib-r4erae — producer-side envelope conformance (v077; the
  advertiser/enforcer mechanical binding stays bd-ib-dohu2g's)
- bd-ib-e74ugp — detection coverage records + staleness facts (v078)

Plus bd-ib-w3if5j (scenario-test bindings for 66–84, owns the TODO
heading-coverage entries).

**The ninth filing** is PENDING: `needs-attention-completeness`
(PR #1852) — matrix §§03/10/11 per 009 R1, riding the ratified
`hygiene:<type>:<resource>` grammar with zero runtime change, adding
API-configurable `dispatcher.ready_aging_threshold_hours` (default 24).
It takes the same adversarial-review → delegated-revise path as the
eight before it.

**Runtime facts carried** (from the coordinator's unblock report):
livespec-runtime v012 ratifies kind-prefix lockstep and composition
completeness as invariants its implementation does not yet satisfy
(carriers livespec-runtime-wfl, -emu) — reference the semantics, do not
assume conforming producer behavior; NO runtime release is cut — the
vendored pin stays v0.21.1 until the runtime's ordered fan-out reaches
this repo through the blessed pin-bump path.
