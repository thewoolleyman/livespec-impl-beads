"""Focused tests for the declared janitor check-suite and its resolution.

Covers `_dispatcher_check_suite_view`: the committed
`dispatcher.janitor.check_suite` reader, the fleet default convention an ABSENT
key falls back to, the subordination of the uncommitted per-invocation
`--janitor` override to a committed declaration, the defects a PRESENT key can
carry (which never slide onto the convention), and the operator-facing prose
every unresolvable-check-suite refusal renders.

The last two cases cover the two `--janitor` ENTRY POINTS -- the dispatch
preamble and the reconcile valve -- where an unusable declaration has to refuse
BEFORE a run exists, because a present-but-unusable declaration resolves no
command at all and would otherwise reach the janitor as an empty argv.
"""

from __future__ import annotations

import argparse
import shlex
from inspect import signature
from pathlib import Path

import pytest
from livespec_orchestrator_beads_fabro.commands._dispatcher_check_suite_view import (
    DECLARED_RESOLUTION,
    DEFAULT_CHECK_SUITE,
    DEFAULT_RESOLUTION,
    JANITOR_CHECK_SUITE_KEY,
    OVERRIDE_RESOLUTION,
    UNRESOLVED_CHECK_SUITE,
    check_suite_refusal,
    check_suite_resolution_sentence,
    janitor_check_suite_from_block,
    resolve_janitor_check_suite,
)
from livespec_orchestrator_beads_fabro.commands._drive_config_schema import config_key_by_name
from livespec_orchestrator_beads_fabro.commands.dispatcher import dispatch_preamble, main
from livespec_orchestrator_beads_fabro.store import append_work_item
from livespec_orchestrator_beads_fabro.types import StoreConfig, WorkItem

_EXIT_PRECONDITION_ERROR = 3
_ADOPTER_CHECK_SUITE = "./scripts/ci.sh --all"
_FLEET_DEFAULT_ARGV = (
    "mise",
    "exec",
    "--",
    "just",
    "check-no-workflow-edits",
    "install-worktree-pack",
    "check",
)


def test_an_absent_key_resolves_the_fleet_default_convention() -> None:
    """An absent key is an ANSWER -- this repository uses the fleet convention."""
    check_suite = janitor_check_suite_from_block(block={}, janitor=None)

    assert check_suite.resolution == DEFAULT_RESOLUTION
    assert check_suite.defect is None
    assert check_suite.command == _FLEET_DEFAULT_ARGV
    assert check_suite.text == DEFAULT_CHECK_SUITE
    # The prose and the argv are one artifact, so an operator sentence can
    # never name a command line the janitor does not run.
    assert tuple(shlex.split(DEFAULT_CHECK_SUITE)) == _FLEET_DEFAULT_ARGV


def test_a_janitor_block_without_the_key_is_still_an_absent_declaration() -> None:
    """Presence is tested on the check-suite key, not on the block that holds it."""
    check_suite = janitor_check_suite_from_block(block={"janitor": {}}, janitor=None)

    assert check_suite.resolution == DEFAULT_RESOLUTION
    assert check_suite.command == _FLEET_DEFAULT_ARGV


def test_a_declared_check_suite_runs_verbatim_with_no_wrapper_imposed() -> None:
    """No `mise exec --` prefix: imposing our invocation on an adopter is the defect."""
    check_suite = janitor_check_suite_from_block(
        block={"janitor": {"check_suite": _ADOPTER_CHECK_SUITE}}, janitor=None
    )

    assert check_suite.resolution == DECLARED_RESOLUTION
    assert check_suite.defect is None
    assert check_suite.text == _ADOPTER_CHECK_SUITE
    assert check_suite.command == ("./scripts/ci.sh", "--all")
    # No `mise exec --` prefix, and nothing else of ours, is prepended: the
    # resolved command IS the argv `janitor_argv` hands the janitor.
    assert "mise" not in check_suite.command


def test_a_declared_check_suite_is_split_with_shell_quoting_honoured() -> None:
    check_suite = janitor_check_suite_from_block(
        block={"janitor": {"check_suite": "sh -c 'run the checks'"}}, janitor=None
    )

    assert check_suite.command == ("sh", "-c", "run the checks")


def test_a_committed_declaration_outranks_the_per_invocation_override() -> None:
    """Committed configuration only: an uncommitted argv may not displace policy."""
    check_suite = janitor_check_suite_from_block(
        block={"janitor": {"check_suite": _ADOPTER_CHECK_SUITE}},
        janitor=("echo", "override"),
    )

    assert check_suite.resolution == DECLARED_RESOLUTION
    assert check_suite.command == ("./scripts/ci.sh", "--all")


def test_the_override_still_applies_where_no_check_suite_is_declared() -> None:
    """`--janitor` survives, scoped to a repository that has declared nothing."""
    check_suite = janitor_check_suite_from_block(block={}, janitor=("echo", "hi"))

    assert check_suite.resolution == OVERRIDE_RESOLUTION
    assert check_suite.command == ("echo", "hi")
    assert check_suite.text == "echo hi"


@pytest.mark.parametrize(
    ("declared", "expected_defect_fragment"),
    [
        pytest.param("just check", "is not a mapping", id="not-a-mapping"),
        pytest.param({"check_suite": None}, "not a non-empty string", id="null-check-suite"),
        pytest.param({"check_suite": 7}, "not a non-empty string", id="non-string-check-suite"),
        pytest.param({"check_suite": "   "}, "not a non-empty string", id="blank-check-suite"),
        pytest.param({"check_suite": "sh -c 'unbalanced"}, "does not parse", id="unbalanced"),
        pytest.param({"check_suite": "''"}, "names no program", id="no-tokens"),
    ],
)
def test_a_present_but_unusable_declaration_is_a_defect_not_a_fallback(
    declared: object, expected_defect_fragment: str
) -> None:
    """Falling back here would run a check-suite the repository denied is its own."""
    check_suite = janitor_check_suite_from_block(block={"janitor": declared}, janitor=None)

    assert check_suite.defect is not None
    assert expected_defect_fragment in check_suite.defect
    assert check_suite.resolution == DECLARED_RESOLUTION
    assert check_suite.text == UNRESOLVED_CHECK_SUITE
    assert check_suite.command == ()


def test_a_defective_declaration_is_not_rescued_by_the_per_invocation_override() -> None:
    """A defect refuses; it does not quietly hand the run to an uncommitted argv."""
    check_suite = janitor_check_suite_from_block(
        block={"janitor": {"check_suite": None}}, janitor=("echo", "hi")
    )

    assert check_suite.defect is not None
    assert check_suite.command == ()


def test_a_null_declaration_refuses_with_a_refusal_naming_the_key() -> None:
    """A key written as JSON null is a present declaration that names nothing."""
    refusal = check_suite_refusal(
        check_suite=janitor_check_suite_from_block(
            block={"janitor": {"check_suite": None}}, janitor=None
        )
    )

    assert refusal is not None
    assert refusal.startswith("ERROR: the post-merge janitor check-suite is unresolvable")
    assert JANITOR_CHECK_SUITE_KEY in refusal
    assert DEFAULT_CHECK_SUITE not in refusal


def test_a_resolvable_check_suite_earns_no_refusal() -> None:
    assert (
        check_suite_refusal(check_suite=janitor_check_suite_from_block(block={}, janitor=None))
        is None
    )


def test_the_resolution_sentence_names_the_default_and_where_to_declare_otherwise() -> None:
    sentence = check_suite_resolution_sentence(
        check_suite=janitor_check_suite_from_block(block={}, janitor=None)
    )

    assert "Resolution attempted: default convention" in sentence
    assert DEFAULT_CHECK_SUITE in sentence
    assert JANITOR_CHECK_SUITE_KEY in sentence


def test_the_resolution_sentence_names_a_declared_check_suite_and_its_key() -> None:
    sentence = check_suite_resolution_sentence(
        check_suite=janitor_check_suite_from_block(
            block={"janitor": {"check_suite": _ADOPTER_CHECK_SUITE}}, janitor=None
        )
    )

    assert "Resolution attempted: declared" in sentence
    assert _ADOPTER_CHECK_SUITE in sentence
    assert JANITOR_CHECK_SUITE_KEY in sentence


def test_the_resolution_sentence_names_the_override_as_the_unscoped_route() -> None:
    sentence = check_suite_resolution_sentence(
        check_suite=janitor_check_suite_from_block(block={}, janitor=("echo", "hi"))
    )

    assert "per-invocation `--janitor` override" in sentence
    assert JANITOR_CHECK_SUITE_KEY in sentence


def test_the_resolution_sentence_reports_a_defect_as_a_declaration_not_the_convention() -> None:
    sentence = check_suite_resolution_sentence(
        check_suite=janitor_check_suite_from_block(
            block={"janitor": {"check_suite": ""}}, janitor=None
        )
    )

    assert "Resolution attempted: declared" in sentence
    assert "present but unusable" in sentence
    assert DEFAULT_CHECK_SUITE not in sentence


def test_the_check_suite_resolves_from_the_committed_livespec_jsonc(tmp_path: Path) -> None:
    _ = (tmp_path / ".livespec.jsonc").write_text(
        '{"livespec-orchestrator-beads-fabro": {"dispatcher": '
        '{"janitor": {"check_suite": "make ci"}}}}',
        encoding="utf-8",
    )

    check_suite = resolve_janitor_check_suite(cwd=tmp_path, janitor=("echo", "hi"))

    assert check_suite.command == ("make", "ci")
    assert check_suite.resolution == DECLARED_RESOLUTION


def test_a_repository_declaring_no_dispatcher_block_at_all_uses_the_convention(
    tmp_path: Path,
) -> None:
    assert resolve_janitor_check_suite(cwd=tmp_path, janitor=None).text == DEFAULT_CHECK_SUITE


def test_the_key_has_no_per_item_override(tmp_path: Path) -> None:
    """Committed configuration only: nothing per-item can redirect the check-suite.

    The key is absent from the API-configurable / per-item-override registry, so
    no ledger label or API call can set it; and no resolution surface accepts a
    work-item at all, so there is no input a per-item value could arrive through.
    The only non-committed input either surface takes is the `--janitor` argv,
    which the declaration outranks.
    """
    assert config_key_by_name(key="janitor") is None
    assert set(signature(resolve_janitor_check_suite).parameters) == {"cwd", "janitor"}
    assert set(signature(janitor_check_suite_from_block).parameters) == {"block", "janitor"}
    _ = (tmp_path / ".livespec.jsonc").write_text(
        '{"livespec-orchestrator-beads-fabro": {"dispatcher": '
        '{"janitor": {"check_suite": "make ci"}}}}',
        encoding="utf-8",
    )
    assert resolve_janitor_check_suite(cwd=tmp_path, janitor=None).text == "make ci"


def _repo_declaring_a_null_check_suite(*, tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _ = (repo / ".livespec.jsonc").write_text(
        '{"livespec-orchestrator-beads-fabro": {'
        '"connection": {"prefix": "bd-ib"}, '
        '"dispatcher": {"acceptance_mode": "ai-only", "janitor": {"check_suite": null}}'
        "}}",
        encoding="utf-8",
    )
    return repo


def test_the_dispatch_preamble_refuses_an_unusable_declaration_before_any_run(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    """Exit 3, and the refusal names the key the operator has to go and fix."""
    repo = _repo_declaring_a_null_check_suite(tmp_path=tmp_path)
    args = argparse.Namespace(fabro_bin=None, janitor=None, journal=None)

    janitor, exit_code = dispatch_preamble(args=args, repo=repo)

    assert (janitor, exit_code) == (None, _EXIT_PRECONDITION_ERROR)
    assert JANITOR_CHECK_SUITE_KEY in capsys.readouterr().err


def test_the_reconcile_valve_refuses_an_unusable_declaration(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    """The second `--janitor` entry point refuses on the same defect."""
    repo = _repo_declaring_a_null_check_suite(tmp_path=tmp_path)
    item = WorkItem(
        id="bd-ib-lza6",
        type="task",
        status="active",
        title="Merged active item",
        description="Reconcile the already merged PR.",
        origin="freeform",
        gap_id=None,
        rank="a2",
        assignee=None,
        depends_on=(),
        captured_at="2026-07-19T00:00:00Z",
        resolution=None,
        reason=None,
        audit=None,
        superseded_by=None,
        admission_policy="auto",
        acceptance_policy="ai-only",
    )
    append_work_item(
        path=StoreConfig(
            tenant="livespec-impl-beads",
            prefix="livespec-impl-beads",
            server_user="livespec-impl-beads",
            database="livespec-impl-beads",
            bd_path="bd",
            fake=True,
        ),
        item=item,
    )

    exit_code = main(argv=["reconcile-merged", "--repo", str(repo), "--item", item.id])

    assert exit_code == _EXIT_PRECONDITION_ERROR
    assert JANITOR_CHECK_SUITE_KEY in capsys.readouterr().err
