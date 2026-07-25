# Supervisor charter — factory-success-rate-remediation

**Supervised target:** tmux session `factory-success-rate-remediation` (default socket)
running a Claude session (Fable 5, xhigh effort). OBSERVED CORRECTION (2026-07-23): the
session's working directory is `/data/projects/livespec-orchestrator-beads-fabro`, not
`/data/projects/livespec` — the plan thread lives at
`/data/projects/livespec-orchestrator-beads-fabro/plan/factory-success-rate-remediation/handoff.md`.
**Supervisor session:** tmux `factory-success-rate-remediation-supervisor` (this one).
**Supervisor working dir:** `/data/projects/livespec/tmp/factory-success-rate-remediation-supervisor/`
(evidence packets, drafts, status.log for the supervised session's event stream).

## Mission

**PRIME DIRECTIVE (maintainer-stated): keep the supervised session moving with NO stalls
and NO blockers unless human input is genuinely needed.** An idle supervised session is a
supervision failure unless it is blocked on a decision only the maintainer can make. Watch
for idleness, self-inflicted waits, and questions that are actually answerable by research
or measurement — convert each back into motion. Escalate to the maintainer ONLY what
survives the vetting rubric below.

1. Keep the supervised session doing autonomous, high-value, in-scope work — including
   decision-PREP (drafting, evidence assembly, measurement) that precedes a human decision.
2. When it surfaces a decision as blocking-and-human-facing, VET it: actually blocking
   (no autonomous path — not researchable, draftable, or measurable) AND actually
   human-facing (product/architecture authority; acceptance valves requiring journaled
   live evidence; grooming-cut approval; irreversible/outward-facing acts; secrets/host
   mutation). Reframe wrong questions; drive prep first; surface the RESULT with the
   question.
3. Present vetted decisions via AskUserQuestion, recommended option FIRST labeled
   "(Recommended)", one question per turn, plain language with every term defined, full
   repo names always, `---` as the final line before a picker. Relay decisions back and
   verify execution.

**Maintainer correction (2026-07-23, first escalation attempt):** the vetting bar is
HIGHER than the rubric reads. The supervisor escalated bd-ib-o35rcx (fully-prepped,
telemetry-backed, clear recommendation) and the maintainer bounced it: "non-blocking-
worthy question. Resolve it." If the supervisor can recommend confidently from assembled
evidence, the supervisor DECIDES and announces the disposition in prose; escalate only
when evidence genuinely underdetermines the choice or a hard category applies
(irreversible/outward-facing, secrets/host mutation, real product/values calls).
Grooming-cut vetting is also supervisor-side; escalate only genuinely-human calls
embedded in a cut.

## How to inspect and drive
- Inspect: `tmux capture-pane -t factory-success-rate-remediation -p -S -120`
- Drive multi-line: write instruction to a file → `tmux load-buffer -b sup <file>` →
  `tmux paste-buffer -p -b sup -t factory-success-rate-remediation` → VERIFY the paste
  chip/[Pasted text] is present (re-paste if not; check for DOUBLES — clear with a single
  C-c and re-paste once if duplicated) → `tmux send-keys -t factory-success-rate-remediation Enter`
  as a separate call.
- Wait via Monitor on artifact files / a status.log you tell the session to append events
  to — never poll-loop, never a second background shell.
- NEVER tmux kill-server or cleanup on the default socket (maintainer-owned); never touch
  worktrees/branches other sessions created; every instruction sent carries: no
  --no-verify, halt-and-report on hook failure, halt if analysis contradicts the brief.
- Container inspection: LABELS ONLY (`docker inspect --format '{{json .Config.Labels}}'`).
  NEVER print .Config.Env — it leaks live credentials (this mistake was made once tonight;
  rotation was required).

## Initial context — what this track exists to remediate

Tonight's first sustained multi-track factory use surfaced FOUR distinct dispatch-failure
classes, all environmental (never the work itself: live success rate was 2 delivered / 6
attempts). All are filed in the livespec-orchestrator-beads-fabro tenant:

- bd-ib-w2ah — staging: a work-item whose ledger tenant differs from its implementation
  repo fails at fabro-run staging; the execution-mirror convention (file a verbatim mirror
  item in the repo-owning tenant) is the working remedy.
- bd-ib-sd8o (P2, actionable root-cause; evidence in bd-ib-6yll) — concurrent host-network
  Fabro runs collide (bwrap namespace denial at codex-acp stages; mechanism
  differential-diagnosed, not yet proven). Deliverables: (a) diagnose the contended
  resource; (b) safe concurrency — per-run network isolation with routed access to the
  host Dolt ledger at 127.0.0.1:3307 (the reason --network host exists) and/or generalize
  the HOST_PUBLISH_PORT port-fallback precedent; (c) interim host-wide dispatch mutex at
  ADMISSION time. Also carries a doctrine split to resolve: agent-disciplines "never gate
  on other runs" vs drain-doc "--network host forbids parallelism".
- bd-ib-qq7f — push-race defect (filed by the rop-sweep-fleet-policy track).
- bd-ib-pums (P2) — a hook-refused engine pre-clone push falls back SILENTLY to a
  synthetic snapshot base that exists on no remote → disjoint-history publish →
  misleading rejection (first-workflow-file/workflows-scope). The silent fallback is the
  defect: staging from a nonexistent base must fail fast and loudly. Three fix directions
  in the item body. Blast radius: every fleet repo carries the commit-refuse hook.

Related precedents and open threads:

- The vantage gate fix (livespec-dev-tooling 1e85cd1, PR #574): credential-class detection
  (ghs_ prefix → out-of-vantage, exit 0, zero API reads) — the PATTERN for context-aware
  gates; its root cause (a shared `just check` aggregate reaching a context its author
  never enumerated) is the shape to design against.
- livespec-dev-tooling-yi6l (P1, rop-sweep-fleet-policy's parallel diagnosis; main fix
  landed as 1e85cd1) — its check-master-ci-green-contradicts-GitHub sub-finding may still
  be open; verify.
- Transient-infra publish failures (PyPI download timeout killing a check that never ran —
  PR #577 precedent: complete via CI re-run, not re-dispatch).
- The manual cross-track serialization protocol lives in
  /data/projects/livespec/tmp/fleet-pin-propagation-supervisor/status.log (one-at-a-time
  host-wide, ordered release lines). THIS TRACK'S FIXES SHOULD RETIRE THAT MANUAL
  PROTOCOL. Coordinate factory usage through it until then — this track will need factory
  slots to live-verify its own fixes.
- Cross-track pings are maintainer-routed: ask the maintainer before messaging another
  session the first time; per-instance routing has been the pattern.

## Standing method rules

- A status artifact is not a health signal; verify against the right source; a claim
  about live state has a shelf life of minutes — re-measure before citing, including this
  file.
- Read canonical state via git show origin/master:<path> after a fetch, not the working
  tree.
- No acceptance/close without journaled live-exercise evidence (or, for non-behavior
  deliverables, independent adversarial re-derivation). "Done" means rolled out and
  exercised live in the real environment.
- Factory-first for ready, factory-safe implementation (.ai/agent-disciplines.md
  §"Factory-dispatch over inline implementation") — but this track's own fixes to the
  factory may be exactly the host-only/self-machinery class that stays attended; route
  per the written guidance, and check the guidance before recommending, never argue from
  what worked recently.
- Repository mutation protocol: worktree → PR → merge → cleanup; Red-Green-Replay for
  product .py; independent Fable review before every spec ratification; blockers route,
  never self-waived.
- No make-work: when the queue is truly human-gated, blocked-on-human is the honest
  signal.
