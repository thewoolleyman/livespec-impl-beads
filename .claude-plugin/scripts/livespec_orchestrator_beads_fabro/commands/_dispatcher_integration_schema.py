"""The ONE versioned schema of what the orchestrator requires of a governed repo.

`SPECIFICATION/contracts.md`, the repository-integration-contract section,
ratifies that the set of integration points the orchestrator imposes on a governed repository is an
API, and that it is TYPED: every point is a field of one versioned
`RepoIntegrationContract`, and a point that is not a field is not a requirement
the orchestrator may impose. This module is that schema.

THE FIELD SET IS CLOSED. `INTEGRATION_FIELDS` enumerates every ratified
obligation and nothing else -- a NEW dispatch-time or post-merge obligation
requires ratification with its own members-and-adopters disposition before a
field for it may exist here. That is why the enumeration is a literal tuple in
one place rather than a registry assembled from decorators: a reader can see the
whole closed set at once, and adding to it is a diff a reviewer cannot miss.

COMMANDS ARE ARGV, NEVER SHELL STRINGS. Every command-shaped field resolves to a
`tuple[str, ...]` of argv tokens. An adopter still DECLARES its command the way
it always could -- as a shell string that the resolver splits, or as a JSON array
-- because no committed key or its ratified semantics migrate here; what changes
is that nothing downstream ever handles the command as one opaque string again.

VENUE IS A SCHEMA DIMENSION, NOT TWO LITERALS. The check-suite legitimately
differs between the host janitor and the in-sandbox gate, so BOTH venues are
fields, reading the SAME committed declaration and differing only in their fleet
default. Before this, the host argv lived in the janitor resolver and the sandbox
one lived as bare prose in a publish prompt, with nothing binding them -- which
is exactly the "two divergent literals" the clause forbids.

THE DEFAULT BRANCH IS A FIELD WHOSE DECLARATION IS THE REPOSITORY ITSELF. Its
value comes from the ratified default-branch resolution (`origin/HEAD`, then the
forge) rather than from `.livespec.jsonc`, so its lookup path is deliberately not
under a committed block. It is REQUIRED for the same reason `compat.pinned` is:
the only substitutable value would be the `master` literal the clause retires.
"""

from __future__ import annotations

from dataclasses import dataclass

from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_defaults import (
    FLEET_CORE_REPO_URL,
    JANITOR_BOOTSTRAP_RECIPE_DEFAULT,
    JANITOR_CHECK_SUITE_DEFAULT,
    MASTER_CI_JOB_DEFAULT,
    MASTER_CI_WORKFLOW_DEFAULT,
    MERGE_MODE_DEFAULT,
    MERGE_MODES,
    SANDBOX_CHECK_SUITE_DEFAULT,
    SANDBOX_EXEMPT_MARKER_DEFAULT,
    SANDBOX_EXEMPT_MARKERS,
    TOOLCHAIN_NO_OP,
)

__all__: list[str] = [
    "COMPAT_CORE_REPO_KEY",
    "COMPAT_PINNED_KEY",
    "CORE_PINNED_REF_FIELD",
    "CORE_REPO_URL_FIELD",
    "DEFAULT_BRANCH_FIELD",
    "DEFAULT_BRANCH_KEY",
    "INTEGRATION_CONTRACT_SCHEMA_VERSION",
    "INTEGRATION_FIELDS",
    "JANITOR_BOOTSTRAP_KEY",
    "JANITOR_BOOTSTRAP_RECIPE_FIELD",
    "JANITOR_BOOTSTRAP_RECIPE_KEY",
    "JANITOR_CHECK_SUITE_FIELD",
    "JANITOR_CHECK_SUITE_KEY",
    "MASTER_CI_JOB_FIELD",
    "MASTER_CI_JOB_KEY",
    "MASTER_CI_KEY",
    "MASTER_CI_WORKFLOW_FIELD",
    "MASTER_CI_WORKFLOW_KEY",
    "MERGE_MODE_FIELD",
    "MERGE_MODE_KEY",
    "PREPARE_TOOLCHAIN_LEFTHOOK_FIELD",
    "PREPARE_TOOLCHAIN_LEFTHOOK_KEY",
    "PREPARE_TOOLCHAIN_MISE_FIELD",
    "PREPARE_TOOLCHAIN_MISE_KEY",
    "SANDBOX_CHECK_SUITE_FIELD",
    "SANDBOX_EXEMPT_MARKER_FIELD",
    "SANDBOX_EXEMPT_MARKER_KEY",
    "SHAPE_ARGV",
    "SHAPE_ENUM",
    "SHAPE_NAME",
    "VENUE_HOST_JANITOR",
    "VENUE_IN_SANDBOX_GATE",
    "IntegrationField",
    "RepoIntegrationContract",
]

# The version the executing plugin build requires of a repository's declaration.
# It is a CONSTANT of the schema rather than a per-field annotation because the
# contract version IS the schema version: a build names one number, and the
# validation pass grades a declaration against that number as a whole.
INTEGRATION_CONTRACT_SCHEMA_VERSION = 1

# The two venues a check-suite legitimately differs between.
VENUE_HOST_JANITOR = "host-janitor"
VENUE_IN_SANDBOX_GATE = "in-sandbox-gate"

# The three value shapes a field admits. `name` is a non-empty string, `argv` is
# a command the resolver hands back as argv tokens, and `enum` is a closed set of
# admitted strings.
SHAPE_NAME = "name"
SHAPE_ARGV = "argv"
SHAPE_ENUM = "enum"

# The committed keys, spelled EXACTLY as every operator-facing refusal names
# them, so a reader of a refusal knows where in `.livespec.jsonc` to write the
# answer. The `compat` pair is fully qualified because it hangs off the PLUGIN
# block rather than the `dispatcher` block, and a bare `compat.pinned` would send
# an adopter to the wrong nesting level.
_PLUGIN_BLOCK = "livespec-orchestrator-beads-fabro"

MASTER_CI_KEY = "dispatcher.master_ci"
MASTER_CI_WORKFLOW_KEY = f"{MASTER_CI_KEY}.workflow"
MASTER_CI_JOB_KEY = f"{MASTER_CI_KEY}.job"
JANITOR_CHECK_SUITE_KEY = "dispatcher.janitor.check_suite"
JANITOR_BOOTSTRAP_KEY = "dispatcher.janitor_bootstrap"
JANITOR_BOOTSTRAP_RECIPE_KEY = f"{JANITOR_BOOTSTRAP_KEY}.recipe"
COMPAT_PINNED_KEY = f"{_PLUGIN_BLOCK}.compat.pinned"
COMPAT_CORE_REPO_KEY = f"{_PLUGIN_BLOCK}.compat.core_repo"
MERGE_MODE_KEY = "dispatcher.merge_mode"
SANDBOX_EXEMPT_MARKER_KEY = "dispatcher.sandbox_exempt_marker"
PREPARE_TOOLCHAIN_MISE_KEY = "dispatcher.prepare_toolchain.mise"
PREPARE_TOOLCHAIN_LEFTHOOK_KEY = "dispatcher.prepare_toolchain.lefthook"

# The default branch is resolved from the repository's own git/forge state, so
# its lookup path sits OUTSIDE every committed block on purpose: nothing an
# adopter writes in `.livespec.jsonc` may answer it.
DEFAULT_BRANCH_KEY = "default_branch"


@dataclass(frozen=True, kw_only=True)
class IntegrationField:
    """One integration point: where it is declared, and what resolving it means.

    `key` is the operator-facing name every refusal quotes; `path` is the dotted
    lookup into the declaration. They differ wherever the two nestings differ --
    the `compat` pair names the plugin block a reader must write under while
    being looked up relative to it.

    `required` marks a field whose ratified semantics admit NO safe default, so
    an absent key resolves to `Defective` naming the absence rather than to a
    substituted value.

    `parent_key` is the ONLY-AN-ABSENT-KEY-FALLS-BACK rule made generic. Where it
    is set, DECLARING the parent block makes this field required: a present
    `dispatcher.master_ci` that names no `workflow` is a defect, because
    defaulting the missing half would prove part of a pipeline the repository
    never named. Where it is None -- `dispatcher.janitor.check_suite` -- a
    present parent that omits the child is a genuine absence and falls back.

    `declared_in_config` says whether this point is one a repository ANSWERS in
    its committed declaration. It is True for every field an adopter writes and
    False for the default branch alone, whose declaration is the repository
    itself. The pre-dispatch schema-validation pass grades a DECLARATION, so it
    grades exactly the fields carrying True: refusing there on an unprobed
    branch would send an operator to fix a committed key that does not exist,
    and the branch's own two-route resolution already refuses at the seam that
    probes it.
    """

    attribute: str
    key: str
    path: str
    shape: str
    required: bool = False
    fleet_default: str | tuple[str, ...] | None = None
    admitted: tuple[str, ...] = ()
    venue: str | None = None
    parent_key: str | None = None
    declared_in_config: bool = True


@dataclass(frozen=True, kw_only=True)
class RepoIntegrationContract:
    """The resolved integration points of ONE governed repository.

    Every field carries the value the generic resolver produced -- declared, or
    the fleet default -- with an unresolvable field carrying its shape's
    sentinel (`UNRESOLVED_NAME`, or the empty argv) rather than a plausible
    fallback. A caller that ignores the accompanying defects therefore fails on
    something that cannot run, never on a fleet value the repository has already
    said is not its own.

    Command-shaped fields are argv tuples, never shell strings: the split
    happens ONCE, here, so no seam downstream re-tokenizes a command and no seam
    can disagree with another about where its arguments end.
    """

    schema_version: int
    master_ci_workflow: str
    master_ci_job: str
    janitor_check_suite: tuple[str, ...]
    sandbox_check_suite: tuple[str, ...]
    janitor_bootstrap_recipe: tuple[str, ...]
    core_repo_url: str
    core_pinned_ref: str
    prepare_toolchain_mise: tuple[str, ...]
    prepare_toolchain_lefthook: tuple[str, ...]
    default_branch: str
    merge_mode: str
    sandbox_exempt_marker: str


MASTER_CI_WORKFLOW_FIELD = IntegrationField(
    attribute="master_ci_workflow",
    key=MASTER_CI_WORKFLOW_KEY,
    path=MASTER_CI_WORKFLOW_KEY,
    shape=SHAPE_NAME,
    fleet_default=MASTER_CI_WORKFLOW_DEFAULT,
    parent_key=MASTER_CI_KEY,
)

MASTER_CI_JOB_FIELD = IntegrationField(
    attribute="master_ci_job",
    key=MASTER_CI_JOB_KEY,
    path=MASTER_CI_JOB_KEY,
    shape=SHAPE_NAME,
    fleet_default=MASTER_CI_JOB_DEFAULT,
    parent_key=MASTER_CI_KEY,
)

JANITOR_CHECK_SUITE_FIELD = IntegrationField(
    attribute="janitor_check_suite",
    key=JANITOR_CHECK_SUITE_KEY,
    path=JANITOR_CHECK_SUITE_KEY,
    shape=SHAPE_ARGV,
    fleet_default=JANITOR_CHECK_SUITE_DEFAULT,
    venue=VENUE_HOST_JANITOR,
)

SANDBOX_CHECK_SUITE_FIELD = IntegrationField(
    attribute="sandbox_check_suite",
    key=JANITOR_CHECK_SUITE_KEY,
    path=JANITOR_CHECK_SUITE_KEY,
    shape=SHAPE_ARGV,
    fleet_default=SANDBOX_CHECK_SUITE_DEFAULT,
    venue=VENUE_IN_SANDBOX_GATE,
)

JANITOR_BOOTSTRAP_RECIPE_FIELD = IntegrationField(
    attribute="janitor_bootstrap_recipe",
    key=JANITOR_BOOTSTRAP_RECIPE_KEY,
    path=JANITOR_BOOTSTRAP_RECIPE_KEY,
    shape=SHAPE_ARGV,
    fleet_default=JANITOR_BOOTSTRAP_RECIPE_DEFAULT,
    parent_key=JANITOR_BOOTSTRAP_KEY,
)

CORE_REPO_URL_FIELD = IntegrationField(
    attribute="core_repo_url",
    key=COMPAT_CORE_REPO_KEY,
    path="compat.core_repo",
    shape=SHAPE_NAME,
    fleet_default=FLEET_CORE_REPO_URL,
)

CORE_PINNED_REF_FIELD = IntegrationField(
    attribute="core_pinned_ref",
    key=COMPAT_PINNED_KEY,
    path="compat.pinned",
    shape=SHAPE_NAME,
    required=True,
)

PREPARE_TOOLCHAIN_MISE_FIELD = IntegrationField(
    attribute="prepare_toolchain_mise",
    key=PREPARE_TOOLCHAIN_MISE_KEY,
    path=PREPARE_TOOLCHAIN_MISE_KEY,
    shape=SHAPE_ARGV,
    fleet_default=TOOLCHAIN_NO_OP,
)

PREPARE_TOOLCHAIN_LEFTHOOK_FIELD = IntegrationField(
    attribute="prepare_toolchain_lefthook",
    key=PREPARE_TOOLCHAIN_LEFTHOOK_KEY,
    path=PREPARE_TOOLCHAIN_LEFTHOOK_KEY,
    shape=SHAPE_ARGV,
    fleet_default=TOOLCHAIN_NO_OP,
)

DEFAULT_BRANCH_FIELD = IntegrationField(
    attribute="default_branch",
    key=DEFAULT_BRANCH_KEY,
    path=DEFAULT_BRANCH_KEY,
    shape=SHAPE_NAME,
    required=True,
    declared_in_config=False,
)

MERGE_MODE_FIELD = IntegrationField(
    attribute="merge_mode",
    key=MERGE_MODE_KEY,
    path=MERGE_MODE_KEY,
    shape=SHAPE_ENUM,
    fleet_default=MERGE_MODE_DEFAULT,
    admitted=MERGE_MODES,
)

SANDBOX_EXEMPT_MARKER_FIELD = IntegrationField(
    attribute="sandbox_exempt_marker",
    key=SANDBOX_EXEMPT_MARKER_KEY,
    path=SANDBOX_EXEMPT_MARKER_KEY,
    shape=SHAPE_ENUM,
    fleet_default=SANDBOX_EXEMPT_MARKER_DEFAULT,
    admitted=SANDBOX_EXEMPT_MARKERS,
)

# The CLOSED set. Order is the order a validation pass enumerates defects in, so
# it is grouped by family rather than alphabetically: an adopter reading one
# refusal sees its pipeline, then its janitor, then its core, then its sandbox.
INTEGRATION_FIELDS: tuple[IntegrationField, ...] = (
    MASTER_CI_WORKFLOW_FIELD,
    MASTER_CI_JOB_FIELD,
    JANITOR_CHECK_SUITE_FIELD,
    SANDBOX_CHECK_SUITE_FIELD,
    JANITOR_BOOTSTRAP_RECIPE_FIELD,
    CORE_REPO_URL_FIELD,
    CORE_PINNED_REF_FIELD,
    PREPARE_TOOLCHAIN_MISE_FIELD,
    PREPARE_TOOLCHAIN_LEFTHOOK_FIELD,
    DEFAULT_BRANCH_FIELD,
    MERGE_MODE_FIELD,
    SANDBOX_EXEMPT_MARKER_FIELD,
)
