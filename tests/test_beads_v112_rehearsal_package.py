from __future__ import annotations

import json
import runpy
import sys
from importlib import util
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "plan" / "beads-v1-1-2-upgrade" / "rehearsal-package"
IDENTITY_PROBE = PACKAGE / "wrappers" / "identity-probe.py"


def _json(path: Path) -> object:
    return json.loads(path.read_text())


def _identity_probe_module() -> ModuleType:
    spec = util.spec_from_file_location("beads_v112_identity_probe", IDENTITY_PROBE)
    assert spec is not None
    assert spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_rehearsal_package_declares_only_the_allowed_production_surface() -> None:
    topology = _json(PACKAGE / "manifests" / "topology.json")
    assert isinstance(topology, dict)
    assert topology["synthetic_rehearsal_only"] is True
    assert topology["production_writes_allowed"] is False

    sources = topology["readonly_shape_sources"]
    assert [source["repo_root"] for source in sources] == [
        "/data/projects/livespec",
        "/data/projects/livespec-orchestrator-beads-fabro",
        "/data/projects/livespec-driver-codex",
    ]
    assert {source["bd_path"] for source in sources} == {"/usr/local/bin/bd"}
    assert all(source["wrapper"].endswith("with-livespec-env.sh") for source in sources)


def test_rehearsal_package_records_reviewed_artifact_and_build_provenance() -> None:
    provenance = _json(PACKAGE / "manifests" / "provenance.json")
    assert isinstance(provenance, dict)
    assert provenance["beads_v112"]["tarball_sha256"] == (
        "a72d71ed374955dc9f83a0f90b54bd7b6a0016709dd1676ae2e368651ed401c2"
    )
    assert provenance["beads_v112"]["extracted_bd_sha256"] == (
        "6d767629e90560506d0ea3de9823aef48386414f5425d8853e2ae3312cad9a82"
    )
    assert provenance["beads_v105_fixture_producer"]["tag_peel_commit"] == (
        "6a3f515ced18406c189c55fff789a4925bfaa35c"
    )
    assert provenance["beads_v105_fixture_producer"]["required_toolchain"] == "go1.26.2"


def test_deterministic_fixture_inventory_covers_observed_and_synthetic_shapes() -> None:
    fixtures = _json(PACKAGE / "fixtures" / "deterministic-fixtures.json")
    assert isinstance(fixtures, dict)
    ids = {fixture["id"] for fixture in fixtures["fixtures"]}
    assert ids == {"o4-root", "o4-ready", "o4-blocked", "o4-rig-wisp"}
    assert fixtures["expected_identity"] == {
        "issue_count": 4,
        "dependency_edges": [{"from": "o4-blocked", "to": "o4-ready", "type": "blocks"}],
        "parent_edges": [{"parent": "o4-root", "child": "o4-ready"}],
        "comment_count": 1,
        "metadata_issue_count": 4,
        "distinct_label_count": 6,
    }


def test_receipt_schemas_are_machine_readable_and_strict() -> None:
    schema_paths = sorted((PACKAGE / "schemas").glob("*.schema.json"))
    assert [path.name for path in schema_paths] == [
        "artifact-fetch-receipt.schema.json",
        "fixture-producer-build-receipt.schema.json",
        "identity-probe-receipt.schema.json",
        "rehearsal-command-plan.schema.json",
        "shape-survey-receipt.schema.json",
    ]
    for path in schema_paths:
        schema = _json(path)
        assert isinstance(schema, dict)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["additionalProperties"] is False


def test_wrappers_do_not_contain_forbidden_host_or_production_mutations() -> None:
    forbidden_fragments = [
        "systemctl",
        "fabro server",
        "docker build",
        "docker run",
        "bd init",
        "/usr/local/bin/bd-real",
        "DOLT_BACKUP",
        "DROP DATABASE",
        "CREATE DATABASE",
    ]
    for path in sorted(
        candidate for candidate in (PACKAGE / "wrappers").glob("*") if candidate.is_file()
    ):
        text = path.read_text()
        for fragment in forbidden_fragments:
            assert fragment not in text


def test_identity_probe_emits_stable_inventory_receipt(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    module = _identity_probe_module()
    input_path = tmp_path / "issues.json"
    input_path.write_text(
        json.dumps(
            [
                {
                    "id": "o4-a",
                    "dependencies": [{"target": "o4-b"}],
                    "comment_count": 2,
                    "labels": ["origin:beads-v1-1-2-upgrade", "ready"],
                    "metadata": {"rank": "001"},
                },
                {
                    "id": "o4-b",
                    "comment_count": 0,
                    "labels": ["origin:beads-v1-1-2-upgrade"],
                    "metadata": {},
                },
            ],
        ),
    )
    monkeypatch.setattr(sys, "argv", ["identity-probe.py", str(input_path)])
    assert module.main() == 0
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["schema"] == "livespec.beads_v112_rehearsal.identity_probe_receipt.v1"
    assert receipt["issue_count"] == 2
    assert receipt["dependency_count"] == 1
    assert receipt["comment_count"] == 2
    assert receipt["metadata_issue_count"] == 1
    assert receipt["distinct_label_count"] == 2


def test_identity_probe_main_guard_runs_in_process(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    input_path = tmp_path / "issues.json"
    input_path.write_text("[]")
    monkeypatch.setattr(sys, "argv", ["identity-probe.py", str(input_path)])
    with pytest.raises(SystemExit) as error:
        runpy.run_path(str(IDENTITY_PROBE), run_name="__main__")
    assert error.value.code == 0
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["issue_count"] == 0


def test_identity_probe_rejects_invalid_inputs(tmp_path: Path, monkeypatch) -> None:
    module = _identity_probe_module()
    input_path = tmp_path / "issues.json"

    for payload, expected in [
        ({}, "expected top-level JSON array"),
        ([1], "expected every issue entry to be a JSON object"),
        ([{"dependencies": "bad"}], "expected dependencies to be a JSON array when present"),
        ([{"labels": "bad"}], "expected labels to be a JSON array when present"),
        ([{"labels": [1]}], "expected every label to be a string"),
    ]:
        input_path.write_text(json.dumps(payload))
        monkeypatch.setattr(sys, "argv", ["identity-probe.py", str(input_path)])
        with pytest.raises(SystemExit) as error:
            module.main()
        assert str(error.value) == expected


def test_identity_probe_requires_input_path(monkeypatch) -> None:
    module = _identity_probe_module()
    monkeypatch.setattr(sys, "argv", ["identity-probe.py"])
    with pytest.raises(SystemExit) as error:
        module.main()
    assert str(error.value) == "usage: identity-probe.py ISSUES_JSON"
