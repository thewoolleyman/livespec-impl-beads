"""Tests for the integration-input seam-equivalence guard.

The guard reports an ABSENCE, so a broken scanner would print exactly what a
conformant payload prints. These tests therefore carry the controls the
work-item makes non-optional plus a NEGATIVE CONTROL per direction of the
equality: every assertion below is made against a payload seeded on disk and
read back through the check's own scan path, never against the return value of
a write call. Since C5-payload the committed payload references every
integration input, so the equality is also exercised for real.

THE VARIANT CASES USE A FIXTURE REGISTRY, not the repository's own
`.livespec.jsonc`, which registers no variant. Each seeds a throwaway root
carrying a real `dispatcher.workflows` table plus real copies of the bundle,
and the defect is introduced in ONE registered copy: the assertion that matters
is that the finding names THAT directory while the bundle beside it still
passes, which no single-payload gate could produce.
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
_PAYLOADS_PATH = _REPO_ROOT / "dev-tooling" / "checks" / "_checked_workflow_payloads.py"
_BUNDLE_WHERE = ".claude-plugin/.fabro/workflows/implement-work-item"

# The one anchor the registry is spliced in after. Asserted to occur exactly
# once before every splice, so a config reshape breaks the fixture loudly
# instead of silently seeding a repo with no registry at all.
_DISPATCHER_OPENER = '"dispatcher": {'

# A run config carrying one token per position class: a prepare-step script
# (rendered), an input default (not rendered), and a comment (no attribute at
# all). Written here rather than derived from the payload so the position rules
# are asserted in isolation from whatever the committed payload carries.
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


@pytest.fixture(name="payloads")
def _payloads_fixture(check: ModuleType) -> ModuleType:
    assert check is not None
    return sys.modules["_checked_workflow_payloads"]


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


def _register_variants(*, repo_root: Path, variants: dict[str, str]) -> None:
    """Declare a `dispatcher.workflows` table in the seeded root's config."""
    config = repo_root / ".livespec.jsonc"
    text = config.read_text(encoding="utf-8")
    assert text.count(_DISPATCHER_OPENER) == 1
    entries = ", ".join(f'"{name}": "{declared}"' for name, declared in variants.items())
    _ = config.write_text(
        text.replace(_DISPATCHER_OPENER, f'{_DISPATCHER_OPENER} "workflows": {{{entries}}},', 1),
        encoding="utf-8",
    )


def _copy_bundle(*, repo_root: Path, declared: str) -> Path:
    """A registered variant directory holding a real, complete copy of the bundle."""
    target = repo_root / declared
    _ = shutil.copytree(_REPO_ROOT.joinpath(*_BUNDLE_WHERE.split("/")), target)
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


def test_scan_of_the_real_payload_returns_the_tokens_that_are_there(
    check: ModuleType,
    payloads: ModuleType,
) -> None:
    occurrences = check.payload_occurrences(payload=payloads.bundle_payload(repo_root=_REPO_ROOT))

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
    prompt = payload / "prompts" / "pr.md"
    # `merge_mode` stays DECLARED in `[run.inputs]`; its one reading position
    # (the publish prompt's merge-method flag) is put back to a literal.
    _ = prompt.write_text(
        prompt.read_text(encoding="utf-8").replace("--{{ inputs.merge_mode }}", "--rebase", 1),
        encoding="utf-8",
    )

    # Prove the edit landed by reading the persisted payload back, then prove
    # the Dispatcher would still render the input no position reads any more.
    assert "inputs.merge_mode" not in prompt.read_text(encoding="utf-8")
    assert "merge_mode" in check.rendered_input_names(repo_root=tmp_path)
    findings = check.payload_findings(repo_root=tmp_path)
    assert [finding.kind for finding in findings] == ["rendered-input-without-token"]
    assert findings[0].subject == "merge_mode"


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
    admitted = (
        'a [ acp.command="{{ inputs.merge_mode }}" ]\n'
        'b -> c [ condition="{{ inputs.default_branch }}" ]\n'
        'd [ shape=parallelogram script="{{ inputs.sandbox_check_suite }}" ]'
    )

    occurrences = scan.graph_occurrences(text=admitted, venue="graph")

    assert {occurrence.position for occurrence in occurrences} == scan.GRAPH_RENDERED_ATTRIBUTES
    assert rules.position_findings(occurrences=occurrences) == []


def test_a_script_node_is_a_rendered_position_and_a_timeout_beside_it_is_not(
    scan: ModuleType,
    rules: ModuleType,
) -> None:
    """Node `script` renders (maintainer-confirmed 2026-08-31 for pinned fabro 0.254.0).

    The payload's janitor gate and dead-implementer breaker template their
    check suite and default branch into a parallelogram node's `script`, so the
    scan must admit that attribute -- and must keep refusing the typed `timeout`
    on the SAME node, because widening one attribute is evidence about that
    attribute alone.
    """
    graph = (
        "janitor [\n"
        "    shape=parallelogram\n"
        '    timeout="{{ inputs.merge_mode }}"\n'
        '    script="{{ inputs.sandbox_check_suite }}"\n'
        "]"
    )

    occurrences = scan.graph_occurrences(text=graph, venue="graph")

    assert "script" in scan.GRAPH_RENDERED_ATTRIBUTES
    assert [(occurrence.position, occurrence.rendered) for occurrence in occurrences] == [
        ("timeout", False),
        ("script", True),
    ]
    assert [finding.subject for finding in rules.position_findings(occurrences=occurrences)] == [
        "merge_mode"
    ]


def test_the_committed_payload_references_every_integration_input(
    check: ModuleType,
    scan: ModuleType,
    rules: ModuleType,
    payloads: ModuleType,
) -> None:
    """The equality is no longer vacuous: every projectable field has a real token."""
    occurrences = check.payload_occurrences(payload=payloads.bundle_payload(repo_root=_REPO_ROOT))

    referenced = rules.referenced_integration_inputs(occurrences=occurrences)
    assert referenced == rules.SCHEMA_PROJECTABLE_INPUTS
    assert referenced == check.rendered_input_names(repo_root=_REPO_ROOT)
    positions = {occurrence.position for occurrence in occurrences if occurrence.name in referenced}
    assert positions >= {"script", scan.PREPARE_STEP_POSITION, scan.PROMPT_BODY_POSITION}


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

    assert 'timeout="{{ inputs.sandbox_check_suite }}"' in graph.read_text(encoding="utf-8")
    # The input is declared and rendered (the janitor script still reads it),
    # so the ONLY disagreement is the typed attribute the engine will not expand.
    kinds = {finding.kind for finding in check.payload_findings(repo_root=tmp_path)}
    assert kinds == {"non-rendered-position"}
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


# ---------------------------------------------------------------------------
# Every REGISTERED variant is checked, and every finding names its directory.
# ---------------------------------------------------------------------------


def test_the_shared_payload_enumeration_module_is_installed() -> None:
    """One module answers "which directories does a payload gate read" for both gates."""
    assert _PAYLOADS_PATH.is_file()


def test_a_repository_declaring_no_registry_is_checked_as_the_bundle_alone(
    check: ModuleType,
    payloads: ModuleType,
    tmp_path: Path,
) -> None:
    _ = _seed_repo(repo_root=tmp_path, check=check)

    checked = payloads.checked_payloads(repo_root=tmp_path)

    assert [payload.where for payload in checked] == [_BUNDLE_WHERE]
    # And the same holds for THIS repository, which registers no variant: the
    # deferral of a real second variant is a fact about the config, not a gap
    # in the gate.
    assert [payload.where for payload in payloads.checked_payloads(repo_root=_REPO_ROOT)] == [
        _BUNDLE_WHERE
    ]


def test_every_directory_the_registry_names_is_checked_beside_the_bundle(
    check: ModuleType,
    payloads: ModuleType,
    tmp_path: Path,
) -> None:
    _ = _seed_repo(repo_root=tmp_path, check=check)
    _register_variants(
        repo_root=tmp_path, variants={"beta": "variants/beta", "alpha": "variants/alpha"}
    )

    checked = payloads.checked_payloads(repo_root=tmp_path)

    # Read back through the registry's OWN parser off the config on disk, so a
    # table this fixture failed to splice in could not read as "no variants".
    assert '"workflows"' in (tmp_path / ".livespec.jsonc").read_text(encoding="utf-8")
    assert [payload.where for payload in checked] == [
        _BUNDLE_WHERE,
        "variants/alpha",
        "variants/beta",
    ]
    assert [payload.directory for payload in checked[1:]] == [
        tmp_path / "variants/alpha",
        tmp_path / "variants/beta",
    ]


def test_a_registered_variant_with_an_unrendered_token_fails_while_the_bundle_passes(
    check: ModuleType,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = _seed_repo(repo_root=tmp_path, check=check)
    _register_variants(
        repo_root=tmp_path,
        variants={"conformant": "variants/conformant", "unrendered": "variants/unrendered"},
    )
    _ = _copy_bundle(repo_root=tmp_path, declared="variants/conformant")
    graph = _copy_bundle(repo_root=tmp_path, declared="variants/unrendered") / "workflow.fabro"
    _ = graph.write_text(
        graph.read_text(encoding="utf-8").replace(
            'timeout="1800s"', 'timeout="{{ inputs.sandbox_check_suite }}"', 1
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    # Prove the defect landed in the VARIANT and nowhere else before reading
    # the verdict: the bundle and the conformant variant are the controls.
    persisted = graph.read_text(encoding="utf-8")
    assert 'timeout="{{ inputs.sandbox_check_suite }}"' in persisted
    assert 'timeout="{{ inputs.sandbox_check_suite }}"' not in (
        bundle / "workflow.fabro"
    ).read_text(encoding="utf-8")
    findings = check.payload_findings(repo_root=tmp_path)
    assert [finding.kind for finding in findings] == ["non-rendered-position"]
    assert findings[0].detail.startswith("variants/unrendered: ")
    assert check.control_failures(repo_root=tmp_path) == []
    assert check.main() == 1


def test_a_registered_variant_referencing_fewer_tokens_is_a_finding_not_a_pass(
    check: ModuleType,
    tmp_path: Path,
) -> None:
    """The rider's own example: a variant that drops `default_branch` must fail.

    The comparand is the ONE Dispatcher-rendered set, derived from the bundle.
    Were it re-derived per variant, this variant would shrink its own comparand
    and the equality would hold vacuously -- a silent pass on the exact defect
    the per-variant set identity exists to catch.
    """
    _ = _seed_repo(repo_root=tmp_path, check=check)
    _register_variants(repo_root=tmp_path, variants={"narrowed": "variants/narrowed"})
    variant = _copy_bundle(repo_root=tmp_path, declared="variants/narrowed")
    for path in sorted(variant.rglob("*")):
        if path.is_file():
            _ = path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "{{ inputs.default_branch }}", "the default branch"
                ),
                encoding="utf-8",
            )

    assert not [
        path for path in variant.rglob("*.md") if "inputs.default_branch" in path.read_text("utf-8")
    ]
    assert "default_branch" in check.rendered_input_names(repo_root=tmp_path)
    findings = check.payload_findings(repo_root=tmp_path)
    assert [(finding.kind, finding.subject) for finding in findings] == [
        ("rendered-input-without-token", "default_branch")
    ]
    assert findings[0].detail.startswith("variants/narrowed: ")


def test_a_registered_variant_that_scans_to_nothing_fails_rather_than_reporting_clean(
    check: ModuleType,
    tmp_path: Path,
) -> None:
    _ = _seed_repo(repo_root=tmp_path, check=check)
    _register_variants(repo_root=tmp_path, variants={"absent": "variants/absent"})

    failures = check.control_failures(repo_root=tmp_path)

    assert not (tmp_path / "variants" / "absent").exists()
    # The controls are PER DIRECTORY: the missing variant fails both of its own
    # while the bundle standing beside it reports neither.
    assert [failure for failure in failures if "completeness control: variants/absent" in failure]
    assert [
        failure for failure in failures if "variants/absent: the graph scan found no" in failure
    ]
    assert not [failure for failure in failures if f"{_BUNDLE_WHERE}:" in failure]
    # And it is loud in the findings too, every one of them naming the absent
    # directory: the equality sees a payload referencing nothing at all.
    findings = check.payload_findings(repo_root=tmp_path)
    assert {finding.kind for finding in findings} == {"rendered-input-without-token"}
    assert all(finding.detail.startswith("variants/absent: ") for finding in findings)


def test_an_incomplete_registered_variant_is_a_finding_naming_that_directory(
    check: ModuleType,
    tmp_path: Path,
) -> None:
    _ = _seed_repo(repo_root=tmp_path, check=check)
    _register_variants(repo_root=tmp_path, variants={"partial": "variants/partial"})
    variant = _copy_bundle(repo_root=tmp_path, declared="variants/partial")
    (variant / "workflow.toml").unlink()

    failures = check.control_failures(repo_root=tmp_path)

    assert not (variant / "workflow.toml").exists()
    assert (variant / "workflow.fabro").is_file()
    named = [failure for failure in failures if "completeness control: variants/partial" in failure]
    assert [failure for failure in named if "workflow.toml" in failure]
    assert not [failure for failure in named if "workflow.fabro" in failure]
