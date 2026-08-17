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
ANCHOR_PROBE = PACKAGE / "wrappers" / "anchor-probe.py"


def _json(path: Path) -> object:
    return json.loads(path.read_text())


def _identity_probe_module() -> ModuleType:
    spec = util.spec_from_file_location("beads_v112_identity_probe", IDENTITY_PROBE)
    assert spec is not None
    assert spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _anchor_probe_module() -> ModuleType:
    assert ANCHOR_PROBE.is_file()
    spec = util.spec_from_file_location("beads_v112_anchor_probe", ANCHOR_PROBE)
    assert spec is not None
    assert spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _assert_three_shape_topology(*, topology: dict[str, object]) -> None:
    assert topology["isolated_server"]["bind"] == "127.0.0.1:13307"
    assert topology["isolated_server"]["forbidden_ports"] == [3307]
    assert topology["shape_codes"] == {
        "dense_policy": "dp",
        "sparse_closed": "sc",
        "rig_wisp": "rw",
    }
    assert topology["role_codes"] == {"source": "s", "migrated": "m", "restored": "r"}

    database_names: set[str] = set()
    client_dirs: set[str] = set()
    sql_users: set[str] = set()
    for shape in ("dense_policy", "sparse_closed", "rig_wisp"):
        shape_row = topology["shapes"][shape]
        assert set(shape_row["databases"]) == {"source", "migrated", "restored"}
        for role, row in shape_row["databases"].items():
            database_names.add(row["database"])
            client_dirs.add(row["client_dir"])
            sql_users.add(row["sql_user"])
            assert "${RUN_ID}" in row["database"]
            assert row["client_dir"] == "${RUN_ROOT}/clients/" + row["database"]
            assert row["sql_user"].startswith("b112_${RUN_ID}_")
            assert row["sql_user"].endswith("_" + topology["role_codes"][role])
    assert len(database_names) == 9
    assert len(client_dirs) == 9
    assert len(sql_users) == 9
    assert topology["golden_schema_database"] == {
        "database": "beads112_${RUN_ID}_golden",
        "client_dir": "${RUN_ROOT}/clients/beads112_${RUN_ID}_golden",
        "sql_user": "b112_${RUN_ID}_g",
        "role": "schema-reference-only",
    }


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


def test_manifest_declares_run_roots_and_isolated_three_shape_topology() -> None:
    manifest_path = PACKAGE / "manifests" / "run-manifest.contract.json"
    assert manifest_path.is_file()
    manifest = _json(manifest_path)
    topology = _json(PACKAGE / "manifests" / "topology.json")
    assert isinstance(manifest, dict)
    assert manifest["run_id"]["name"] == "RUN_ID"
    assert manifest["run_id"]["pattern"] == "^[0-9]{8}t[0-9]{6}z$"
    assert manifest["run_root"]["template"] == "/var/tmp/beads112-rehearsal.${RUN_ID}"
    assert (
        manifest["receipt_root"]["template"]
        == "/home/ubuntu/.local/state/livespec-proof-logs/beads112-${RUN_ID}"
    )
    assert manifest["directory_preconditions"] == {
        "run_root_must_not_exist": True,
        "receipt_root_must_not_exist": True,
        "symlink_resolution_forbidden": True,
        "owner_only_receipt_root": True,
    }

    assert isinstance(topology, dict)
    _assert_three_shape_topology(topology=topology)


def test_anchor_probe_contract_is_single_statement_and_refuses_query_surface(
    monkeypatch,
) -> None:
    module = _anchor_probe_module()
    assert module.ALLOWED_QUERY == "SELECT DATABASE(), CURRENT_USER(), @@hostname, @@port"
    assert module.ALLOWED_QUERY_SHA256 == (
        "9308612c4a6f2f24c7c4c6f4a5a1ffc141cebc67eb0a4dc7794debcf7a6f66d4"
    )
    assert module.statement_count() == 1
    assert module.is_query_allowed(query=module.ALLOWED_QUERY) is True
    for query in [
        module.ALLOWED_QUERY + "; SELECT 1",
        "SELECT DATABASE();",
        "INSERT INTO issues (id) VALUES ('x')",
        "UPDATE issues SET title = 'x'",
        "DELETE FROM issues",
        "CREATE TABLE x (id int)",
        "DROP TABLE x",
        "CALL migrate()",
    ]:
        assert module.is_query_allowed(query=query) is False

    socket_calls: list[tuple[str, int, str, str]] = []

    def fake_connect(
        *,
        host: str,
        port: int,
        user: str,
        password: str,
    ) -> tuple[str, int, str, str]:
        socket_calls.append((host, port, user, password))
        return (host, port, user, password)

    fake_password = "credential-present"
    monkeypatch.setenv("ANCHOR_PROBE_QUERY", "SELECT 1")
    with pytest.raises(SystemExit) as error:
        module.probe_identity(
            host="127.0.0.1",
            port=13307,
            user="b112_20260817t010203z_dp_s",
            password=fake_password,
            database="beads112_20260817t010203z_dense_policy_source",
            connect=fake_connect,
        )
    assert str(error.value) == "query override surfaces are forbidden"
    assert socket_calls == []

    monkeypatch.delenv("ANCHOR_PROBE_QUERY")
    result = module.probe_identity(
        host="127.0.0.1",
        port=13307,
        user="b112_20260817t010203z_dp_s",
        password=fake_password,
        database="beads112_20260817t010203z_dense_policy_source",
        connect=fake_connect,
    )
    assert socket_calls == [
        ("127.0.0.1", 13307, "b112_20260817t010203z_dp_s", fake_password),
    ]
    assert result["statement_count"] == 1
    assert result["read_only_transaction"] is True
    assert result["query_sha256"] == module.ALLOWED_QUERY_SHA256


def test_inventory_queries_cover_all_required_rehearsal_projections() -> None:
    inventory = _json(PACKAGE / "queries" / "inventory.json")
    assert isinstance(inventory, dict)
    assert inventory["capture_command"]["name"] == "capture-inventory"
    assert inventory["capture_command"]["through_wrapper"] == "WITH_CLIENT"
    assert inventory["capture_command"]["canonical_json"] == {
        "encoding": "utf-8",
        "sorted_keys": True,
        "sorted_rows": True,
        "per_artifact_sha256": True,
        "combined_sha256": True,
    }
    projection_names = {projection["artifact"] for projection in inventory["projections"]}
    assert projection_names == {
        "status-type-counts.json",
        "issues.json",
        "dependencies.json",
        "comments.json",
        "labels.json",
        "policy-metadata.json",
        "schema-migrations.json",
        "schema.json",
        "branches.json",
        "table-counts.json",
        "remotes.json",
        "client-anchor.json",
    }
    policy = next(
        projection
        for projection in inventory["projections"]
        if projection["artifact"] == "policy-metadata.json"
    )
    assert policy["label_prefixes"] == [
        "acceptance:",
        "admission:",
        "intake:",
        "origin:",
        "factory-safety:",
        "blocked-reason:",
    ]


def test_command_plan_instance_covers_attended_gates_without_live_execution() -> None:
    plan_path = PACKAGE / "command-plans" / "beads112-rehearsal.command-plan.json"
    assert plan_path.is_file()
    plan = _json(plan_path)
    schema = _json(PACKAGE / "schemas" / "rehearsal-command-plan.schema.json")
    assert isinstance(plan, dict)
    assert isinstance(schema, dict)
    assert plan["schema"] == schema["$id"]
    assert plan["run_variables"] == ["RUN_ID", "RUN_ROOT", "RECEIPT_ROOT"]
    assert plan["execution_boundary"]["factory_safe_preparation_only"] is True
    assert plan["execution_boundary"]["live_execution_allowed_by_this_package"] is False
    assert plan["execution_boundary"]["forbidden_fragments"] == [
        "/usr/local/bin/bd-real",
        "/var/lib/doltdb",
        "/var/backups",
        "127.0.0.1:3307",
        "fabro server",
        "systemctl",
        "docker ",
    ]
    stage_names = [stage["name"] for stage in plan["stages"]]
    assert stage_names == [
        "manifest-preflight",
        "artifact-fetch-and-v105-build",
        "topology-preflight",
        "create-client-pointers",
        "source-fixture-production",
        "capture-v49-baseline",
        "single-use-backup",
        "clean-target-restore-to-migrated",
        "target-side-remote-materialization",
        "designated-migrator-record",
        "migration-gate-and-single-retry",
        "capture-v53-and-golden-schema",
        "round-trip-commands",
        "restore-v49-baseline-to-restored",
        "immutable-receipts",
        "stop-boundary",
        "cleanup-after-acceptance",
    ]
    assert plan["stages"][12]["commands"] == [
        "create rehearsal parent",
        "create rehearsal child",
        "update child active bug",
        "dep add child parent",
        "comments add child",
        "close child",
        "list parent child",
        "show child with comments",
    ]
    assert plan["receipt_contracts"] == [
        "manifest",
        "topology",
        "anchor",
        "inventory",
        "backup",
        "migration_gate",
        "designated_migrator",
        "round_trip_delta",
        "restore_baseline_comparison",
        "cleanup",
        "SHA256SUMS",
    ]
