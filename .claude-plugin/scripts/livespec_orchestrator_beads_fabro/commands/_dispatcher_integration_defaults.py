"""EVERY fleet default the integration-contract resolver can return, in ONE place.

`SPECIFICATION/contracts.md`, the repository-integration-contract section,
requires that
every integration point the orchestrator imposes on a governed repository be a
field of one versioned schema read through one generic resolver. A `FleetDefault`
is the value that resolver hands back for an absent OPTIONAL key, and this module
is where every one of those values is spelled -- so the answer to "what does this
repository get when it declares nothing?" is read off a single file rather than
reconstructed from four resolvers that each kept their own copy.

WHY A DEFAULTS MODULE RATHER THAN A DEFAULT BESIDE EACH FIELD. The defaults ARE
the fleet's own toolchain, and they are exactly the literals that used to be
hard-coded at their point of use -- `CI`/`ci-green` inside the preflight, the
`mise exec -- just ...` argv inside the janitor argv builder, `--rebase` inside
the auto-merge argv and again inside the publish prompt. Each of those was a
silent assumption imposed on every adopter, and each drifted from its twin
because nothing bound them. Gathering them here makes an adopter-visible default
a reviewable diff in one file, and it is the module a literal-ban gate can point
at: a fleet literal ANYWHERE ELSE in the dispatcher package is then a defect by
construction rather than by judgement.

THE NO-OP IS A VALUE, NOT AN ABSENCE. `TOOLCHAIN_NO_OP` is the explicit no-op
this specification's factory-sandbox-toolchain-disposition clause ratifies for
a prepare-toolchain premise an adopter does not carry. It is spelled as a value a
field RESOLVES TO precisely so the no-op is declared and validated like every
other point instead of being inferred from silence -- an inference is what makes
a silent adopter degradation indistinguishable from a configuration nobody wrote.
"""

from __future__ import annotations

__all__: list[str] = [
    "FLEET_CORE_REPO_URL",
    "JANITOR_BOOTSTRAP_RECIPE_DEFAULT",
    "JANITOR_CHECK_SUITE_DEFAULT",
    "MASTER_CI_JOB_DEFAULT",
    "MASTER_CI_WORKFLOW_DEFAULT",
    "MERGE_MODES",
    "MERGE_MODE_DEFAULT",
    "SANDBOX_CHECK_SUITE_DEFAULT",
    "SANDBOX_EXEMPT_MARKERS",
    "SANDBOX_EXEMPT_MARKER_DEFAULT",
    "TOOLCHAIN_NO_OP",
    "UNRESOLVED_ARGV",
    "UNRESOLVED_NAME",
]

# What a field that resolved NOTHING renders as. A sentinel rather than the
# convention's own value, because the convention is the wrong answer on a
# defective declaration: prose reading `CI` would tell an operator the lookup
# targeted a pipeline they never declared.
UNRESOLVED_NAME = "<unresolved>"

# The argv-shaped counterpart of the sentinel above. An empty argv cannot be
# run, which is the point: a caller that ignores the defect fails on a command
# that resolves nothing rather than on a plausible-looking fleet command.
UNRESOLVED_ARGV: tuple[str, ...] = ()

# This fleet's aggregate workflow and its aggregate job -- the convention an
# adopter overrides through `dispatcher.master_ci`.
MASTER_CI_WORKFLOW_DEFAULT = "CI"
MASTER_CI_JOB_DEFAULT = "ci-green"

# The HOST-JANITOR venue's check-suite. `install-worktree-pack` PRECEDES `check`
# because the janitor checkout is a fresh worktree that never ran
# `just bootstrap`, and the worktree-discipline pack is gitignored -- so it is
# absent there by construction, and since livespec-dev-tooling v0.54.24 an absent
# pack is a FAIL by default, which reds the janitor's own `just check` on a fully
# conformant repository. The janitor is a normal worktree-equivalent, NOT a
# declared sandbox, so this PROVISIONS the pack rather than exempting the venue:
# the asserted property becomes TRUE instead of skipped.
JANITOR_CHECK_SUITE_DEFAULT: tuple[str, ...] = (
    "mise",
    "exec",
    "--",
    "just",
    "check-no-workflow-edits",
    "install-worktree-pack",
    "check",
)

# The IN-SANDBOX-GATE venue's check-suite. It is the same declared check-suite
# with the host-venue provisioning dropped: a Fabro sandbox is a fresh full
# clone whose own prepare chain has already run, so the worktree-pack
# provisioning the host janitor needs is not a premise there. The two venues
# differing ONLY in their fleet default is what the ratified venue dimension
# buys -- before it, this argv lived as a bare literal in the publish prompts
# with nothing binding it to the host one.
SANDBOX_CHECK_SUITE_DEFAULT: tuple[str, ...] = ("mise", "exec", "--", "just", "check")

# How this fleet INVOKES its hook-install recipe. `just` reaches these hosts
# through mise, so the default's argv keeps the `mise exec --` prefix the shipped
# bootstrap always used. A DECLARED recipe is invoked exactly as the adopter
# wrote it: imposing our wrapper on someone else's command is the same
# assumed-tooling defect one layer down.
JANITOR_BOOTSTRAP_RECIPE_DEFAULT: tuple[str, ...] = (
    "mise",
    "exec",
    "--",
    "just",
    "install-commit-refuse-hooks",
)

# The fleet livespec core, which is what an UNDECLARED `compat.core_repo` means.
# There is deliberately NO companion default for `compat.pinned`: the only
# substitutable ref would be the moving branch tip its own clause forbids, so
# that field is REQUIRED and an absent declaration resolves to `Defective`.
FLEET_CORE_REPO_URL = "https://github.com/thewoolleyman/livespec.git"

# The explicit no-op VALUE a prepare-toolchain premise resolves to for a
# repository that carries no such premise. Never an absent key -- see the module
# docstring for why the distinction is the whole point of the field existing.
TOOLCHAIN_NO_OP: tuple[str, ...] = ()

# The closed value space of `dispatcher.merge_mode`, and the member default. A
# true merge commit is NOT admitted: acceptance's fallback merged-diff read and
# the `reject:regroom` revert both read the merge commit directly and break on a
# merge commit's combined diff, so admitting it is a separate obligation that
# must ratify those two code-path changes.
MERGE_MODES: tuple[str, ...] = ("rebase", "squash")
MERGE_MODE_DEFAULT = "rebase"

# The closed value space of `dispatcher.sandbox_exempt_marker`, which holds
# exactly ONE value. The canonical commit-refuse hook body reads that git-config
# key literally, so a declared alternate would be set by the projection and
# ignored by every fleet hook -- a stranded dispatch, contract-sanctioned and
# uncatchable. Key variance is a separate ratification requiring a
# key-parameterized hook body.
SANDBOX_EXEMPT_MARKER_DEFAULT = "livespec.sandboxExempt"
SANDBOX_EXEMPT_MARKERS: tuple[str, ...] = (SANDBOX_EXEMPT_MARKER_DEFAULT,)
