---
proposal: codex-config-shell-quoting.md
decision: accept
revised_at: 2026-08-27T04:22:50Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: claude-opus-5
---

## Decision and Rationale

Accepted after a two-leg independent adversarial review (claude + codex) that both returned do-not-ratify-as-written and converged on the same two blockers, and after every finding from both legs was repaired in the proposal. The requirement lands on the general adapter rendering contract as a round-trip property of every env value rather than as a per-key single-quote wrap, because adapter env values are operator-supplied and unvalidated and a naive wrap is defeated by an apostrophe. The 'rendered verbatim' sentence is adjusted to value fidelity so the two clauses no longer contradict. The three Codex literals gain one quote pair each and are otherwise byte-unchanged, and Scenario 90 gains the one assertion that can catch a regression on the pinned path, which previously had no coverage of the property being ratified. Triage: plan/homelab-loop-hardening-orchestrator/research/009-codex-config-shell-quoting-review-triage.md. Prior art: bd-ib-qulf.

## Resulting Changes

- contracts.md
- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: sonnet
reviewer_identity: sonnet
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-27T04:22:38Z
verdict: NO BLOCKERS
proposal_stem: codex-config-shell-quoting
content_digest: e6446b2412a6a86860557e92d7ad4ce9c292f9eb94dead65ae7d9bc76fec24c2
