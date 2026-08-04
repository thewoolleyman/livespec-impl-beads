---
topic: plan-thread-tombstone-ban
author: claude-opus-5
created_at: 2026-08-04T13:34:20Z
---

## Proposal: The Planning Lane realization MUST forbid any residue at an archived thread's live path

### Target specification files

- SPECIFICATION/contracts.md

### Summary

§"Planning Lane realization" → "Archive on epic close" realizes core's lifecycle binding and shows the `git mv`, but it does not say that the move must leave NOTHING behind. This proposal adds the totality rule as a STATE invariant, the two sanctioned dispositions when a thread would close with something unresolved, and the mechanical reason. It is the realization half of the same clause proposed against core's Planning Lane guidance, and it matters more here than there, because this is the tree whose `plan` operation an agent actually executes at archive time. It carries a ratification co-edit to the operation prose, via the revise `resulting_files[]` mechanism.

### Motivation

A rule that lives only in core's guidance is a rule the acting agent never reads. The `plan` operation's own prose is what runs; if the prohibition is absent from the realization, an agent finishing a thread with one loose end will invent the obvious accommodation — archive the directory, leave a note at the old path saying where it went — and that accommodation is the defect.

It is not hypothetical. Measured in `livespec-overseer` on 2026-08-04: an archived thread was RESTARTED 1h02m after its archive merged, and another 4h19m after, then nudged again 14h10m after it was finished. The Control-Plane consumer discovers threads and tests archival at DIRECTORY granularity, so residue at `plan/<topic>/` keeps a finished thread reading as ACTIVE and its bookkeeping is never reclaimed.

The one measured tombstone in the fleet is worth naming precisely, because the obvious guess about it is wrong. It was the WORKER `handoff.md` stub, left so that the daemon's stored worker resume line would resolve to something rather than to a missing file; the hosted supervisor artifact beside it had already been archived correctly. So the defect this clause prevents is not a supervisor-respawn problem — it is that a stub serving the worker resume path keeps the whole directory alive and thereby defeats the archive GC for the thread as a whole.

That also disposes of the objection that totality breaks supervision of an archived thread. It does not. With nothing at the live path the archived-or-deleted test reports the plan archived, the next acting tick drops the worker's mapping row, and the supervisor pair member is a per-tick PROJECTION off that worker row rather than a store row of its own — so supervision terminates with the row and no supervisor prompt is built afterwards. In the pre-GC window only, a supervisor `ready` meets a fail-closed refusal, which is the correct terminal behaviour for a supervisor of a FINISHED thread. Keeping that prompt resolving forever is the measured defect, not the fix.

**Why this is stated as a STATE invariant.** The mechanical backstop that ships for this ban fails on any topic present at BOTH `plan/<topic>/` and `plan/archive/<topic>/`, unconditionally — a directory-name intersection, fail-closed, no opt-in lever, no content read. It cannot distinguish residue from a NEW thread reusing a retired slug while the old archive remains. An event-only rule would permit that reuse and hand the repo a permanently red gate, so the realization states the invariant the gate actually enforces.

Note what is NOT residue, since the distinction is the whole content of the rule: reopening an epic unarchives its thread by moving the directory BACK, which leaves nothing in the archive; and deliberately relocating a research note to a living home is a move. Both are moves. A stub is a copy left behind.

### Proposed Changes

In `contracts.md` §"Planning Lane realization" → "Archive on epic close", insert the blockquoted text below beside the existing `git mv`. That text is the clause verbatim (quote markers stripped when landed); nothing else in this proposal is to be landed.

> Archival MUST be TOTAL: the whole directory is relocated and NOTHING remains
> at `plan/<topic>/` — no stub, terminal marker, forwarding note, or other
> residue, and not the directory itself, even empty. The `plan` operation MUST
> NOT create one, and MUST NOT treat one as an acceptable outcome of an
> archive it performs.
>
> This is a STATE invariant, not only a rule about the moment of archival: in
> no committed tree, from this clause's ratification forward, may the same
> topic exist at both `plan/<topic>/` and `plan/archive/<topic>/`. A retired
> topic's slug is consequently NOT reused for a new thread while its archive
> remains — choose a new slug; or, if the new work genuinely continues the old
> thread, REOPEN ITS EPIC, which unarchives the thread by moving it back.
> Moving an archived thread back WITHOUT reopening its epic is forbidden: it
> produces an active `plan/<topic>/` whose epic is closed, contradicting the
> if-and-only-if binding this section states.
>
> The mechanism belongs with the rule. Control-Plane consumers of this lane
> discover plan threads and test archival at DIRECTORY granularity, so residue
> that keeps the live directory in existence makes a finished thread read as
> ACTIVE, its mapping bookkeeping is never reclaimed, and it stays eligible for
> nudges, wrap-up injection and RESTART.
>
> When a plan thread would close with anything unresolved, exactly ONE of two
> dispositions is sanctioned. Either the thread is LEFT UN-ARCHIVED — its epic
> staying OPEN, so the lifecycle binding continues to hold — until its
> blockers are resolved; or ALL of its blockers are TRANSFERRED to a different
> or new NON-ARCHIVED plan thread and/or work-item, after which the thread is
> archived whole. A work-item transfer goes through `capture-work-item`, per
> the *plan → work* seam, never a direct cross-plane store write; a transfer
> into another plan thread is an ordinary plan-store edit and stays in-plane.
> Archiving the thread and leaving a note saying what is left is not a third
> option.
>
> Nothing here narrows the clauses beside it. Reopening an epic still
> unarchives by moving BACK, which leaves nothing in the archive and is not
> residue. `supervisor-handoff.md` still archives and unarchives WITH its
> thread — an instance of this totality rule rather than an exception to it.
> The at-most-one-handoff refusal, the prohibition on a root `research/` tree,
> and the sanctioned relocation of a research note to a living home in
> `docs/`, `.ai/`, or a dedicated top-level topic directory are all
> unaffected.

The clause adds no new `## ` heading and renames none.

### Ratification co-edit (via the revise `resulting_files[]` mechanism, not a second proposal)

`.claude-plugin/prose/plan.md` §"Step 5 — Archive on epic close" is the operation prose an agent actually reads at archive time. It currently shows the `git mv` and says reopening moves back, but says nothing about residue. It MUST carry the same prohibition, the same state invariant, and the same two dispositions, landed in this revise payload — a ratified contract the acting prose does not repeat is a contract the acting agent never sees. The prose is harness-neutral and shared by both the Claude and Codex surfaces, so one edit covers both. Precedent for co-editing this exact file through `resulting_files[]` rather than a second proposal: `SPECIFICATION/history/v048/proposed_changes/supervisor-handoff-hosted-artifact-in-the-thread-store.md`.
