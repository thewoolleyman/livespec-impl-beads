# 001 — The default janitor argv is dev-tooling-premised: incident and declared-resolution direction

Filed 2026-08-29 by homelab's steady-state-loop-hardening coordination
seat at the homelab maintainer's direction. Provenance: homelab
dogfooding — the SECOND adopter-premise instance, surfaced minutes after
homelab's first clean hardened dispatch. Sibling filing today:
plan/dispatcher-staleness-gate-comparand (independent finding, same
program).

## 1. The incident (homelab, 2026-08-29, UTC)

homelab dispatched homelab/hl-cid234 on the 0.96.1 build: preflights
passed (staleness, origin-reachability, declared master-CI), the factory
produced a REAL merge — PR homelab#1045, merged 12:11:05Z, deliverables
verified on main. First clean dispatch of homelab's hardened loop. The
run then FAILED at janitor-post-merge: homelab's justfile has no
`install-worktree-pack` recipe. Consequences: the merged item is
stranded `active` (janitor red, acceptance never ran; recoverable via
reconcile-merged once a recipe exists), and every further homelab
dispatch fails identically. Prior instance of the same class:
2026-08-27, the janitor degraded on homelab's then-missing
`install-commit-refuse-hooks` (fixed by v087 + homelab#1062).

## 2. The shipped behavior (v0.96.1, build ba30bc662f07)

`_dispatcher_fabro_argv.py` hardcodes:

```
_DEFAULT_JANITOR = ("mise", "exec", "--", "just",
                    "check-no-workflow-edits", "install-worktree-pack",
                    "check")
```

Its own comment explains the premise: since livespec-dev-tooling
v0.54.24 an absent worktree-discipline pack FAILS `just check`, so the
janitor provisions the pack into its fresh checkout (introduced after
the bd-ib-hvuhxp reconcile stranding, PR #1018 era). The only override
surface is the per-invocation `--janitor` CLI flag
(`dispatcher.py:401,445` feeding `janitor_argv_with_default`). There is
NO committed repo declaration for the post-merge janitor argv.

## 3. The ruled context

- contracts.md:1679: fleet members and adopters consume the orchestrator
  IDENTICALLY.
- homelab's maintainer ruling 2026-08-29 (recorded as a scope event on
  homelab's plan steady-state-loop-hardening): homelab is an ADOPTER; it
  does not import livespec-dev-tooling; "any gate or step premised on
  the governed repo running livespec-dev-tooling is defective, and the
  fix routes UPSTREAM"; and the commissioned upstream leg explicitly
  included AUDITING THE WHOLE STEP/PREFLIGHT SET for fleet-member
  assumptions.
- v087 "Janitor-bootstrap recipe resolution" executed that ruling for
  the BOOTSTRAP step: the step resolves the governed repo's DECLARED
  `dispatcher.janitor_bootstrap.recipe`, fleet default only when
  undeclared. The post-merge janitor argv is the unfinished remainder of
  the same audit: dev-tooling recipe names (`install-worktree-pack`,
  dev-tooling `check` semantics, the `mise exec` wrapper) remain a
  hardwired default imposed on adopters.

## 4. Proposed direction (for this repo's propose-change lifecycle)

1. Mirror the v087 / dispatcher.master_ci pattern: a committed
   declaration (e.g. `dispatcher.janitor.argv` or a recipe-set form)
   resolving the post-merge janitor per governed repo; the current
   dev-tooling default applies ONLY when undeclared, so no conforming
   fleet member changes behavior.
2. Fail-closed semantics unchanged: a declared argv that fails still
   reds the janitor and blocks disposition.
3. Subordinate or retire the `--janitor` CLI flag: an uncommitted
   per-invocation override of committed policy is the posture class the
   v075 temporary-settings clause exists to prevent.
4. Finish the audit: sweep the remaining step/preflight surface for
   other dev-tooling premises (recipe names, `mise` wrapper, pack
   semantics) so this is the LAST instance of the class, not the second
   of N.

Verification shape: positive — a repo with a declared janitor argv runs
it verbatim; discriminating — an adopter repo with NO dev-tooling and a
declared plain-shell argv completes janitor green with no dev-tooling
recipe present; control — an undeclared repo still gets the fleet
default unchanged.

## 5. Cross-repo state, recorded so re-derivation is unnecessary

homelab's interim unblock (in flight 2026-08-29) provides a
fleet-default-NAMED `install-worktree-pack` recipe with homelab-REAL
plain-shell content (provisioning homelab's own worktree discipline —
its commit-refuse hook — into fresh checkouts), per its no-fake-recipes
ruling. That is interface-name compliance, not dev-tooling adoption; the
declared resolution here retires even the name coupling. Downstream this
gates: homelab/hl-cid234's disposition, homelab/hl-s2kiob's re-dispatch,
and thereby homelab/hl-tk2zcd (clean-dispatch evidence).

## 6. Caveats

Measured 2026-08-29 against build ba30bc662f07 (v0.96.1), homelab's
dispatch journal, and homelab's justfile. Re-verify the argv and
override surfaces at current HEAD before drafting the propose-change.
