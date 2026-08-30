"""Argv builders for the Dispatcher planning layer."""

from __future__ import annotations

import json
import re
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from livespec_orchestrator_beads_fabro.commands import _jsonc

if TYPE_CHECKING:
    from livespec_orchestrator_beads_fabro.commands._codex_model_tiers import CodexModelTier
    from livespec_orchestrator_beads_fabro.commands._dispatcher_janitor_bootstrap_recipe import (
        JanitorBootstrapRecipe,
    )
    from livespec_orchestrator_beads_fabro.commands._dispatcher_janitor_check_suite import (
        JanitorCheckSuite,
    )
    from livespec_orchestrator_beads_fabro.commands._dispatcher_plan_build import DispatchPlan

__all__: list[str] = [
    "CODEX_ADAPTER_BASE",
    "CODEX_ADAPTER_COMMAND",
    "CODEX_AGENT_MODE_READ_ONLY",
    "CODEX_AGENT_MODE_WRITE",
    "CODEX_IMPLEMENTER_ADAPTER",
    "FleetMembers",
    "codex_adapter",
    "janitor_argv",
    "janitor_bootstrap_argv",
    "janitor_checkout_path",
    "janitor_core_checkout_path",
    "janitor_core_clone_argv",
    "janitor_core_ref_from_config",
    "janitor_reconcile_checkout_path",
    "janitor_trust_argv",
    "janitor_worktree_add_argv",
    "janitor_worktree_remove_argv",
    "parse_fleet_members",
    "pr_arm_argv",
    "pr_update_branch_argv",
    "pr_view_argv",
    "pull_primary_argv",
]

_DEFAULT_JANITOR_CORE_REPO_URL = "https://github.com/thewoolleyman/livespec.git"
_DEFAULT_JANITOR_CORE_REF = "master"


# The Codex ACP adapter command: the successor `@agentclientprotocol/codex-acp`
# package invoked AT ITS BAKED PATH (the Codex-ACP-node-model-pins contract in
# `SPECIFICATION/contracts.md`, whose "identified by its baked path, never by
# package name" rule this implements). livespec-dev-tooling's sandbox image
# installs that package under the dedicated npm prefix `/opt/livespec/codex-acp`,
# which owns NO global bin link.
#
# WHY A PATH RATHER THAN `npx --no-install <package>`. The retired npx form was
# chosen for four properties: version-free, fetch-free (so it runs under
# `--network none`), and the baked image as the SINGLE source of truth for the
# adapter version. The baked path keeps all of them and adds the one the npx
# form lacked — an unambiguous IDENTITY. `npx` resolves a package's bin through
# the SHARED global bin link, so where two `codex-acp` packages are installed,
# invoking EITHER package name runs whichever package owns that link: the
# rendered string can name one package while executing another, which defeats
# that contract's own claim that a reader can predict the adapter string and
# check it against `run_turn.command`. Measured on the released image
# python-agent-v1.35.0 (2026-08-26): the baked path reports
# `@agentclientprotocol/codex-acp 1.6.2` while `npx --no-install
# @zed-industries/codex-acp` still runs the predecessor 0.16.0.
CODEX_ADAPTER_COMMAND = "/opt/livespec/codex-acp/bin/codex-acp"

# `INITIAL_AGENT_MODE` values. The implementer and publish classes WRITE (they
# edit the workspace, commit, and push), so they take `agent-full-access`; a
# node that performs no writes — a reviewer — takes `read-only`.
CODEX_AGENT_MODE_WRITE = "agent-full-access"
CODEX_AGENT_MODE_READ_ONLY = "read-only"

# The sandbox and approval posture every rendered Codex adapter declares,
# pinned or not. The implementer already runs inside Fabro's ephemeral Docker
# sandbox; on the current host AppArmor blocks Codex's inner bwrap namespace,
# after which Fabro grants an ACP permission retry outside that inner sandbox.
# `sandbox_mode=danger-full-access` makes the real Docker boundary explicit and
# `approval_policy=never` removes that failed escalation path.
_CODEX_POSTURE_CONFIG: dict[str, str] = {
    "approval_policy": "never",
    "sandbox_mode": "danger-full-access",
}

# The posture object's JSON bytes, spelled out literally so a reader can
# reconstruct the base string below from this module exactly as contracts.md
# spells it out — the two are bound by a test rather than by trust. This is the
# same object `json.dumps(_CODEX_POSTURE_CONFIG, sort_keys=True, separators=...)`
# renders for an un-pinned tier, restated so a renderer change has to be made
# twice before the binding test stops failing.
_CODEX_POSTURE_JSON = '{"approval_policy":"never","sandbox_mode":"danger-full-access"}'

# The UN-PINNED BASE STRING for a write-capable node. The read-only variant is
# this string with `INITIAL_AGENT_MODE=read-only`.
#
# WHY THE JSON GOES THROUGH `shlex.quote`. The rendered adapter string is
# SHELL-TOKENIZED before it is executed — fabro splits `acp.command` with
# `shlex::split` in `AcpProcessSpec::from_command_attr` — and POSIX tokenization
# CONSUMES quote characters. An unquoted JSON object therefore reaches the
# adapter as `{approval_policy:never,...}` and its own `JSON.parse` rejects it,
# which is exactly how release 0.82.0 could not start a single Codex-backed node
# (work-item bd-ib-qulf). The quoting is part of the byte-identity referent the
# Codex-ACP-node-model-pins contract states, so an implementation rendering bare
# JSON is NOT byte-identical to the base string.
#
# The non-rotatable refresh sentinel's load-but-cannot-refresh behavior
# (project_codex_auth_snapshot; tracked by bd-ib-ss7rkr) is RE-VERIFIED on every
# adapter change by the Codex-mode golden-master at
# orchestrator-image/acceptance-live-golden-master.sh, whose injected prepare
# steps install the successor under the same dedicated prefix and read the
# projected auth.json back from the sandbox `$CODEX_HOME`.
CODEX_ADAPTER_BASE = (
    f"CODEX_CONFIG={shlex.quote(_CODEX_POSTURE_JSON)} "
    f"INITIAL_AGENT_MODE={CODEX_AGENT_MODE_WRITE} {CODEX_ADAPTER_COMMAND}"
)

# Back-compat alias for the un-pinned adapter. `codex_adapter` is what the
# engine calls; this name is the base string every tier is built on.
CODEX_IMPLEMENTER_ADAPTER = CODEX_ADAPTER_BASE


def codex_adapter(*, tier: CodexModelTier, agent_mode: str = CODEX_AGENT_MODE_WRITE) -> str:
    """Render the Codex ACP adapter command for one resolved model tier.

    The settings ride the adapter's own ENVIRONMENT as leading `KEY=value`
    assignments in sorted key order, which is what makes them expressible at
    all: fabro REJECTS `model` / `reasoning_effort` as acp-node attributes
    (fabro-validate `backend_valid`), so a node attr or a model_stylesheet is
    not available here. The successor adapter reads its whole session
    configuration from `CODEX_CONFIG` — a JSON object merged into that
    configuration — rather than from the `-c key=value` arguments the retired
    predecessor took. That JSON object is emitted through `shlex.quote`: the
    rendered string is POSIX-tokenized before execution, and the retired `-c`
    form survived that tokenization only because its values carried no quote
    characters of their own (see `CODEX_ADAPTER_BASE` for the failure the
    unquoted successor produced).

    A PINNED tier is the un-pinned base string with `model` and
    `model_reasoning_effort` ADDED inside `CODEX_CONFIG`, the object's keys
    remaining in sorted order; nothing else changes. An un-pinned tier renders
    the base string byte-for-byte, so the opt-out is a true no-op rather than a
    differently-spelled default carrying empty values.

    The tier's `compaction_token_limit` stays an adapter ARGUMENT
    (`model_auto_compact_token_limit`), which is where the ACP-node-timeouts
    contract in `SPECIFICATION/contracts.md` puts it, and it is emitted
    INDEPENDENTLY of the model pin: a node can opt out of the model override
    while still needing its compaction threshold moved, so folding the limit
    into the `pinned` branch would silently drop it for exactly that
    configuration.
    """
    config = dict(_CODEX_POSTURE_CONFIG)
    if tier.pinned:
        config["model"] = tier.model
        config["model_reasoning_effort"] = tier.reasoning_effort
    rendered_config = shlex.quote(json.dumps(config, sort_keys=True, separators=(",", ":")))
    compaction = (
        ""
        if tier.compaction_token_limit == 0
        else f" -c model_auto_compact_token_limit={tier.compaction_token_limit}"
    )
    return (
        f"CODEX_CONFIG={rendered_config} INITIAL_AGENT_MODE={agent_mode} "
        f"{CODEX_ADAPTER_COMMAND}{compaction}"
    )


# GitHub owner / repo-name shape. The matched values are spliced into
# prepare-step clone scripts, so anything outside this conservative
# alphabet is refused at parse time (fail-fast over fail-soft: the
# fleet manifest is a tightly-owned committed file on livespec master,
# and a malformed member is a real problem to surface, not skip).
_GITHUB_SLUG_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


@dataclass(frozen=True, kw_only=True)
class FleetMembers:
    """Owner + member repo names parsed from livespec's .livespec-fleet-manifest.jsonc.

    The fleet manifest (livespec non-functional-requirements.md) is the
    canonical family member registry; the
    `class` field of each member is irrelevant here — every member gets
    a sandbox sibling clone, so any future cross-repo check resolves.
    """

    owner: str
    repos: tuple[str, ...]


def parse_fleet_members(*, manifest_text: str) -> FleetMembers | None:
    """Parse .livespec-fleet-manifest.jsonc text into FleetMembers; None when malformed.

    Accepts the committed shape on livespec master: a JSONC object with
    a string `owner` and a non-empty `fleet` list of objects each
    carrying a string `repo`. The livespec v148 rename made `fleet` the
    canonical key; the pre-rename `members` key is accepted as a fallback
    (matching livespec-dev-tooling's `(.fleet // .members)` parser) so a
    not-yet-migrated manifest copy keeps resolving. Owner and repo values
    must be GitHub-slug-shaped (they are spliced into clone scripts). Any
    deviation yields None — the caller refuses the dispatch with an
    actionable error rather than cloning from a guessed member list.
    """
    parsed_raw = _jsonc.parse(text=manifest_text)
    if isinstance(parsed_raw, _jsonc.JsoncFailure):
        return None
    if not isinstance(parsed_raw, dict):
        return None
    parsed = cast("dict[str, Any]", parsed_raw)
    owner_raw: object = parsed.get("owner")
    fleet_raw: object = parsed.get("fleet")
    members_raw: object = fleet_raw if fleet_raw is not None else parsed.get("members")
    if not isinstance(owner_raw, str) or not isinstance(members_raw, list):
        return None
    if _GITHUB_SLUG_PATTERN.match(owner_raw) is None:
        return None
    repos: list[str] = []
    for member_raw in cast("list[object]", members_raw):
        repo_name = _parse_member_repo(member_raw=member_raw)
        if repo_name is None:
            return None
        repos.append(repo_name)
    return FleetMembers(owner=owner_raw, repos=tuple(repos)) if repos else None


def _parse_member_repo(*, member_raw: object) -> str | None:
    """Extract a validated repo name from one fleet-manifest member entry."""
    if not isinstance(member_raw, dict):
        return None
    repo_raw: object = cast("dict[str, Any]", member_raw).get("repo")
    if not isinstance(repo_raw, str) or _GITHUB_SLUG_PATTERN.match(repo_raw) is None:
        return None
    return repo_raw


def janitor_argv(*, check_suite: JanitorCheckSuite) -> tuple[str, ...]:
    """The post-merge janitor's argv: the resolved check-suite, invoked VERBATIM.

    The check-suite is DECLARED (`dispatcher.janitor.check_suite`) with the
    fleet convention as its default, so this builder no longer names one and,
    just as importantly, no longer prepends a wrapper of its own: presuming our
    `mise exec --` invocation of every adopter's command is the defect the
    janitor check-suite resolution clause retires.
    """
    return check_suite.command


def janitor_checkout_path(*, repo: Path, work_item_id: str) -> Path:
    """The post-merge janitor's fresh-checkout venue under the family worktree root.

    The checkout must stay outside the target repo so a stray `git add -A`
    cannot stage it. It also stays out of the system temp dir: the family
    pyproject's `[tool.coverage.run]` omit carries `/tmp/*` (a guard
    against measured tempfile artifacts that must stay), so a /tmp venue
    omits every source file inside the checkout — coverage measures zero
    files and check-per-file-coverage dies with NoDataError, false-redding
    a merged-green change (work-item livespec-impl-beads-1l6; reproduced
    in the preserved tpu checkout). `git worktree add` creates the missing
    parent dirs itself.
    """
    return Path.home() / ".worktrees" / repo.name / f"janitor-{work_item_id}"


def janitor_core_checkout_path(*, janitor_checkout: Path) -> Path:
    """Livespec core clone provisioned inside the fresh janitor checkout."""
    return janitor_checkout / ".livespec-core"


def janitor_reconcile_checkout_path(*, repo: Path, work_item_id: str) -> Path:
    """The reconcile valve's janitor venue, distinct from live dispatch checkouts."""
    return Path.home() / ".worktrees" / repo.name / f"janitor-reconcile-{work_item_id}"


def janitor_core_ref_from_config(*, config_text: str) -> str:
    """Resolve the livespec core ref pinned by the target repo config."""
    parsed_raw = _jsonc.parse(text=config_text)
    if isinstance(parsed_raw, _jsonc.JsoncFailure):
        return _DEFAULT_JANITOR_CORE_REF
    if not isinstance(parsed_raw, dict):
        return _DEFAULT_JANITOR_CORE_REF
    parsed = cast("dict[str, object]", parsed_raw)
    plugin_raw: object = parsed.get("livespec-orchestrator-beads-fabro")
    if not isinstance(plugin_raw, dict):
        return _DEFAULT_JANITOR_CORE_REF
    compat_raw: object = cast("dict[str, object]", plugin_raw).get("compat")
    if not isinstance(compat_raw, dict):
        return _DEFAULT_JANITOR_CORE_REF
    pinned_raw: object = cast("dict[str, object]", compat_raw).get("pinned")
    if not isinstance(pinned_raw, str) or pinned_raw.strip() == "":
        return _DEFAULT_JANITOR_CORE_REF
    return pinned_raw.strip()


def pr_view_argv(*, plan: DispatchPlan) -> list[str]:
    return [
        "gh",
        "pr",
        "view",
        plan.branch,
        "--json",
        "number,state,autoMergeRequest,mergeStateStatus,mergeCommit,statusCheckRollup",
    ]


def pr_arm_argv(*, plan: DispatchPlan, number: int) -> list[str]:
    _ = plan
    return ["gh", "pr", "merge", str(number), "--rebase", "--auto", "--delete-branch"]


def pr_update_branch_argv(*, plan: DispatchPlan, number: int) -> list[str]:
    _ = plan
    return ["gh", "pr", "update-branch", str(number)]


def pull_primary_argv(*, plan: DispatchPlan) -> list[str]:
    return [
        "mise",
        "exec",
        "--",
        "sh",
        "-lc",
        (
            'branch="$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null '
            '|| printf master)"; branch="${branch#origin/}"; '
            'git -C "$1" pull --ff-only origin "$branch"'
        ),
        "pull-primary",
        str(plan.repo),
    ]


def janitor_worktree_add_argv(*, plan: DispatchPlan, ref: str) -> list[str]:
    """Provision the fresh detached janitor checkout at the merged ref.

    Plain `git` (no `mise exec`): worktree commands fire no hooks and
    need no pinned toolchain, and the checkout path is not yet
    mise-trusted at this point anyway.
    """
    return [
        "git",
        "-C",
        str(plan.repo),
        "worktree",
        "add",
        "--detach",
        str(plan.janitor_checkout),
        ref,
    ]


def janitor_worktree_remove_argv(*, plan: DispatchPlan) -> list[str]:
    """Remove the janitor checkout (both pre-clean and post-green cleanup).

    `--force` covers the untracked state a janitor run leaves behind
    (the self-provisioned `.venv`), and as the pre-clean it also clears
    a stale registration left by a crashed earlier dispatch of the same
    item.
    """
    return [
        "git",
        "-C",
        str(plan.repo),
        "worktree",
        "remove",
        "--force",
        str(plan.janitor_checkout),
    ]


def janitor_core_clone_argv(*, plan: DispatchPlan) -> list[str]:
    """Clone livespec core inside the fresh janitor checkout."""
    return [
        "git",
        "clone",
        "--quiet",
        "--depth",
        "1",
        "--branch",
        plan.janitor_core_ref,
        plan.janitor_core_repo_url,
        str(plan.janitor_core_checkout),
    ]


def janitor_trust_argv() -> list[str]:
    """Trust the janitor checkout's mise config (run with cwd=checkout).

    mise trust is per-PATH, so a freshly provisioned checkout is never
    pre-trusted and the default janitor's `mise exec` would refuse to
    run there. With no config file present, `mise trust` warns and
    exits 0, so this is safe to run unconditionally.
    """
    return ["mise", "trust"]


def janitor_bootstrap_argv(*, recipe: JanitorBootstrapRecipe) -> list[str]:
    """Install commit-refuse hooks in the primary checkout (run with cwd=plan.repo).

    Runs the governed repository's own RESOLVED hooks-only bootstrap recipe in
    the primary checkout so its pre-commit and pre-push hooks are present at
    `.git/hooks/` before `just check` runs in the janitor worktree - the shared
    `check-primary-checkout-commit-refuse-hook-installed` gate reads
    the same hooks_dir and fails when the bootstrap step was never run.
    Idempotent: safe to run on every dispatch.

    The recipe is DECLARED (`dispatcher.janitor_bootstrap.recipe`) with the
    fleet convention as its default, so this builder no longer names one:
    presuming our own `just` recipe of every adopter is the defect the
    janitor-bootstrap recipe resolution clause retires.
    """
    return list(recipe.command)
