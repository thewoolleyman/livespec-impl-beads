# Dossier 002 — cattle, not pets: migrate the factory workloads onto the homelab Kubernetes fleet

Strategic-direction note for plan thread `runaway-process-containment`,
compiled 2026-09-01 at the maintainer's direction. Where note 001 root-caused
four runaway-process incidents on the current factory hosts and enumerated ten
instance-level prevention mechanisms (P1–P10), this note records the **class**
answer the maintainer chose over those patches: run the factory workloads as
first-class Kubernetes cattle on the homelab fleet, and route that as a
`propose-change` against the **homelab** SPECIFICATION.

The maintainer selected this over two alternatives (interim local
containerization on hp/vps now; keep pets and harden with P1–P10). The chosen
option is the biggest structural win and the cleanest end state, and it carries
two costs recorded honestly below: the fleet does not exist yet, so containment
stays open until it lands, and it **reverses a deliberate homelab decision** to
keep the factory hosts as pets.

Labelling convention is note 001's: **measured** (re-measured this session with
the instrument named), **dossier** (carried from note 001), **inferred**,
**hypothesis**. Do not strengthen a label when quoting.

## Why "cattle, not pets" is the class answer

Each of the four incidents is an instance of *state accumulating on a
long-lived host that nobody rebuilds*. A process burns unbounded CPU for 67
minutes (H1); a sandbox saturates its quota through two timeouts and a
hook-running commit (H2); a terminal run's container is re-started by an
operator tool and never re-stopped, surviving 3.9 days (H3); an orphaned shim
spins under a fake HOME, PPID 1, for 8.5 days (V1). Every one of these is only
possible because the host is a **pet**: it is nursed, kept running, reached into
by hand, and never destroyed-and-rebuilt from declared state.

How production environments contain this class — not by detecting each runaway
after the fact, but by removing the conditions that let one persist:

1. **cgroup-enforced requests and limits per workload.** kubelet caps CPU
   (throttle) and memory (OOMKill) at the pod cgroup. A workload cannot burn
   360% for 67 minutes (H1) or hold a 4-core quota idle for days (H3); it is
   throttled or killed at its declared ceiling.
2. **Liveness / readiness probes → automatic restart.** A wedged daemon is
   restarted by its controller, not left spinning until a human notices.
3. **Job/Pod TTL, `ownerReferences`, and garbage collection.** A finished run
   is an owned object with `TTLAfterFinished`; the control plane reaps it. There
   is no "the container outlived its run record" because the control plane *is*
   the reconciler between declared and actual — the exact divergence that made
   H3 invisible to `fabro ps -a` cannot exist.
4. **Node cordon / drain / recycle and scheduled rolling restarts.** Nodes are
   rebuilt on a cadence and workloads are periodically restarted (a max-lifetime
   recycle). Nothing spins for 8.5 days (V1) when the node is rebuilt weekly and
   the pod is recycled daily.
5. **Immutable images and no interactive SSH into prod.** There is no ambient
   root shell on a node from which to launch an unbounded `grep /` (H1), and no
   `POST /ssh` that re-animates a terminal container (H3). Talos makes this
   structural: it *"exposes an API, not SSH or a general shell"*
   (homelab `SPECIFICATION/constraints.md:8-9`).

This is the homelab charter already, verbatim: *"Machines are cattle: any node
may be destroyed and rebuilt from declared state without recovering anything
from the machine itself"* (homelab `SPECIFICATION/spec.md:1-7`); *"Kubernetes,
not the host operating system, is the durable workload abstraction"* (`:24-35`).
The direction of this plan is to bring the factory workloads *under* that
charter instead of leaving them outside it.

## The current homelab reality — measured 2026-09-01

Read directly from `/data/projects/homelab` this session:

- **Target architecture** (`SPECIFICATION/spec.md:1-7`, `constraints.md:8-9`,
  `docs/talos-omni-architecture-and-rollout.md:874-889`): Talos Linux nodes,
  Hosted Omni for machine/cluster lifecycle, **Flux** for workload
  reconciliation, Cilium CNI, KubeSpan mesh, Tailscale as the identity-aware
  access plane. AWS-hosted control plane in `us-east-1`; fleet ceiling ten
  nodes.
- **The fleet is EMPTY.** `SPECIFICATION/spec.md:254-256`: *"The fleet is
  currently EMPTY. No machine has been provisioned under this specification."*
  `clusters/mi-homelab/` holds exactly one file — a
  `control-plane-taint-toleration` `ValidatingAdmissionPolicy` awaiting a
  cluster to bind to. No Deployments, StatefulSets, Jobs, or Flux
  Kustomizations exist outside `history/` and check fixtures; `provision/` is
  empty. The repo is in its pre-provisioning phase: its real deliverables to
  date are spec clauses and `checks/*.sh` validators.
- **The factory hosts are explicitly carved OUT of the migration.**
  `docs/talos-omni-reset.md:645-649` directs any device sweep to *"carve out
  `hp-xubuntu` and `vps`: they are the factory hosts every repo's dispatch
  resolves by MagicDNS name"*; `:687` treats them as preserved, independent,
  manually-managed build hosts. The **dolt/beads ledger** is a separate host
  *"outside this repo and outside every phase here"* (`:549-551`), S3-backed
  (`:766-767`). **overseerd** is factory tooling in the `livespec-overseer`
  repo, never a fleet workload. So the four incident servers are, by the
  *current* homelab decision, pets by design.
- **There is no process-resource-governance contract yet.** A whole-tree search
  of homelab `SPECIFICATION/` for `ResourceQuota | LimitRange | cgroup | ulimit
  | resource limits | liveness | readiness` returns no governance rule — only
  incidental hits (a memory-planning aside on Talos's eviction threshold, and
  "probe" used to mean a connectivity test). The cattle model there is about
  **nodes**, not per-workload resource lifecycle.

The consequence for this plan: the chosen direction is **two spec-tier changes
in the homelab tenant** — (a) reverse the factory-host carve-out enough to run
the factory workloads on the fleet, and (b) add the process-resource-governance
contract (requests/limits, probes, Job TTL, recycle cadence) that would make any
fleet workload — not just ours — cattle at the process level.

## Incident → cattle-workload mapping

| id | what a cattle workload does structurally | residual |
|---|---|---|
| H1 | A limited workload is CPU-throttled at its request/limit; no interactive root shell exists on a Talos node to launch `grep /` | agent-shell command hygiene (P10) still matters *inside* a workload |
| H2 | Pod delete SIGKILLs the whole pod cgroup, so a timed-out turn's process tree dies with the pod; scheduler spreads load | **limits alone are not enough** — see the nuance below; the checkpoint-hook cost is workload-internal (P4) |
| H3 | A run is an owned Job with `TTLAfterFinished`; GC reaps it; no `POST /ssh` re-animates a terminal pod; declared==actual by reconciliation | none at the container-lifecycle layer — this is the cleanest structural win |
| V1 | Pod PID 1 reaps orphans; the pod is CPU-limited; node/pod recycling clears any survivor within the cadence | the fire-and-forget helper (P7) is still worth fixing so it never spawns unbounded even inside a pod |

**The honest H2 nuance (measured, note 001):** H2's sandbox was *already*
cgroup-capped at `cpu: 4` — its 397% was a 4-core cap **saturated**, not an
unbounded container. So resource limits alone would not have prevented H2. What
cattle adds for H2 is the *lifecycle-kill* half — deleting the pod tears down
the whole cgroup, and a fresh retry starts from a clean process table — plus
scheduler-level load awareness. Limits ≠ lifecycle-kill; the migration
proposal must carry both, and the checkpoint-that-runs-hooks cost (note 001 P4;
ledger `bd-ib-6ka`) is internal to the workload and is not fixed by moving it
onto k8s.

## Target workload shapes (the substance the homelab proposal will draw on)

- **fabro run sandbox → a per-run Job/Pod** with cpu/mem requests+limits,
  `activeDeadlineSeconds` (the stage/run ceiling), `TTLAfterFinished` +
  `ownerReferences` for GC, and a restart policy that does not resurrect a
  terminal run. Closes H3 outright; bounds H1/H2 blast radius; the run process
  tree dies with the pod.
- **fabro-server (dispatch daemon) → a Deployment** with liveness/readiness,
  resource limits, and a scheduled rollout-restart cadence (max-lifetime
  recycle).
- **overseerd → a Deployment** (liveness, restart, limits). **Open question:**
  its worker model is tmux sessions on a host (note 001; homelab
  `plan/steady-state-loop-hardening/research/002-problem-and-fix-matrix.md`),
  which does not translate to pods unmodified — workers likely become Jobs. This
  is a `livespec-overseer`-tenant redesign, pointer only here.
- **dolt/beads ledger → a StatefulSet** with a PVC and the existing S3 backup,
  preserving the single-writer authority. This is the highest-risk migration
  (stateful, multi-tenant, the ledger every family repo depends on) and is a
  candidate to stay a managed pet longest.

## The crux the homelab proposal MUST resolve — circular dependency

The factory-host carve-out is not an oversight; it is the same
circular-dependency rule homelab already applies to its site gateways: *"The
gateway is deliberately not a Kubernetes node … Putting them inside the cluster
creates a circular dependency"* (homelab `SPECIFICATION/spec.md`). The Fabro
factory is what **builds, provisions, and repairs** the fleet. A factory that
dispatches the very cluster it runs on cannot depend on that cluster being
healthy, or a cluster outage becomes unrecoverable — the tool that would fix it
is down with it.

So the proposal cannot be "move everything onto the fleet." It must choose a
seam that preserves a bootstrap path:

- **(a) Bootstrap nodepool.** Run the factory on a separate, minimally-dependent
  nodepool/cluster (or the AWS infra workers) that does not depend on the
  remote/GPU workloads it dispatches — analogous to how platform components run
  on dedicated AWS infra workers so Flux/secrets survive the loss of remote
  capacity (homelab `spec.md:54-65`).
- **(b) Partial migration.** Run the *run sandboxes* as Jobs on the fleet (where
  the H3/H1/V1 wins are) while the *dispatch server* and *ledger* stay
  bootstrap pets under proper cgroup/systemd governance until a safe on-fleet
  home exists.

Naming this crux is the point of routing it as a spec proposal rather than an
implementation task: the accept/reject decision on the seam is a homelab
architectural call, not this repo's to make.

## Routing and re-tiering

- **Cross-repo, spec-tier (homelab), the primary route:** a `propose-change`
  against homelab `SPECIFICATION/` carrying (1) the factory-workload migration
  with the circular-dependency seam resolved, and (2) the process-resource-
  governance contract (requests/limits, probes, Job TTL, recycle cadence). This
  plan files a **pointer**; the homelab tenant owns the proposal and its
  revise/accept lifecycle. Per this thread's scope event, cross-repo pieces are
  pointers to the owning tenant.
- **This repo (`livespec-orchestrator-beads-fabro`), deferred:** the Dispatcher
  change to submit runs as k8s Jobs instead of `fabro run --server`. Large,
  dispatch-safe in principle, but blocked until the homelab contract exists and
  is a fabro-fork question (the sandbox model uses docker + ssh today).
- **`livespec-overseer`, deferred pointer:** the overseerd worker-as-Job
  redesign.
- **Re-tiering note 001's P1–P10** under this frame — the interim P-mechanisms
  are now explicitly the **bridge** the maintainer chose to build *toward*, not
  a parallel permanent track:
  - **Subsumed by the migration** (build only as interim if the class bites
    before the fleet lands): P1 sandbox-leak detector (→ Job GC), P3
    process-tree kill (→ pod-cgroup kill), P6 cgroup scopes (→ pod limits), P9
    host-level runaway detector (→ the control plane reconciles it).
  - **Still needed, migration or not** (workload-internal or scheduling): P4
    checkpoint-hook budget, P5 load-aware admission, P7 fire-and-forget
    self-limit, P8 test-fixture hygiene, P10 agent-shell command hygiene.

## Sequencing and the open caveat

The maintainer chose the fleet migration over interim local containerization.
That means **containment of this class stays open** until (1) the homelab fleet
is provisioned and (2) the migration lands — a long arc, gated behind homelab's
own pre-provisioning phase and its steady-state-loop-hardening pause on fleet
implementation. The four incidents already happened; new ones in the same class
can happen on the pet hosts in the interim. This note records that the interim
P-mechanisms are the **bridge**, and the plan should build only the cheapest
subset (the "still needed" tier above, plus any leak that actively bites) rather
than a full parallel patch program — the structural fix is the migration.

## Read-first chain for a successor

1. This note (002) for the direction and the crux.
2. Note 001 for the four incidents, their measured mechanisms, and P1–P10.
3. This epic's scope events and handoff timeline (`bd comments bd-ib-wcuauj
   --json`, read `text`).
4. The homelab spec files cited above, in `/data/projects/homelab`.
