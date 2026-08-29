# 001 — Staleness gate incident and the ratified divergence

Filed 2026-08-29 by homelab's steady-state-loop-hardening coordination
seat at the homelab maintainer's direction. Provenance: homelab
dogfooding — this fired on the first dispatch attempt of the hardened
loop and is currently gating homelab's clean-dispatch evidence.

## 1. The incident (homelab, 2026-08-29, all times UTC)

- ~09:40Z — an attended worker session starts in homelab; Claude Code
  resolves the plugin `release` channel to build `329ba0e1d130`
  (v0.96.0), the latest release at that moment.
- 10:52Z — v0.96.1 (`ba30bc662f07`) is published and appears in the
  local plugin cache.
- 10:59:16Z — the session executes a human valve action
  (`human-valve-reject-rework`, item homelab/hl-s2kiob), journaled with
  attributed invoker `plan:fleet-substrate-boot-identity-and-network`.
- 11:03:02–04Z — dispatch preflights PASS: source-checkout origin
  reachability; master-CI via the DECLARED `dispatcher.master_ci`
  pipeline (`ci-green`, branch main). First live confirmation of the
  declared-CI and attribution work in an adopter repo.
- 11:03:05Z — the staleness gate refuses, blocking. Verbatim journal
  record (homelab `tmp/fabro-dispatch-journal.jsonl`):

```
{"at": "2026-08-29T11:03:05Z", "stage": "dispatcher-staleness-refused",
 "invoker": "plan:fleet-substrate-boot-identity-and-network",
 "invoker_source": "flag", "blocking": true,
 "detail": "ERROR: dispatcher plugin build is stale; executing build
 329ba0e1d130 predates latest release ba30bc662f07. Run `claude plugin
 update livespec-orchestrator-beads-fabro@livespec-orchestrator-beads-fabro`
 before dispatching."}
```

The session was 83 minutes old and had been current at start. No factory
run occurred. The remedy costs a full session restart (plugin bindings
resolve only at session start), and it recurs on every release published
mid-session.

## 2. The shipped behavior

`_dispatcher_staleness_gate.py` (executing in v0.96.0; unchanged in
v0.96.1, build `ba30bc662f07`):

- Identity: a git-checkout plugin root is exempt; a cache root whose
  name is not a sha prefix warns and proceeds (the
  livespec-orchestrator-beads-fabro/bd-ib-n7ce4n deadlock fix).
- Comparand: `git ls-remote` of THIS repo's live `refs/heads/release`
  head — probed over the network AT DISPATCH TIME — plus
  `refs/heads/master` (matching master is allowed; being behind both
  refuses; master-ahead-of-release yields a non-blocking warning).
- Refusal: blocking, exit 3, journaled `dispatcher-staleness-refused`.

History: the blocking gate entered through the fix lane — `33bf8d5d`
"fix: gate stale dispatcher plugin builds" (2026-07-24), no spec
citation in the commit; then two corrective fixes: `ad715ea3` "allow
unreleased dispatcher plugin builds" and `96ce547e` "staleness gate
warns and proceeds when release context is unobservable (bd-ib-n7ce4n
deadlock case)".

## 3. The ratified text

`SPECIFICATION/contracts.md`, "Self-update triggers on a version
comparison, and every promotion is canaried" (lines ~1709–1760 at HEAD
`de488069`):

- Self-update compares the RUNNING RELEASE against the latest available
  RELEASE — to decide about UPDATING, with every promotion canaried.
- A passing canary "MUST surface that a RESTART IS DUE"; a failing one
  keeps last-known-good AND alarms.
- Verbatim: "Neither outcome moves the running process onto the
  candidate. Detecting, canarying, and alarming is the whole of the
  Dispatcher's self-update responsibility."
- Operator consequence, verbatim in intent: "a host-side dispatch runs
  the last RELEASE the operator has provisioned" — and this "applies to
  fleet members and adopters identically."

No ratified clause carries a blocking refuse-dispatch-on-stale form:
"predates latest release" appears nowhere in SPECIFICATION, and
scenarios.md's only restart-due scenario is the canary one
(scenarios.md:1265). The ratified word "staleness" belongs to the
detection-coverage facts (gap/drift), a surfaced-not-blocking pattern.

## 4. The divergence and why it is brittle

The shipped gate is STRICTER than the ratified contract: the contract
says the provisioned release is legitimate to run and staleness is
handled by detect → canary → surface restart-due → alarm; the gate
instead hard-refuses dispatch unless the executing build equals the
instantaneous latest release head. Mechanism of breakage: plugin builds
bind at SESSION START; the gate probes the moving `release` head at
DISPATCH TIME. Any release published between those two instants bricks
dispatch in every live session until each is restarted. On a day with
several releases, attended dispatch windows shrink toward zero, and the
cost is a full session restart per release. The gate has already needed
two corrective fixes for adjacent over-blocking (§2) — evidence the
comparand, not the implementation, is the problem.

## 5. Proposed direction (for this repo's propose-change lifecycle)

1. Comparand: the gate compares the executing build against the
   OPERATOR-PROVISIONED payload (for an exact pin: the pin; for a
   channel pin: the payload that channel resolved to for this session).
   Executing == provisioned ⇒ proceed. Refusal remains for true
   divergence — executing a payload that is NOT the provisioned one —
   which is a real integrity violation and stays fail-closed.
2. Freshness pressure moves to the already-ratified surfacing lane:
   detect newer release → canary → surface RESTART IS DUE, plus a
   needs-attention staleness fact ("provisioned build is N releases /
   M days behind latest release"), modeled on the detection-staleness
   composers. Pressure without mid-session breakage.
3. Optional deliberate floor: a committed `dispatcher.minimum_release`
   config key an operator sets when a specific release is
   safety-critical — a hard refusal below the floor, chosen by a human,
   not ambient.
4. Whichever shape is ratified, the revise should settle explicitly
   whether ANY blocking form is wanted; if yes, ratify it with its
   comparand named; if no, the gate returns to the ratified
   detect/canary/alarm shape. Either outcome removes the
   impl-stricter-than-spec condition.

Verification shape: positive control — executing != provisioned
refuses; discriminating control — a release published mid-session does
NOT refuse a dispatch from a session running its provisioned payload,
and the staleness fact/restart-due surfacing appears instead.

## 6. What this gates downstream

homelab (adopter) has two items sitting `ready` behind this refusal
(homelab/hl-s2kiob, homelab/hl-cid234); their re-dispatch is homelab's
clean-dispatch evidence on the hardened loop (homelab/hl-tk2zcd), which
gates homelab's steady-state cutover program. Interim workaround there:
plugin update + session restart per release.

## 7. Caveats

Facts measured 2026-08-29 ~11:30Z against homelab's journal, the plugin
cache builds v0.96.0/v0.96.1, and this repo at HEAD `de488069`.
Re-verify the gate at current HEAD before drafting the propose-change.
