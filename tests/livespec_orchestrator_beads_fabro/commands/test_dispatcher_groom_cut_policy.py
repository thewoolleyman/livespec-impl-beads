"""The two v100 groom-cut policy settings: parsed, manifested, and inert.

The dispatcher-policy-settings contract in `SPECIFICATION/contracts.md` gained
`dispatcher.groom_cut_approval` as its fourth policy setting and
`dispatcher.automated_regroom_cap` as its third rework cap when v100 ratified
the consensus-gated automated groom cut in the same file.
This slice makes both READABLE and nothing more, so the inertness case here is
load-bearing rather than decorative: it sets both keys and asserts the dispatch
plan built under them is byte-identical to the plan built without them, which
is the only way a "this changes nothing yet" claim can be checked at all.

The asymmetry of `groom_cut_approval`'s per-item override is the case worth
reading twice. Its label MAY lower an item to `human` and MUST NOT raise one
to `consensus`, which is exactly what a cap-shaped override would get wrong —
so both directions are asserted, against a global that would make a wrong
answer visible in each.

Both modules are reached through `importlib` rather than a top-level import
because the Red half of this file's own ritual must fail on an assertion, not
on a missing module.
"""

from __future__ import annotations

import json
from dataclasses import replace
from importlib import import_module
from pathlib import Path
from typing import Any, TypeVar

from livespec_orchestrator_beads_fabro.commands._dispatcher_plan import DispatchPlan, build_plan
from livespec_orchestrator_beads_fabro.commands._drive_config_schema import (
    api_configurable_key_manifest,
)
from livespec_orchestrator_beads_fabro.types import WorkItem
from returns.io import IOResult
from returns.unsafe import unsafe_perform_io

_REPO_ROOT = Path(__file__).resolve().parents[3]
_COMMANDS = (
    _REPO_ROOT / ".claude-plugin" / "scripts" / "livespec_orchestrator_beads_fabro" / "commands"
)
_SETTINGS_NAME = "livespec_orchestrator_beads_fabro.commands._dispatcher_policy_settings"
_OVERRIDES_NAME = "livespec_orchestrator_beads_fabro.commands._dispatcher_policy_overrides"
_OVERRIDES_PATH = _COMMANDS / "_dispatcher_policy_overrides.py"

_PLUGIN_BLOCK = "livespec-orchestrator-beads-fabro"
_NO_CONFIG_CWD = Path("tests/nonexistent-groom-cut-cwd")

_Value = TypeVar("_Value")


def _read(outcome: IOResult[_Value, object]) -> _Value:
    """The value out of a successful policy read.

    `unsafe_perform_io` is mandatory rather than decorative: `IOResult.unwrap`
    yields `IO[value]`, and comparing that wrapper to `2`/`"human"` passes
    nothing and fails everything.
    """
    return unsafe_perform_io(outcome.unwrap())


def _settings() -> Any:
    return import_module(_SETTINGS_NAME)


def _overrides() -> Any:
    assert _OVERRIDES_PATH.is_file()
    return import_module(_OVERRIDES_NAME)


def _item() -> WorkItem:
    base = WorkItem(
        id="bd-ib-groom",
        type="task",
        status="backlog",
        title="An epic awaiting a cut",
        description="Decompose the thing.",
        origin="freeform",
        gap_id=None,
        rank="a2",
        assignee=None,
        depends_on=(),
        captured_at="2026-09-06T00:00:00Z",
        resolution=None,
        reason=None,
        audit=None,
        superseded_by=None,
    )
    return replace(base)


def _config_text(*, dispatcher: dict[str, object]) -> str:
    return json.dumps({_PLUGIN_BLOCK: {"compat": {"pinned": "master"}, "dispatcher": dispatcher}})


def _write_config(*, tmp_path: Path, dispatcher: dict[str, object]) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    _ = (tmp_path / ".livespec.jsonc").write_text(
        _config_text(dispatcher=dispatcher), encoding="utf-8"
    )
    return tmp_path


def _plan(*, repo: Path, config_text: str) -> DispatchPlan:
    return build_plan(
        repo=repo,
        work_item_id="bd-ib-groom",
        workflow_toml=repo / "wf.toml",
        goal_file=repo / "goal.md",
        fabro_bin="fabro",
        janitor=None,
        janitor_checkout=repo / "janitor-co",
        config_text=config_text,
        default_branch="master",
    )


def test_the_two_settings_default_to_human_and_two_when_unconfigured() -> None:
    """An absent file is an ANSWER, so each read lands on its documented default."""
    settings = _settings()

    assert settings.DEFAULT_GROOM_CUT_APPROVAL == "human"
    assert settings.DEFAULT_AUTOMATED_REGROOM_CAP == 2
    assert _read(settings.resolve_groom_cut_approval(cwd=_NO_CONFIG_CWD)) == "human"
    assert _read(settings.resolve_automated_regroom_cap(cwd=_NO_CONFIG_CWD)) == 2


def test_the_enum_accepts_consensus_and_refuses_anything_else(tmp_path: Path) -> None:
    """`consensus` is the one other member; an unreadable value is a FAILURE, not a default."""
    settings = _settings()
    opted_in = _write_config(
        tmp_path=tmp_path / "in", dispatcher={"groom_cut_approval": "consensus"}
    )
    nonsense = _write_config(
        tmp_path=tmp_path / "out", dispatcher={"groom_cut_approval": "whenever"}
    )

    assert _read(settings.resolve_groom_cut_approval(cwd=opted_in)) == "consensus"
    failure = settings.resolve_groom_cut_approval(cwd=nonsense).failure()
    assert unsafe_perform_io(failure).setting == "groom_cut_approval"
    assert "one of consensus, human" in unsafe_perform_io(failure).detail


def test_the_regroom_cap_reads_a_configured_integer_and_refuses_zero(tmp_path: Path) -> None:
    """The cap is a bound on re-drafting rounds, so it floors at one like its siblings."""
    settings = _settings()
    configured = _write_config(tmp_path=tmp_path / "in", dispatcher={"automated_regroom_cap": 5})
    degenerate = _write_config(tmp_path=tmp_path / "out", dispatcher={"automated_regroom_cap": 0})

    assert _read(settings.resolve_automated_regroom_cap(cwd=configured)) == 5
    failure = settings.resolve_automated_regroom_cap(cwd=degenerate).failure()
    assert unsafe_perform_io(failure).setting == "automated_regroom_cap"


def test_a_per_item_label_lowers_to_human_but_cannot_raise_to_consensus(tmp_path: Path) -> None:
    """The asymmetry, asserted in BOTH directions against a global that would show a slip.

    Lowering runs against a `consensus` global, so honoring the label is the
    only way to read `human`. Raising runs against a `human` global, so
    honoring the label is the only way to read `consensus`. One global would
    have made one of the two answers indistinguishable from doing nothing.
    """
    overrides = _overrides()
    opted_in = _write_config(
        tmp_path=tmp_path / "in", dispatcher={"groom_cut_approval": "consensus"}
    )
    conservative = _write_config(
        tmp_path=tmp_path / "out", dispatcher={"groom_cut_approval": "human"}
    )
    lowered = overrides.effective_groom_cut_approval(
        item=_item(), cwd=opted_in, raw_labels=("groom-cut-approval:human",)
    )
    raised = overrides.effective_groom_cut_approval(
        item=_item(), cwd=conservative, raw_labels=("groom-cut-approval:consensus",)
    )

    assert _read(lowered) == "human"
    assert _read(raised) == "human"


def test_an_unlabeled_or_junk_labeled_item_inherits_the_global(tmp_path: Path) -> None:
    """Only the literal `human` overrides; a typo falls through rather than refusing."""
    overrides = _overrides()
    opted_in = _write_config(tmp_path=tmp_path, dispatcher={"groom_cut_approval": "consensus"})

    assert _read(overrides.effective_groom_cut_approval(item=_item(), cwd=opted_in)) == "consensus"
    assert (
        _read(
            overrides.effective_groom_cut_approval(
                item=_item(), cwd=opted_in, raw_labels=("groom-cut-approval:humann",)
            )
        )
        == "consensus"
    )


def test_the_regroom_cap_takes_a_per_item_label_in_the_existing_cap_shape(tmp_path: Path) -> None:
    """Same `<setting>:<value>` shape as `review-fix-cap:` and `acceptance-rework-cap:`."""
    overrides = _overrides()
    cwd = _write_config(tmp_path=tmp_path, dispatcher={"automated_regroom_cap": 5})

    assert (
        _read(
            overrides.effective_automated_regroom_cap(
                item=_item(), cwd=cwd, raw_labels=("automated-regroom-cap:9",)
            )
        )
        == 9
    )
    assert (
        _read(
            overrides.effective_automated_regroom_cap(
                item=_item(), cwd=cwd, raw_labels=("automated-regroom-cap:0",)
            )
        )
        == 5
    )


def test_both_keys_join_the_api_configurable_key_manifest() -> None:
    """Every policy setting MUST be settable through the orchestrator API."""
    keys = {str(entry["key"]): entry for entry in api_configurable_key_manifest()["keys"]}

    assert keys["groom_cut_approval"] == {
        "key": "groom_cut_approval",
        "type": "enum",
        "default": "human",
        "values": ["human", "consensus"],
        "per_item_override": True,
    }
    assert keys["automated_regroom_cap"] == {
        "key": "automated_regroom_cap",
        "type": "positive_integer",
        "default": 2,
        "per_item_override": True,
    }


def test_both_keys_are_inert_and_leave_the_dispatch_plan_byte_identical(tmp_path: Path) -> None:
    """Readable configuration and nothing more: no dispatch seam reads either key yet.

    The two settings are read back off the same `.livespec.jsonc` the plan is
    built from, so the case proves the keys ARE present and understood before
    it proves they change nothing.
    """
    settings = _settings()
    overrides = _overrides()
    groom_settings: dict[str, object] = {
        "groom_cut_approval": "consensus",
        "automated_regroom_cap": 7,
    }
    cwd = _write_config(tmp_path=tmp_path, dispatcher=groom_settings)

    assert _read(settings.resolve_groom_cut_approval(cwd=cwd)) == "consensus"
    assert _read(settings.resolve_automated_regroom_cap(cwd=cwd)) == 7
    assert _read(overrides.effective_groom_cut_approval(item=_item(), cwd=cwd)) == "consensus"
    assert _read(overrides.effective_automated_regroom_cap(item=_item(), cwd=cwd)) == 7
    assert repr(_plan(repo=cwd, config_text=_config_text(dispatcher=groom_settings))) == repr(
        _plan(repo=cwd, config_text=_config_text(dispatcher={}))
    )
