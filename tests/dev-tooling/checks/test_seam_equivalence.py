"""Tests for the integration-input seam-equivalence guard.

The guard reports an ABSENCE, and it does so over a payload that references no
integration token yet, so a broken scanner would print exactly what a conformant
payload prints. These tests therefore carry the two controls the work-item makes
non-optional plus a NEGATIVE CONTROL per direction of the equality: every
assertion below is made against a payload seeded on disk and read back through
the check's own scan path, never against the return value of a write call.
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path
from types import ModuleType

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CHECK_PATH = _REPO_ROOT / "dev-tooling" / "checks" / "seam_equivalence.py"

# A run config carrying one token per position class: a prepare-step script
# (rendered), an input default (not rendered), and a comment (no attribute at
# all). Written here rather than derived from the payload because the committed
# payload deliberately carries none of them yet.
_RUN_CONFIG = """
[run.inputs]
sandbox_check_suite = "{{ inputs.sandbox_check_suite }}"

[[run.prepare.steps]]
script = "just {{ inputs.sandbox_check_suite }}"

# a comment holding {{ inputs.merge_mode }}
"""


def _load_check() -> ModuleType:
    assert _CHECK_PATH.is_file()
    spec = importlib.util.spec_from_file_location("seam_equivalence_under_test", _CHECK_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(name="check")
def _check_fixture() -> ModuleType:
    return _load_check()


@pytest.fixture(name="scan")
def _scan_fixture(check: ModuleType) -> ModuleType:
    assert check is not None
    return sys.modules["_seam_equivalence_scan"]


@pytest.fixture(name="rules")
def _rules_fixture(check: ModuleType) -> ModuleType:
    # The INSTANCE the check imported, not a second load by path: a
    # monkeypatched constant has to land on the object the check reads.
    assert check is not None
    return sys.modules["_seam_equivalence_findings"]


def _seed_repo(*, repo_root: Path, check: ModuleType) -> Path:
    """Copy the real payload, config and control fixture into a throwaway root."""
    source = check.payload_dir(repo_root=_REPO_ROOT)
    target = check.payload_dir(repo_root=repo_root)
    _ = shutil.copytree(source, target)
    _ = shutil.copy2(_REPO_ROOT / ".livespec.jsonc", repo_root / ".livespec.jsonc")
    fixture = check.fixture_path(repo_root=repo_root)
    fixture.parent.mkdir(parents=True, exist_ok=True)
    _ = shutil.copy2(check.fixture_path(repo_root=_REPO_ROOT), fixture)
    return target


# ---------------------------------------------------------------------------
# The payload as it stands.
# ---------------------------------------------------------------------------


def test_the_check_is_installed_where_the_justfile_target_invokes_it() -> None:
    assert _CHECK_PATH.is_file()


def test_committed_payload_keeps_the_seam_equivalence(check: ModuleType) -> None:
    assert check.payload_findings(repo_root=_REPO_ROOT) == []


def test_controls_hold_against_the_real_repo(check: ModuleType) -> None:
    assert check.control_failures(repo_root=_REPO_ROOT) == []


def test_main_passes_against_the_real_repo(
    check: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(_REPO_ROOT)

    assert check.main() == 0


def test_scan_of_the_real_payload_returns_the_tokens_that_are_there(check: ModuleType) -> None:
    occurrences = check.payload_occurrences(repo_root=_REPO_ROOT)

    # The instrument must be able to return a hit before its clean report on
    # the integration subset means anything: the adapter and policy tokens ARE
    # in the payload, so a scan that found none of them is broken, not clean.
    assert {occurrence.name for occurrence in occurrences if occurrence.position == "acp.command"}
    assert {occurrence.name for occurrence in occurrences if occurrence.position == "condition"}
    assert all(occurrence.rendered for occurrence in occurrences)


# ---------------------------------------------------------------------------
# Criterion 1 — the equality, in both directions.
# ---------------------------------------------------------------------------


def test_a_workflow_token_without_a_rendered_input_is_named(rules: ModuleType) -> None:
    findings = rules.equivalence_findings(
        referenced=frozenset({"merge_mode"}), rendered=frozenset()
    )

    assert [finding.kind for finding in findings] == ["token-without-rendered-input"]
    assert findings[0].subject == "merge_mode"


def test_a_rendered_input_without_a_workflow_token_is_named(rules: ModuleType) -> None:
    findings = rules.equivalence_findings(
        referenced=frozenset(), rendered=frozenset({"default_branch"})
    )

    assert [finding.kind for finding in findings] == ["rendered-input-without-token"]
    assert findings[0].subject == "default_branch"


def test_agreeing_sets_raise_nothing(rules: ModuleType) -> None:
    names = frozenset({"merge_mode"})

    assert rules.equivalence_findings(referenced=names, rendered=names) == []


def test_declaring_an_integration_input_no_position_reads_fails_the_payload(
    check: ModuleType,
    tmp_path: Path,
) -> None:
    payload = _seed_repo(repo_root=tmp_path, check=check)
    run_config = payload / "workflow.toml"
    _ = run_config.write_text(
        run_config.read_text(encoding="utf-8").replace(
            "[run.inputs]", '[run.inputs]\nmerge_mode = "rebase"', 1
        ),
        encoding="utf-8",
    )

    # Prove the edit landed by reading the persisted payload back, then prove
    # the Dispatcher would now render the input the graph never reads.
    assert 'merge_mode = "rebase"' in run_config.read_text(encoding="utf-8")
    assert "merge_mode" in check.rendered_input_names(repo_root=tmp_path)
    findings = check.payload_findings(repo_root=tmp_path)
    assert [finding.kind for finding in findings] == ["rendered-input-without-token"]


# ---------------------------------------------------------------------------
# Criterion 2 — every token sits in a position the pinned engine renders.
# ---------------------------------------------------------------------------


def test_a_token_in_a_duration_attribute_is_reported_with_its_position(
    scan: ModuleType,
    rules: ModuleType,
) -> None:
    occurrences = scan.graph_occurrences(
        text='janitor [ timeout="{{ inputs.sandbox_check_suite }}" ]', venue="graph"
    )

    assert [occurrence.position for occurrence in occurrences] == ["timeout"]
    findings = rules.position_findings(occurrences=occurrences)
    assert [finding.kind for finding in findings] == ["non-rendered-position"]
    assert "timeout" in findings[0].detail


def test_a_token_outside_any_attribute_value_is_reported(
    scan: ModuleType,
    rules: ModuleType,
) -> None:
    occurrences = scan.graph_occurrences(text="// {{ inputs.merge_mode }}", venue="graph")

    assert [occurrence.position for occurrence in occurrences] == [scan.OUTSIDE_ATTRIBUTE_POSITION]
    assert rules.position_findings(occurrences=occurrences)


def test_the_allowlisted_graph_positions_are_admitted(scan: ModuleType, rules: ModuleType) -> None:
    admitted = 'a [ acp.command="{{ inputs.merge_mode }}" ]\nb -> c [ condition="{{ inputs.default_branch }}" ]'

    occurrences = scan.graph_occurrences(text=admitted, venue="graph")

    assert {occurrence.position for occurrence in occurrences} == scan.GRAPH_RENDERED_ATTRIBUTES
    assert rules.position_findings(occurrences=occurrences) == []


def test_only_a_prepare_step_script_renders_in_the_run_config(
    scan: ModuleType,
    rules: ModuleType,
) -> None:
    occurrences = scan.run_config_occurrences(text=_RUN_CONFIG, venue="workflow.toml")

    assert [(occurrence.position, occurrence.rendered) for occurrence in occurrences] == [
        ("run.inputs.sandbox_check_suite", False),
        (scan.PREPARE_STEP_POSITION, True),
        (scan.OUTSIDE_ATTRIBUTE_POSITION, False),
    ]
    assert len(rules.position_findings(occurrences=occurrences)) == 2


def test_a_node_prompt_body_renders_in_whole(scan: ModuleType, rules: ModuleType) -> None:
    occurrences = scan.prompt_occurrences(
        text="Merge with {{ inputs.merge_mode }}.", venue="prompts/pr.md"
    )

    assert [occurrence.position for occurrence in occurrences] == [scan.PROMPT_BODY_POSITION]
    assert rules.position_findings(occurrences=occurrences) == []


def test_an_excluded_input_in_a_non_rendered_position_is_out_of_scope(
    scan: ModuleType,
    rules: ModuleType,
) -> None:
    occurrences = scan.graph_occurrences(
        text='n [ timeout="{{ inputs.review_fix_visit_cap }}" ]', venue="graph"
    )

    # The scan sees it; the equality does not, because it is a policy input.
    assert [occurrence.name for occurrence in occurrences] == ["review_fix_visit_cap"]
    assert rules.position_findings(occurrences=occurrences) == []


def test_a_token_in_a_non_rendered_graph_position_fails_the_payload(
    check: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _seed_repo(repo_root=tmp_path, check=check)
    graph = payload / "workflow.fabro"
    _ = graph.write_text(
        graph.read_text(encoding="utf-8").replace(
            'timeout="1800s"', 'timeout="{{ inputs.sandbox_check_suite }}"', 1
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    assert '"{{ inputs.sandbox_check_suite }}"' in graph.read_text(encoding="utf-8")
    kinds = {finding.kind for finding in check.payload_findings(repo_root=tmp_path)}
    assert kinds == {"non-rendered-position", "token-without-rendered-input"}
    assert check.main() == 1


# ---------------------------------------------------------------------------
# Criterion 3 — the equality is scoped to the integration subset.
# ---------------------------------------------------------------------------


def test_the_three_input_families_are_disjoint_and_cover_what_the_payload_declares(
    rules: ModuleType,
) -> None:
    assert frozenset() == rules.SCHEMA_PROJECTABLE_INPUTS & rules.ADAPTER_INPUT_NAMES
    assert frozenset() == rules.SCHEMA_PROJECTABLE_INPUTS & rules.POLICY_INPUT_NAMES
    assert (
        frozenset({"review_fix_visit_cap", "merge_on_review_cap_outcome"})
        == rules.POLICY_INPUT_NAMES
    )
    assert rules.scoping_findings(declared={}) == []


def test_an_input_belonging_to_no_family_is_named(rules: ModuleType) -> None:
    findings = rules.scoping_findings(declared={"some_new_input": ""})

    assert [finding.kind for finding in findings] == ["unclassified-declared-input"]
    assert findings[0].subject == "some_new_input"


def test_an_input_claimed_by_two_families_is_named(
    rules: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(rules, "POLICY_INPUT_NAMES", frozenset({"merge_mode"}))

    findings = rules.scoping_findings(declared={})

    assert [finding.kind for finding in findings] == ["overlapping-input-families"]
    assert findings[0].subject == "merge_mode"


# ---------------------------------------------------------------------------
# The schema leg — rendered names and projectable fields are one vocabulary.
# ---------------------------------------------------------------------------


def test_the_schema_leg_holds_for_the_shipped_projection(rules: ModuleType) -> None:
    assert rules.schema_findings() == []


def test_a_projected_name_that_is_no_schema_field_is_named(
    rules: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(rules, "CONTRACT_INPUT_NAMES", {"not_a_field": "not_a_field"})

    findings = rules.schema_findings()

    assert [finding.kind for finding in findings] == ["projection-names-no-schema-field"]


def test_a_projected_name_that_renames_its_field_is_named(
    rules: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(rules, "CONTRACT_INPUT_NAMES", {"merge_mode": "merge_strategy"})

    findings = rules.schema_findings()

    assert [finding.kind for finding in findings] == ["projected-name-differs-from-field"]
    assert findings[0].subject == "merge_strategy"


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS — the check refuses to report a clean payload blind.
# ---------------------------------------------------------------------------


def test_positive_control_fixture_carries_the_positions_it_claims_to(
    check: ModuleType,
    scan: ModuleType,
) -> None:
    persisted = check.fixture_path(repo_root=_REPO_ROOT).read_text(encoding="utf-8")

    # Read back off disk and asserted on by CONTENT: the fixture must place
    # real tokens in real non-rendered positions, not merely name them.
    assert 'timeout="{{ inputs.sandbox_check_suite }}"' in persisted
    assert 'stall_timeout="{{ inputs.merge_mode }}"' in persisted
    assert "// A token in a comment: {{ inputs.default_branch }}" in persisted
    assert 'acp.command="{{ inputs.prepare_toolchain_mise }}"' in persisted
    occurrences = scan.graph_occurrences(text=persisted, venue="fixture")
    assert {occurrence.position for occurrence in occurrences if not occurrence.rendered} == {
        "timeout",
        "stall_timeout",
        scan.OUTSIDE_ATTRIBUTE_POSITION,
    }


def test_matcher_control_fails_the_build_when_the_fixture_stops_producing_findings(
    check: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = _seed_repo(repo_root=tmp_path, check=check)
    blinded = check.fixture_path(repo_root=tmp_path)
    _ = blinded.write_text('digraph Blind { start [label="Start"] }\n', encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert "inputs." not in blinded.read_text(encoding="utf-8")
    assert [
        failure for failure in check.control_failures(repo_root=tmp_path) if "matcher" in failure
    ]
    assert check.payload_findings(repo_root=tmp_path) == []
    assert check.main() == 1


def test_matcher_control_fails_the_build_when_the_fixture_is_missing(
    check: ModuleType,
    tmp_path: Path,
) -> None:
    _ = _seed_repo(repo_root=tmp_path, check=check)
    check.fixture_path(repo_root=tmp_path).unlink()

    failures = check.control_failures(repo_root=tmp_path)

    assert not check.fixture_path(repo_root=tmp_path).exists()
    assert [failure for failure in failures if "missing" in failure]


def test_matcher_control_fails_when_a_reported_finding_goes_missing(
    check: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _reports_nothing(*, occurrences: object) -> list[object]:
        assert occurrences is not None
        return []

    monkeypatch.setattr(check, "position_findings", _reports_nothing)

    failures = check.control_failures(repo_root=_REPO_ROOT)

    assert [failure for failure in failures if "disagree" in failure]


def test_discovery_control_fails_when_the_graph_scan_finds_no_adapter_token(
    check: ModuleType,
    tmp_path: Path,
) -> None:
    payload = _seed_repo(repo_root=tmp_path, check=check)
    graph = payload / "workflow.fabro"
    _ = graph.write_text(
        graph.read_text(encoding="utf-8").replace("{{ inputs.implement_adapter }}", "acp", 1),
        encoding="utf-8",
    )

    assert "inputs.implement_adapter" not in graph.read_text(encoding="utf-8")
    failures = check.control_failures(repo_root=tmp_path)
    assert [failure for failure in failures if "node implement" in failure]
    assert not [failure for failure in failures if "matcher" in failure]
