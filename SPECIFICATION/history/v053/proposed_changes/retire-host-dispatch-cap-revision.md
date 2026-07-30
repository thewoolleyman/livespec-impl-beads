---
proposal: retire-host-dispatch-cap.md
decision: accept
revised_at: 2026-07-30T11:26:28Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5
---

## Decision and Rationale

ACCEPTED as filed, unmodified. Ratifies ledger item bd-ib-vmve.1 (epic bd-ib-vmve, plan thread plan/retire-host-dispatch-cap/) on the maintainer's explicit 2026-07-30 ruling.

The Orchestrator's client-side host-level dispatch concurrency cap duplicated a limit the Fabro server already enforces — `server.scheduler.max_concurrent_runs`, in the long-lived daemon that owns runs — and did so worse in three measured ways. (1) The value never reached the factory: it was resolved per dispatch, consumed inside the short-lived dispatcher process, and absent from the `fabro run` argv. (2) It applied a PER-REPO threshold to a HOST-WIDE count, because the in-flight gauge filtered on run status kind only and never read a run's source directory or repo origin; measured 2026-07-30, host-wide in-flight was 3 with all three runs belonging to one repo, and a second repo capped at 2 was REFUSED with zero runs of its own in flight. Unequal thresholds turn that into starvation rather than unfairness, since the higher-capped repo refills the host each time it drains. The deleted section conceded the model in its own words: "the host is bounded at 2 only while every dispatching repo commits (or defaults to) 2." (3) It was set BELOW the factory's real capacity — client default 2 against a scheduler limit of 5, since raised to 10 — so it throttled the factory rather than protecting it.

The deleted section's own justification did not hold either. It called 2 "the empirically verified safe level", but 2 was the level EXERCISED, never a level at which 3 was shown to fail; and the originating concern was falsified by its own diagnosis leg (bd-ib-tyxzhv), which found the `bwrap` namespace EPERM to be a host sysctl constant reproducible in a SINGLE container and the host-network port-collision premise to be false. No contended host resource was ever identified.

Nothing new is built to replace it. Host throughput is stated positively as the Fabro scheduler's job, which queues excess runs as `runnable` and promotes them FIFO — three properties the client cap lacked: it queues instead of refusing, it is FIFO across all repos, and it is enforced by the process that knows what is running.

Intent-preservation gate: CLEAR — no contradiction to name. The proposal touches two load-bearing definitions that cite a design record, and departs from neither. The per-item-override ruling (repo thewoolleyman/livespec, plan/archive/autonomous-mode/handoff.md, "SESSION UPDATE — 2026-07-14 (cont. 12)" plus its CORRECTION / ADDENDUM) rules that every dispatcher setting is per-item overridable EXCEPT `wip_cap`; removing `host_dispatch_cap` leaves that ruling exactly as stated, and the surviving subsection is renamed to match reality (one setting, not two) rather than re-scoped. The `wip_cap`-of-0 dispatch-off blessing (v049) is preserved verbatim; only its carve-out sentence naming the removed key is dropped, because a carve-out cannot name a key that no longer exists. The cap's own design record (bd-ib-sd8o deliverable (b), ratified v047) is superseded deliberately and by the same maintainer authority that established it, on evidence its own diagnosis leg produced.

SCOPE HELD. `wip_cap` is untouched in value (5), scope (per-repo), per-item-override shape (false), and value domain (non-negative integer, `0` = dispatch-off). The enforcement asymmetry whereby the drain loop honors the cap and a hand-picked `dispatch --item` deliberately bypasses it is INTENTIONAL per the same 2026-07-30 ruling and is explicitly out of scope here; it is filed separately as a spec-documentation gap, since the `contracts.md` clause currently states the bound without that carve-out. The proposal does not make the removed cap per-repo-aware, does not raise it, and does not retain a thinner pre-check — all three were considered and rejected.

Behavior/scenario discipline: edit (C) introduces BCP14 `MUST NOT` clauses, so `## Scenario 49` is deleted (all four of its scenarios) and a paired `## Scenario 53` is added covering the no-host-cap behavior. Behavioral prose with no scenario would be malformed. Scenario 49's number is left as a gap rather than renumbering downstream scenarios — the file already carries gaps at 2 and 3, and no reference to "Scenario 49" survives outside frozen history. `tests/heading-coverage.json` is co-edited in this same pass: the Scenario 49 entry is removed and a Scenario 53 entry added with test `TODO` and a reason binding it to an integration-tier test landing with bd-ib-vmve.2.

SELECTIVE PASS. This revise processes ONLY this proposal. `set-workflow-scope-override-spec-coverage.md` is deliberately LEFT PENDING: it belongs to the plan/factory-hardening thread and is not this thread's to accept or reject.

## Resulting Changes

- contracts.md
- scenarios.md
- spec.md
- ../tests/heading-coverage.json
