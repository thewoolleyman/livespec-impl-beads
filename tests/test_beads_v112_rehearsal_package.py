from __future__ import annotations

import hashlib
import json
import os
import runpy
import shlex
import stat
import subprocess
import sys
from importlib import util
from pathlib import Path
from types import ModuleType

import pytest
from jsonschema import ValidationError
from jsonschema.validators import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "plan" / "archive" / "beads-v1-1-2-upgrade" / "rehearsal-package"
IDENTITY_PROBE = PACKAGE / "wrappers" / "identity-probe.py"
ANCHOR_PROBE = PACKAGE / "wrappers" / "anchor-probe.py"


def _json(path: Path) -> object:
    return json.loads(path.read_text())


def _schema_accepts(*, schema: dict[str, object], instance: dict[str, object]) -> bool:
    try:
        Draft202012Validator(schema).validate(instance)
    except ValidationError:
        return False
    return True


def _run(
    argv: list[str],
    *,
    env: dict[str, str],
    cwd: Path | None = None,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=cwd,
        env=env,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )


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


def _write_executable(path: Path, text: str) -> None:
    path.write_text(text)
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def _client_fixture(tmp_path: Path) -> dict[str, object]:
    run_id = "20260817t010203z"
    run_root = tmp_path / f"beads112-rehearsal.{run_id}"
    receipt_root = tmp_path / f"proof-logs/beads112-{run_id}"
    client_dir = run_root / "clients" / f"beads112_{run_id}_dense_policy_source"
    beads_dir = client_dir / ".beads"
    beads_dir.mkdir(parents=True)
    pointer = (
        "dolt.auto-start: false\n"
        "dolt.mode: server\n"
        "dolt.server-host: 127.0.0.1\n"
        "dolt.server-port: 13307\n"
        f"dolt.server-user: b112_{run_id}_dp_s\n"
        f"dolt.database: beads112_{run_id}_dense_policy_source\n"
        "dolt.prefix: b112\n"
    )
    pointer_path = beads_dir / "config.yaml"
    pointer_path.write_text(pointer)
    receipt_root.mkdir(parents=True)
    probe = tmp_path / "anchor-probe"
    _write_executable(
        probe,
        "#!/bin/sh\n"
        'printf \'%s\\n\' \'{"database":"beads112_20260817t010203z_dense_policy_source",'
        '"current_user":"b112_20260817t010203z_dp_s@%",'
        '"hostname":"isolated-dolt",'
        '"port":13307,'
        '"tcp_peer":"127.0.0.1:13307",'
        '"server_fingerprint":"sha256:isolated"}\'\n',
    )
    dependency_lock = tmp_path / "dependencies.lock"
    dependency_lock.write_text('{"dependencies":[]}\n')
    with_client = PACKAGE / "wrappers" / "with-client.sh"
    manifest = {
        "run_id": run_id,
        "run_root": str(run_root),
        "receipt_root": str(receipt_root),
        "anchor_probe": str(probe),
        "anchor_probe_sha256": hashlib.sha256(probe.read_bytes()).hexdigest(),
        "dependency_lock": str(dependency_lock),
        "dependency_lock_sha256": hashlib.sha256(dependency_lock.read_bytes()).hexdigest(),
        "with_client": str(with_client),
        "with_client_sha256": hashlib.sha256(with_client.read_bytes()).hexdigest(),
        "expected_server_fingerprint": "sha256:isolated",
        "clients": [
            {
                "client_key": f"dense_policy/source/{run_id}",
                "database": f"beads112_{run_id}_dense_policy_source",
                "sql_user": f"b112_{run_id}_dp_s",
                "client_dir": str(client_dir),
                "pointer_sha256": hashlib.sha256(pointer.encode()).hexdigest(),
                "metadata": {"state": "absent", "sha256": None},
            }
        ],
    }
    manifest_path = tmp_path / "topology.instance.json"
    manifest_path.write_text(json.dumps(manifest, sort_keys=True))
    credential_helper = tmp_path / "credential-helper"
    _write_executable(
        credential_helper,
        "#!/bin/sh\n"
        'test "$1" = dense_policy/source/20260817t010203z\n'
        'test "$2" = b112_20260817t010203z_dp_s\n'
        "printf '%s\\n' isolated-secret\n",
    )
    return {
        "run_id": run_id,
        "run_root": run_root,
        "receipt_root": receipt_root,
        "client_key": f"dense_policy/source/{run_id}",
        "client_dir": client_dir,
        "manifest": manifest_path,
        "credential_helper": credential_helper,
    }


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
    assert (
        provenance["anchor_probe"]["implementation_sha256"]
        == hashlib.sha256(
            (PACKAGE / provenance["anchor_probe"]["implementation"]).read_bytes()
        ).hexdigest()
    )
    assert (
        provenance["anchor_probe"]["dependency_lock_sha256"]
        == hashlib.sha256(
            (PACKAGE / provenance["anchor_probe"]["dependency_lock"]).read_bytes()
        ).hexdigest()
    )
    assert provenance["anchor_probe"]["dependencies"] == [
        {
            "name": "anchor_driver.py",
            "version": "reviewed-package-local",
            "source": "reviewed package root",
            "sha256": hashlib.sha256(
                (PACKAGE / "wrappers" / "anchor_driver.py").read_bytes(),
            ).hexdigest(),
        }
    ]
    for key, relative in {
        "with_client_sha256": "wrappers/with-client.sh",
        "assert_client_anchor_sha256": "wrappers/assert-client-anchor.sh",
        "capture_inventory_sha256": "wrappers/capture-inventory.sh",
    }.items():
        assert (
            provenance["wrappers"][key]
            == hashlib.sha256((PACKAGE / relative).read_bytes()).hexdigest()
        )


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
        "anchor-receipt.schema.json",
        "artifact-fetch-receipt.schema.json",
        "backup-identity-receipt.schema.json",
        "backup-namespace-preflight-receipt.schema.json",
        "cleanup-receipt.schema.json",
        "designated-migrator-receipt.schema.json",
        "fixture-producer-build-receipt.schema.json",
        "golden-schema-comparison-receipt.schema.json",
        "identity-probe-receipt.schema.json",
        "inventory-receipt.schema.json",
        "migration-gate-receipt.schema.json",
        "production-unchanged-receipt.schema.json",
        "rehearsal-command-plan.schema.json",
        "restored-baseline-comparison-receipt.schema.json",
        "round-trip-delta-receipt.schema.json",
        "shape-survey-receipt.schema.json",
        "stop-boundary-receipt.schema.json",
        "top-level-sha256sums.schema.json",
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


def test_anchor_probe_has_no_query_override_or_fake_connector_surface(monkeypatch) -> None:
    module = _anchor_probe_module()
    probe_secret = "credential-present"
    assert module.ALLOWED_QUERY == "SELECT DATABASE(), CURRENT_USER(), @@hostname, @@port"
    assert hashlib.sha256(module.ALLOWED_QUERY.encode()).hexdigest() == module.ALLOWED_QUERY_SHA256
    assert module.statement_count() == 1
    assert not hasattr(module, "Callable")
    assert not hasattr(module, "connect")
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

    monkeypatch.setenv("ANCHOR_PROBE_QUERY", "SELECT 1")
    with pytest.raises(SystemExit) as error:
        module.probe_identity(
            host="127.0.0.1",
            port=13307,
            user="b112_20260817t010203z_dp_s",
            password=probe_secret,
            database="beads112_20260817t010203z_dense_policy_source",
        )
    assert str(error.value) == "query override surfaces are forbidden"


def test_anchor_probe_source_has_one_literal_query_and_one_execute_site() -> None:
    text = ANCHOR_PROBE.read_text()
    literal = '"SELECT DATABASE(), CURRENT_USER(), @@hostname, @@port"'
    assert text.count(literal) == 1
    assert text.count(".execute(") == 1
    assert "Callable" not in text
    assert "query_for_test" not in text
    assert "connect:" not in text
    assert "stdin" not in text.lower()
    assert "BEADS112_EXPECTED_HOSTNAME" not in text
    assert "BEADS112_SERVER_FINGERPRINT" not in text


def test_anchor_probe_refusals_happen_before_driver_socket_open(monkeypatch) -> None:
    module = _anchor_probe_module()
    probe_secret = "credential-present"
    driver = module.load_reviewed_driver()
    monkeypatch.setattr(driver, "SOCKET_OPEN_COUNT", 0)
    monkeypatch.setenv("ANCHOR_PROBE_SQL", "SELECT 1")
    with pytest.raises(SystemExit):
        module.probe_identity(
            host="127.0.0.1",
            port=13307,
            user="b112_20260817t010203z_dp_s",
            password=probe_secret,
            database="beads112_20260817t010203z_dense_policy_source",
        )
    assert driver.SOCKET_OPEN_COUNT == 0


def test_anchor_probe_cli_success_and_refuses_query_flags(monkeypatch, capfd) -> None:
    module = _anchor_probe_module()
    argv = [
        "--host",
        "127.0.0.1",
        "--port",
        "13307",
        "--user",
        "b112_20260817t010203z_dp_s",
        "--database",
        "beads112_20260817t010203z_dense_policy_source",
    ]
    monkeypatch.setenv("BEADS_DOLT_PASSWORD", "credential-present")
    assert module.main(argv=argv) == 0
    receipt = json.loads(capfd.readouterr().out)
    assert receipt["hostname"] == "isolated-dolt"
    assert receipt["server_fingerprint"] == "sha256:isolated"
    assert receipt["rolled_back"] is True
    assert receipt["closed"] is True

    with pytest.raises(SystemExit) as error:
        module.main(argv=["--query", module.ALLOWED_QUERY, *argv])
    assert str(error.value) == module.ERROR_QUERY_OVERRIDE


def test_with_client_uses_exact_isolated_secret_and_blocks_inherited_state(tmp_path: Path) -> None:
    fixture = _client_fixture(tmp_path)
    capture_env = tmp_path / "child-env.json"
    command = tmp_path / "child-command"
    _write_executable(
        command,
        "#!/bin/sh\n"
        "python3 - <<'PY'\n"
        "import json, os\n"
        "names = sorted(name for name in os.environ if 'BEADS' in name or 'DOLT' in name)\n"
        "payload = {'names': names, 'password': os.environ.get('BEADS_DOLT_PASSWORD')}\n"
        f"open({str(capture_env)!r}, 'w').write(json.dumps(payload, sort_keys=True))\n"
        "PY\n",
    )
    env = {
        "PATH": os.environ["PATH"],
        "RUN_ID": str(fixture["run_id"]),
        "RUN_ROOT": str(fixture["run_root"]),
        "RECEIPT_ROOT": str(fixture["receipt_root"]),
        "TOPOLOGY_MANIFEST": str(fixture["manifest"]),
        "BEADS112_CREDENTIAL_HELPER": str(fixture["credential_helper"]),
        "ASSERT_CLIENT_ANCHOR": str(PACKAGE / "wrappers" / "assert-client-anchor.sh"),
        "BEADS112_COMMAND_CATEGORY": "inventory",
    }
    result = _run(
        [str(PACKAGE / "wrappers" / "with-client.sh"), str(fixture["client_key"]), str(command)],
        env=env,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(capture_env.read_text()) == {
        "names": ["BEADS_DOLT_PASSWORD"],
        "password": "isolated-secret",
    }
    assert sorted(Path(fixture["receipt_root"]).glob("anchor-*.json"))

    inherited = dict(env)
    inherited["BEADS_DOLT_PASSWORD"] = "production-secret"
    blocked = _run(
        [str(PACKAGE / "wrappers" / "with-client.sh"), str(fixture["client_key"]), str(command)],
        env=inherited,
    )
    assert blocked.returncode == 70
    assert "parent environment already carries BEADS_DOLT_PASSWORD" in blocked.stderr

    no_helper = dict(env)
    no_helper.pop("BEADS112_CREDENTIAL_HELPER")
    no_helper["BEADS112_ISOLATED_CREDENTIAL_LENGTH"] = "15"
    blocked = _run(
        [str(PACKAGE / "wrappers" / "with-client.sh"), str(fixture["client_key"]), str(command)],
        env=no_helper,
    )
    assert blocked.returncode == 70
    assert "credential helper required" in blocked.stderr


def test_with_client_refuses_credential_source_user_mismatch(tmp_path: Path) -> None:
    fixture = _client_fixture(tmp_path)
    helper = tmp_path / "credential-helper"
    _write_executable(
        helper,
        "#!/bin/sh\n"
        'test "$2" = b112_20260817t010203z_wrong\n'
        "printf '%s\\n' isolated-secret\n",
    )
    env = {
        "PATH": os.environ["PATH"],
        "RUN_ID": str(fixture["run_id"]),
        "RUN_ROOT": str(fixture["run_root"]),
        "RECEIPT_ROOT": str(fixture["receipt_root"]),
        "TOPOLOGY_MANIFEST": str(fixture["manifest"]),
        "BEADS112_CREDENTIAL_HELPER": str(helper),
        "ASSERT_CLIENT_ANCHOR": str(PACKAGE / "wrappers" / "assert-client-anchor.sh"),
    }
    result = _run(
        [
            str(PACKAGE / "wrappers" / "with-client.sh"),
            str(fixture["client_key"]),
            "/bin/sh",
            "-c",
            "exit 0",
        ],
        env=env,
    )
    assert result.returncode == 70
    assert "credential-source/user mismatch" in result.stderr


def test_assert_client_anchor_writes_canonical_receipt_and_blocks_pointer_drift(
    tmp_path: Path,
) -> None:
    fixture = _client_fixture(tmp_path)
    receipt_path = Path(fixture["receipt_root"]) / "anchor.json"
    env = {
        "PATH": os.environ["PATH"],
        "RUN_ID": str(fixture["run_id"]),
        "RUN_ROOT": str(fixture["run_root"]),
        "RECEIPT_ROOT": str(fixture["receipt_root"]),
        "TOPOLOGY_MANIFEST": str(fixture["manifest"]),
        "BEADS_DOLT_PASSWORD": "isolated-secret",
        "BEADS112_CREDENTIAL_BYTE_COUNT": "16",
        "BEADS112_COMMAND_CATEGORY": "inventory",
        "BEADS112_COMMAND_SEQUENCE": "7",
    }
    result = _run(
        [
            str(PACKAGE / "wrappers" / "assert-client-anchor.sh"),
            str(fixture["client_key"]),
            str(receipt_path),
        ],
        env=env,
    )
    assert result.returncode == 0, result.stderr
    receipt = json.loads(receipt_path.read_text())
    assert receipt["schema"] == "livespec.beads_v112_rehearsal.anchor_receipt.v1"
    assert receipt["pointer"]["key_count"] == 7
    assert receipt["metadata"]["state"] == "absent"
    assert receipt["identity"]["database"] == "beads112_20260817t010203z_dense_policy_source"
    assert receipt["identity"]["tcp_peer"] == "127.0.0.1:13307"
    assert receipt["following_command"] == {"category": "inventory", "sequence": 7}
    assert "isolated-secret" not in receipt_path.read_text()

    pointer = Path(fixture["client_dir"]) / ".beads" / "config.yaml"
    pointer.write_text(pointer.read_text() + "dolt.socket: /tmp/prod.sock\n")
    drift = _run(
        [
            str(PACKAGE / "wrappers" / "assert-client-anchor.sh"),
            str(fixture["client_key"]),
            str(Path(fixture["receipt_root"]) / "anchor-drift.json"),
        ],
        env=env,
    )
    assert drift.returncode == 70
    assert "pointer contains extra dolt key" in drift.stderr


def test_capture_inventory_runs_all_projections_and_writes_hash_manifest(tmp_path: Path) -> None:
    fixture = _client_fixture(tmp_path)
    bd = tmp_path / "fake-bd"
    calls = tmp_path / "calls.jsonl"
    _write_executable(
        bd,
        "#!/bin/sh\n"
        f"printf '%s\\n' \"$*\" >> {str(calls)!r}\n"
        'case "$1" in inventory) printf "%s\\n" "invented inventory verb called" >&2; exit 91;; esac\n'
        'case "$*" in\n'
        '  "list --status all --limit 0 --json") printf \'[{"id":"o4-issue","value":2}]\\n\' ;;\n'
        '  "show o4-issue --json") printf \'[{"id":"o4-issue","value":2}]\\n\' ;;\n'
        '  "comments o4-issue --json") printf \'[{"id":"comment-1","issue_id":"o4-issue"}]\\n\' ;;\n'
        '  "dep list o4-issue --json") printf \'[{"id":"dep-1","issue_id":"o4-issue"}]\\n\' ;;\n'
        '  "children o4-issue --json") printf \'[{"id":"child-1","parent":"o4-issue"}]\\n\' ;;\n'
        '  "show o4-rig-wisp --json") printf \'[{"id":"o4-rig-wisp","issue_type":"rig"}]\\n\' ;;\n'
        '  "comments o4-rig-wisp --json") printf \'[{"id":"comment-rig","issue_id":"o4-rig-wisp"}]\\n\' ;;\n'
        '  "dep list o4-rig-wisp --json") printf \'[{"id":"dep-rig","issue_id":"o4-rig-wisp"}]\\n\' ;;\n'
        "  \"children o4-rig-wisp --json\") printf '[]\\n' ;;\n"
        "  \"migrate status\") printf 'schema version: 53\\n' ;;\n"
        "  sql*)\n"
        '    case "$*" in\n'
        '      *"status-type-counts.json"*)\n'
        '        printf \'%s\\n\' \'JSON_OBJECT(...)\' \'-------------------------\' \'{"issues.json":[{"id":"o4-issue","issue_type":"task"},{"id":"o4-rig-wisp","issue_type":"rig"}],"labels.json":[{"issue_id":"o4-rig-wisp","label":"acceptance:manual"}],"policy-metadata.json":[{"issue_id":"o4-rig-wisp","policy_labels":["acceptance:manual"]}],"status-type-counts.json":[{"status":"open","issue_type":"rig","COUNT(*)":1}]}\' \'(1 row)\' ;;\n'
        '      *"UNION ALL"*"wisps"*) printf \'%s\\n\' \'COALESCE(...)\' \'"[""o4-issue"",""o4-rig-wisp""]"\' ;;\n'
        "      *) printf '%s\\n' 'COALESCE(...)' '-------------------------' '[{\"id\":\"o4-issue\",\"issue_type\":\"task\"}]' '(1 row)' ;;\n"
        "    esac\n"
        "    ;;\n"
        '  *) printf "%s\\n" "unexpected argv: $*" >&2; exit 92 ;;\n'
        "esac\n",
    )
    output = Path(fixture["receipt_root"]) / "inventory"
    env = {
        "PATH": os.environ["PATH"],
        "RUN_ID": str(fixture["run_id"]),
        "RUN_ROOT": str(fixture["run_root"]),
        "RECEIPT_ROOT": str(fixture["receipt_root"]),
        "TOPOLOGY_MANIFEST": str(fixture["manifest"]),
        "BEADS112_CREDENTIAL_HELPER": str(fixture["credential_helper"]),
        "ASSERT_CLIENT_ANCHOR": str(PACKAGE / "wrappers" / "assert-client-anchor.sh"),
        "BD_PATH": str(bd),
    }
    result = _run(
        [
            str(PACKAGE / "wrappers" / "capture-inventory.sh"),
            str(fixture["client_key"]),
            str(output),
            "pre-backup-v49-baseline",
        ],
        env=env,
    )
    assert result.returncode == 0, result.stderr
    assert {path.name for path in output.iterdir()} == {
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
        "inventory-receipt.json",
        "SHA256SUMS",
        "combined.sha256",
    }
    assert "planned_only" not in (output / "client-anchor.json").read_text()
    called = calls.read_text().splitlines()
    assert len(called) >= 11
    argv = [shlex.split(line) for line in called]
    # Per-issue artifacts MUST be captured for the rig row too. Enumerating from
    # `bd list --json` omits it, because `list` reads `issues` and a rig row lives
    # in `wisps` — which left dependencies.json and comments.json blind.
    for verb in (["show"], ["dep", "list"], ["comments"], ["children"]):
        for issue_id in ("o4-issue", "o4-rig-wisp"):
            assert [*verb, issue_id, "--json"] in argv, (verb, issue_id)
    # NOTE: the stub logs `"$*"`, so shlex.split shreds a SQL body across many
    # tokens. Check the SQL on the RAW line; use argv only for the verb/flags.
    sql_lines = [line for line in called if shlex.split(line)[0] == "sql"]
    sql_calls = [shlex.split(line) for line in sql_lines]
    assert sql_calls, "no bd sql calls were made"
    # Every bd sql call must pass --csv: the default TABLE renderer truncates a
    # long cell at 60 chars with a trailing "...", so the JSON payload does not
    # parse. Measured on a real Dolt server, v1.2.2.
    assert all(a[1] == "--csv" for a in sql_calls), sql_calls
    # A leading /* comment */ makes `bd sql` return "OK, 0 rows affected" with no
    # result set, so no SQL body may begin with one.
    assert not any(
        line.split(None, 2)[2].lstrip().startswith("/*") for line in sql_lines
    ), sql_lines
    # The union assertion must be satisfied by a real UNION, never by a comment
    # mentioning one — that is how the previous revision passed while every query
    # was broken.
    work_item_sql = [
        line for line in sql_lines if "JSON_ARRAYAGG" in line and "FROM issues" in line
    ]
    assert work_item_sql, "no work-item projection reached the SQL surface"
    for body in work_item_sql:
        assert "UNION ALL" in body and "FROM wisps" in body, body[:200]
    assert json.loads((output / "status-type-counts.json").read_text()) == [
        {"COUNT(*)": 1, "issue_type": "rig", "status": "open"},
    ]
    assert json.loads((output / "issues.json").read_text()) == [
        {"id": "o4-issue", "issue_type": "task"},
        {"id": "o4-rig-wisp", "issue_type": "rig"},
    ]
    assert json.loads((output / "labels.json").read_text()) == [
        {"issue_id": "o4-rig-wisp", "label": "acceptance:manual"},
    ]
    assert json.loads((output / "policy-metadata.json").read_text()) == [
        {"issue_id": "o4-rig-wisp", "policy_labels": ["acceptance:manual"]},
    ]
    receipt = json.loads((output / "inventory-receipt.json").read_text())
    assert receipt["schema"] == "livespec.beads_v112_rehearsal.inventory_receipt.v1"
    assert receipt["capture_point"] == "pre-backup-v49-baseline"
    assert receipt["combined_sha256"] == (output / "combined.sha256").read_text().strip()


def test_command_plan_instance_covers_attended_gates_without_live_execution() -> None:
    plan = _json(PACKAGE / "command-plans" / "beads112-rehearsal.command-plan.json")
    schema = _json(PACKAGE / "schemas" / "rehearsal-command-plan.schema.json")
    assert isinstance(plan, dict)
    assert isinstance(schema, dict)
    assert plan["schema"] == schema["$id"]
    assert plan["run_variables"] == ["RUN_ID", "RUN_ROOT", "RECEIPT_ROOT"]
    assert plan["execution_boundary"]["factory_safe_preparation_only"] is True
    assert plan["execution_boundary"]["live_execution_allowed_by_this_package"] is False
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
    for stage in plan["stages"]:
        assert stage["commands"]
        assert stage["argv_templates"] == stage["commands"]
        assert all("planned_only" not in command for command in stage["commands"])
        assert all("prose:" not in command for command in stage["commands"])
    plan_text = json.dumps(plan, sort_keys=True)
    assert "bd init" not in plan_text
    for required in [
        "BD_ALLOW_REMOTE_MIGRATE=1",
        "record-designated-migrator.sh",
        "run-round-trip.sh",
        "compare-restored-baseline.sh",
        "stop-manifest-pid.sh",
        "cleanup-run-scoped-resources.sh",
    ]:
        assert required in plan_text


def test_receipt_schemas_accept_positive_examples_and_reject_placeholders() -> None:
    examples = {
        "anchor-receipt.schema.json": {
            "schema": "livespec.beads_v112_rehearsal.anchor_receipt.v1",
            "client_key": "dense_policy/source/20260817t010203z",
            "client_dir_realpath": "/var/tmp/beads112-rehearsal.20260817t010203z/clients/db",
            "database": "beads112_20260817t010203z_dense_policy_source",
            "sql_user": "b112_20260817t010203z_dp_s",
            "pointer": {"key_count": 7},
            "metadata": {"state": "absent", "sha256": None},
            "wrapper_sha256": "a" * 64,
            "anchor_probe_sha256": "b" * 64,
            "dependency_lock_sha256": "c" * 64,
            "credential_byte_count": 16,
            "query": "SELECT DATABASE(), CURRENT_USER(), @@hostname, @@port",
            "query_sha256": "0f334703b52dea71b6c7184692f245094b4c93cbf1d61bcee36fc6c3531a5b36",
            "read_only_transaction": True,
            "statement_count": 1,
            "started_at": "2026-08-17T01:02:03Z",
            "finished_at": "2026-08-17T01:02:04Z",
            "probe_exit": 0,
            "identity": {"database": "beads112_20260817t010203z_dense_policy_source"},
            "tcp_peer": "127.0.0.1:13307",
            "server_fingerprint": "sha256:isolated",
            "following_command": {"category": "inventory", "sequence": 1},
        },
        "inventory-receipt.schema.json": {
            "schema": "livespec.beads_v112_rehearsal.inventory_receipt.v1",
            "client_key": "dense_policy/source/20260817t010203z",
            "capture_point": "pre-backup-v49-baseline",
            "artifacts": ["issues.json"],
            "per_artifact_sha256": {"issues.json": "a" * 64},
            "combined_sha256": "b" * 64,
        },
        "backup-identity-receipt.schema.json": {
            "schema": "livespec.beads_v112_rehearsal.backup_identity_receipt.v1",
            "run_id": "20260817t010203z",
            "source_database": "beads112_20260817t010203z_dense_policy_source",
            "backup_url": "s3://nonproduction/beads112-20260817t010203z",
            "bucket_prefix": "beads112-20260817t010203z",
            "manifest_namespace": "beads112-20260817t010203z",
            "object_version_id": "v1",
            "etag": "etag",
            "size_inventory": {},
            "branch_heads": {},
            "v49_baseline_digest": "a" * 64,
            "start_time": "2026-08-17T01:02:03Z",
            "finish_time": "2026-08-17T01:02:04Z",
            "helper_commit": "9a598594",
            "command_digest": "b" * 64,
            "single_sync_only": True,
            "exit_status": 0,
        },
        "migration-gate-receipt.schema.json": {
            "schema": "livespec.beads_v112_rehearsal.migration_gate_receipt.v1",
            "client_key": "dense_policy/migrated/20260817t010203z",
            "database": "beads112_20260817t010203z_dense_policy_migrated",
            "armed_before_process_start": True,
            "environment_preflight": {
                "BD_ALLOW_REMOTE_MIGRATE_unset": True,
                "BD_SMART_GATE_unset": True,
            },
            "first_attempt": {"exit_status": 75},
            "gate_decision": "migrate-or-adopt-refusal",
            "inventory_unchanged_after_refusal": True,
            "retry": {"BD_ALLOW_REMOTE_MIGRATE": "1", "exit_status": 0},
        },
        "designated-migrator-receipt.schema.json": {
            "schema": "livespec.beads_v112_rehearsal.designated_migrator_receipt.v1",
            "human_or_session_identity": "operator",
            "process_id": 123,
            "candidate_executable_sha256": "a" * 64,
            "host": "isolated-host",
            "start_time": "2026-08-17T01:02:03Z",
            "ordered_database_list": ["beads112_20260817t010203z_dense_policy_migrated"],
        },
        "round-trip-delta-receipt.schema.json": {
            "schema": "livespec.beads_v112_rehearsal.round_trip_delta_receipt.v1",
            "client_key": "dense_policy/migrated/20260817t010203z",
            "json_outputs_parse": True,
            "expected_issue_delta": 2,
            "expected_dependency_delta": 1,
            "expected_comment_delta": 1,
            "unexpected_changes": 0,
        },
        "restored-baseline-comparison-receipt.schema.json": {
            "schema": "livespec.beads_v112_rehearsal.restored_baseline_comparison_receipt.v1",
            "shape": "dense_policy",
            "source_baseline_combined_sha256": "a" * 64,
            "restored_combined_sha256": "a" * 64,
            "all_artifacts_match": True,
        },
        "cleanup-receipt.schema.json": {
            "schema": "livespec.beads_v112_rehearsal.cleanup_receipt.v1",
            "run_id": "20260817t010203z",
            "pid_absent": True,
            "port_13307_absent": True,
            "receipt_root_retained": True,
            "production_unchanged_receipt": "/receipts/production-unchanged.json",
            "production_port_3307_unchanged": True,
            "production_registry_digest_unchanged": True,
            "production_backup_config_digest_unchanged": True,
            "isolated_data_dir_absent": True,
            "sql_users_absent": True,
            "client_directories_absent": True,
            "run_root_absent": True,
            "removed_manifest_scoped_resources": [],
        },
        "golden-schema-comparison-receipt.schema.json": {
            "schema": "livespec.beads_v112_rehearsal.golden_schema_comparison.v1",
            "migrated_schema_path": "/receipts/inventory/dense_policy/schema.json",
            "migrated_schema_sha256": "a" * 64,
            "golden_schema_path": "/receipts/inventory/golden/schema.json",
            "golden_schema_sha256": "a" * 64,
            "golden_client_dir": "/var/tmp/beads112-rehearsal.20260817t010203z/clients/golden",
            "schema_hash_matches": True,
        },
        "production-unchanged-receipt.schema.json": {
            "schema": "livespec.beads_v112_rehearsal.production_unchanged_receipt.v1",
            "production_port_before": "3307",
            "production_port_after": "3307",
            "production_port_3307_unchanged": True,
            "production_registry_sha256_before": "b" * 64,
            "production_registry_sha256_after": "b" * 64,
            "production_registry_digest_unchanged": True,
            "production_backup_config_sha256_before": "c" * 64,
            "production_backup_config_sha256_after": "c" * 64,
            "production_backup_config_digest_unchanged": True,
        },
        "backup-namespace-preflight-receipt.schema.json": {
            "schema": "livespec.beads_v112_rehearsal.backup_namespace_preflight.v1",
            "run_id": "20260817t010203z",
            "backup_bucket_prefix": "beads112-20260817t010203z",
            "examined_value_count": 7,
            "offending_values": [],
            "bucket_prefix_contains_run_id": True,
            "manifest_namespace_contains_run_id": True,
            "production_values_refused": True,
        },
        "stop-boundary-receipt.schema.json": {
            "schema": "livespec.beads_v112_rehearsal.stop_boundary_receipt.v1",
            "pid_file": "/var/tmp/beads112-rehearsal.20260817t010203z/dolt/dolt.pid",
            "pid_file_state": "present",
            "pid": 4321,
            "process_state": "running",
            "isolated_state_markers": [
                "/var/tmp/beads112-rehearsal.20260817t010203z/dolt/data",
            ],
            "cmdline_references_isolated_state": True,
            "production_port_absent_from_cmdline": True,
            "pid_scope_verified": True,
        },
        "top-level-sha256sums.schema.json": {
            "schema": "livespec.beads_v112_rehearsal.top_level_sha256sums.v1",
            "receipt_root": "/home/ubuntu/.local/state/livespec-proof-logs/beads112-20260817t010203z",
            "entries": [{"path": "anchor.json", "sha256": "a" * 64}],
            "sha256sums_sha256": "b" * 64,
        },
    }
    for name, example in examples.items():
        schema = _json(PACKAGE / "schemas" / name)
        assert isinstance(schema, dict)
        assert _schema_accepts(schema=schema, instance=example)
        placeholder = dict(example)
        placeholder["planned_only"] = True
        assert not _schema_accepts(schema=schema, instance=placeholder)


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


# --- Receipt producers must MEASURE, not assert -----------------------------
#
# Five producers used to publish sixteen assertion fields as a hardcoded True
# while holding one side of the comparison, or none. Schema validation could
# not catch that: the schemas pin `const: true` and the producers wrote exactly
# that, so validation passed by construction and reported a clean green
# carrying no information. The tests below feed each producer inputs that MUST
# drive its assertion false, which is the only shape of check a fabricated
# receipt cannot survive.

WRAPPERS = PACKAGE / "wrappers"
# assert-client-anchor.sh's `read_only_transaction` describes the script's own
# behaviour -- it issues one literal read-only SELECT -- rather than measured
# external state, so it is the one legitimate hardcoded assertion.
_ALLOWED_HARDCODED_ASSERTIONS = {("assert-client-anchor.sh", "read_only_transaction")}


def _run_wrapper(
    script: str, *args: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(WRAPPERS / script), *args],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def _topology(tmp_path: Path, *, run_id: str = "20260817t010203z") -> Path:
    run_root = tmp_path / f"beads112-rehearsal.{run_id}"
    manifest = {
        "run_id": run_id,
        "isolated_server": {
            "port": 13307,
            "data_dir": str(run_root / "dolt" / "data"),
            "config_dir": str(run_root / "dolt" / "config"),
            "pid_file": str(run_root / "dolt" / "dolt.pid"),
        },
        "clients": [
            {
                "client_key": f"dense_policy/source/{run_id}",
                "client_dir": str(run_root / "clients" / f"beads112_{run_id}_dense_source"),
                "database": f"beads112_{run_id}_dense_policy_source",
                "sql_user": f"b112_{run_id}_dp_s",
            },
        ],
    }
    path = tmp_path / "topology.json"
    path.write_text(json.dumps(manifest))
    return path


def test_no_wrapper_publishes_an_unmeasured_assertion(tmp_path: Path) -> None:
    del tmp_path
    hardcoded = {
        (path.name, line.split('"')[1])
        for path in sorted(WRAPPERS.glob("*"))
        if path.is_file()
        for line in path.read_text().splitlines()
        if line.strip().startswith('"') and line.strip().endswith('": True,')
    }
    assert hardcoded == _ALLOWED_HARDCODED_ASSERTIONS


def test_compare_golden_schema_computes_both_sides(tmp_path: Path) -> None:
    migrated = tmp_path / "migrated.json"
    golden = tmp_path / "golden.json"
    receipt = tmp_path / "receipts" / "golden.json"
    migrated.write_text('{"columns": 12}')

    golden.write_text('{"columns": 13}')
    assert (
        _run_wrapper(
            "compare-golden-schema.sh", *map(str, (migrated, golden, "/g", receipt))
        ).returncode
        == 0
    )
    diverged = json.loads(receipt.read_text())
    assert diverged["schema_hash_matches"] is False
    assert diverged["migrated_schema_sha256"] != diverged["golden_schema_sha256"]
    schema = _json(PACKAGE / "schemas" / "golden-schema-comparison-receipt.schema.json")
    assert isinstance(schema, dict)
    assert not _schema_accepts(schema=schema, instance=diverged)

    golden.write_text('{"columns": 12}')
    _run_wrapper("compare-golden-schema.sh", *map(str, (migrated, golden, "/g", receipt)))
    agreed = json.loads(receipt.read_text())
    assert agreed["schema_hash_matches"] is True
    assert _schema_accepts(schema=schema, instance=agreed)


def test_prove_production_unchanged_detects_each_changed_side(tmp_path: Path) -> None:
    receipt = tmp_path / "production-unchanged.json"
    before = ("3307", "a" * 64, "b" * 64)
    unchanged = _run_wrapper(
        "prove-production-unchanged.sh",
        before[0],
        before[0],
        before[1],
        before[1],
        before[2],
        before[2],
        str(receipt),
    )
    assert unchanged.returncode == 0
    assert all(
        json.loads(receipt.read_text())[field] is True
        for field in (
            "production_port_3307_unchanged",
            "production_registry_digest_unchanged",
            "production_backup_config_digest_unchanged",
        )
    )

    changed = {
        "production_port_3307_unchanged": ("3308", before[1], before[2]),
        "production_registry_digest_unchanged": (before[0], "c" * 64, before[2]),
        "production_backup_config_digest_unchanged": (before[0], before[1], "d" * 64),
    }
    schema = _json(PACKAGE / "schemas" / "production-unchanged-receipt.schema.json")
    assert isinstance(schema, dict)
    for field, after in changed.items():
        _run_wrapper(
            "prove-production-unchanged.sh",
            before[0],
            after[0],
            before[1],
            after[1],
            before[2],
            after[2],
            str(receipt),
        )
        payload = json.loads(receipt.read_text())
        assert payload[field] is False, field
        assert not _schema_accepts(schema=schema, instance=payload)


def test_preflight_backup_namespace_refuses_production_and_stray_namespaces(tmp_path: Path) -> None:
    run_id = "20260817t010203z"
    manifest_path = _topology(tmp_path, run_id=run_id)
    receipt = tmp_path / "backup-namespace-preflight.json"
    prefix = f"beads112-{run_id}"

    clean = _run_wrapper(
        "preflight-backup-namespace.sh", str(manifest_path), run_id, prefix, str(receipt)
    )
    assert clean.returncode == 0
    payload = json.loads(receipt.read_text())
    assert payload["production_values_refused"] is True
    assert payload["offending_values"] == []
    assert payload["examined_value_count"] >= 4

    # A bucket prefix that does not carry the run id would let the rehearsal
    # write beside production backups.
    strayed = _run_wrapper(
        "preflight-backup-namespace.sh", str(manifest_path), run_id, "beads-backups", str(receipt)
    )
    assert strayed.returncode != 0
    assert json.loads(receipt.read_text())["bucket_prefix_contains_run_id"] is False

    # A manifest naming the production port must halt, and must say what it saw.
    production = json.loads(manifest_path.read_text())
    production["clients"][0]["database"] = f"beads112_{run_id}_on_3307"
    manifest_path.write_text(json.dumps(production))
    refused = _run_wrapper(
        "preflight-backup-namespace.sh", str(manifest_path), run_id, prefix, str(receipt)
    )
    assert refused.returncode != 0
    assert "HALT" in refused.stderr
    halted = json.loads(receipt.read_text())
    assert halted["production_values_refused"] is False
    assert halted["offending_values"] == [f"beads112_{run_id}_on_3307"]


def _stop_boundary_schema() -> dict[str, object]:
    schema = _json(PACKAGE / "schemas" / "stop-boundary-receipt.schema.json")
    assert isinstance(schema, dict)
    return schema


def _pid_file(manifest_path: Path) -> Path:
    manifest = json.loads(manifest_path.read_text())
    pid_file = Path(manifest["isolated_server"]["pid_file"])
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    return pid_file


def test_stop_manifest_pid_refuses_a_pid_it_cannot_scope(tmp_path: Path) -> None:
    manifest_path = _topology(tmp_path)
    pid_file = _pid_file(manifest_path)
    receipt = tmp_path / "stop-boundary.json"

    # No pid file at all: the old wrapper published pid_scope_verified anyway.
    missing = _run_wrapper("stop-manifest-pid.sh", str(manifest_path), str(receipt))
    assert missing.returncode != 0
    unscoped = json.loads(receipt.read_text())
    assert unscoped["pid_scope_verified"] is False
    assert unscoped["process_state"] == "absent"
    assert not _schema_accepts(schema=_stop_boundary_schema(), instance=unscoped)

    # A live process whose cmdline does NOT name the isolated state tree could
    # be any process on the host, including production's. A plain shell holds
    # the pid; `sh -c CMD name` puts `name` in the child's own cmdline, which
    # is the surface the wrapper inspects.
    stranger = subprocess.Popen(["/bin/sh", "-c", "sleep 30", "/some/other/tree"])
    try:
        pid_file.write_text(f"{stranger.pid}\n")
        wrong = _run_wrapper("stop-manifest-pid.sh", str(manifest_path), str(receipt))
        assert wrong.returncode != 0
        assert json.loads(receipt.read_text())["cmdline_references_isolated_state"] is False
    finally:
        stranger.kill()
        stranger.wait()


def test_stop_manifest_pid_accepts_the_running_isolated_server(tmp_path: Path) -> None:
    manifest_path = _topology(tmp_path)
    manifest = json.loads(manifest_path.read_text())
    pid_file = _pid_file(manifest_path)
    receipt = tmp_path / "stop-boundary.json"

    isolated = subprocess.Popen(
        ["/bin/sh", "-c", "sleep 30", manifest["isolated_server"]["data_dir"]],
    )
    try:
        pid_file.write_text(f"{isolated.pid}\n")
        scoped = _run_wrapper("stop-manifest-pid.sh", str(manifest_path), str(receipt))
        assert scoped.returncode == 0
        payload = json.loads(receipt.read_text())
        assert payload["pid_scope_verified"] is True
        assert payload["pid"] == isolated.pid
        # 13307 contains the digits 3307; a substring test would misread the
        # isolated port as production and refuse a correct stop target.
        assert payload["production_port_absent_from_cmdline"] is True
        assert _schema_accepts(schema=_stop_boundary_schema(), instance=payload)
    finally:
        isolated.kill()
        isolated.wait()


def _production_receipt(tmp_path: Path) -> Path:
    production = tmp_path / "production-unchanged.json"
    production.write_text(
        json.dumps(
            {
                "schema": "livespec.beads_v112_rehearsal.production_unchanged_receipt.v1",
                "production_port_3307_unchanged": True,
                "production_registry_digest_unchanged": True,
                "production_backup_config_digest_unchanged": True,
            },
        ),
    )
    return production


def _cleanup_schema() -> dict[str, object]:
    schema = _json(PACKAGE / "schemas" / "cleanup-receipt.schema.json")
    assert isinstance(schema, dict)
    return schema


def test_cleanup_receipt_measures_residue_rather_than_asserting_its_absence(
    tmp_path: Path,
) -> None:
    manifest_path = _topology(tmp_path)
    manifest = json.loads(manifest_path.read_text())
    run_root = Path(manifest["clients"][0]["client_dir"]).parent.parent
    receipt = tmp_path / "cleanup.json"
    production = _production_receipt(tmp_path)
    argv = (str(manifest_path), str(run_root), str(production), str(receipt))

    # Residue left behind: the client directory and the run root still exist.
    Path(manifest["clients"][0]["client_dir"]).mkdir(parents=True, exist_ok=True)
    Path(manifest["isolated_server"]["data_dir"]).mkdir(parents=True, exist_ok=True)
    assert _run_wrapper("cleanup-run-scoped-resources.sh", *argv).returncode == 0
    residue = json.loads(receipt.read_text())
    assert residue["run_root_absent"] is False
    assert residue["client_directories_absent"] is False
    assert residue["isolated_data_dir_absent"] is False
    assert residue["sql_users_absent"] is False
    assert not _schema_accepts(schema=_cleanup_schema(), instance=residue)

    # Cleaned up: everything under the run root is gone.
    for path in sorted(run_root.rglob("*"), reverse=True):
        path.rmdir()
    run_root.rmdir()
    assert _run_wrapper("cleanup-run-scoped-resources.sh", *argv).returncode == 0
    cleaned = json.loads(receipt.read_text())
    assert cleaned["run_root_absent"] is True
    assert cleaned["sql_users_absent"] is True
    assert cleaned["production_unchanged_receipt"] == str(production)
    assert _schema_accepts(schema=_cleanup_schema(), instance=cleaned)


def test_cleanup_receipt_refuses_a_foreign_production_receipt(tmp_path: Path) -> None:
    # The three production digests are propagated from a receipt that measured
    # them, so an unrelated JSON file must not be able to satisfy them.
    manifest_path = _topology(tmp_path)
    foreign = tmp_path / "foreign.json"
    foreign.write_text(json.dumps({"schema": "something.else.v1"}))
    refused = _run_wrapper(
        "cleanup-run-scoped-resources.sh",
        str(manifest_path),
        str(tmp_path / "absent-run-root"),
        str(foreign),
        str(tmp_path / "cleanup.json"),
    )
    assert refused.returncode != 0
    assert "HALT" in refused.stderr


# --- The secret scan must see the VALUE, not only the variable name ---------
#
# `verify-no-secret-values.sh` used to hold exactly one pattern -- a shell-style
# `BEADS_DOLT_PASSWORD=` assignment -- and it never received the secret at all,
# so it was structurally incapable of seeing the leak it exists to catch. A raw
# credential inside a DSN, a connection string, a JSON field, or a client error
# message carries no variable name, so it passed AND collected a clean
# `secret_scan` receipt: positive evidence for a property nobody had measured.
# The arms below are a three-way control -- arm (b) proves the instrument can
# fire, which is what makes arm (a)'s pass and arm (c)'s old pass different
# observations rather than the same one.

# Synthetic and secret-SHAPED only: this is not a credential, it is never read
# from a credential source, and it only ever reaches a `tmp_path` receipt root.
_SYNTHETIC_SECRET = "sYnth3t1c-not-a-real-credential-9f2b"
_SECRET_SCAN_SCHEMA = "livespec.beads_v112_rehearsal.secret_scan_receipt.v1"


def _secret_scan(receipt_root: Path, *, secret: str | None) -> subprocess.CompletedProcess[str]:
    # The value travels by ENVIRONMENT, which is the channel the wrapper reads:
    # never an argv element (visible in `ps` and shell history) and never a file.
    env = {"PATH": os.environ["PATH"]}
    if secret is not None:
        env["BEADS_DOLT_PASSWORD"] = secret
    return _run_wrapper(
        "verify-no-secret-values.sh", str(receipt_root), "BEADS_DOLT_PASSWORD", env=env
    )


def test_secret_scan_sees_the_secret_value_and_not_only_the_variable_name(tmp_path: Path) -> None:
    root = tmp_path / "receipts"
    root.mkdir()
    receipt = root / "inventory.json"

    # Arm (a) -- a clean receipt root scans clean and publishes the receipt.
    receipt.write_text(json.dumps({"rows": 12, "sanitized_env_names": "BEADS_DOLT_PASSWORD"}))
    clean = _secret_scan(root, secret=_SYNTHETIC_SECRET)
    assert clean.returncode == 0, clean.stderr
    assert json.loads(clean.stdout)["schema"] == _SECRET_SCAN_SCHEMA

    # Arm (b) -- the name-shaped assignment. Retained as the second arm because
    # it still fires once the credential has been rotated and the value below
    # no longer matches anything in the bundle.
    receipt.write_text(f"BEADS_DOLT_PASSWORD={_SYNTHETIC_SECRET}\n")
    named = _secret_scan(root, secret=_SYNTHETIC_SECRET)
    assert named.returncode == 70
    assert "HALT" in named.stderr
    assert _SECRET_SCAN_SCHEMA not in named.stdout

    # Arm (c) -- the raw VALUE inside a DSN, with no variable name anywhere. The
    # absence assertion is the discriminator: without it, arm (b)'s pattern could
    # have produced this halt and the value arm would still be untested.
    receipt.write_text(json.dumps({"dsn": f"mysql://user:{_SYNTHETIC_SECRET}@127.0.0.1:13307/db"}))
    assert "BEADS_DOLT_PASSWORD" not in receipt.read_text()
    valued = _secret_scan(root, secret=_SYNTHETIC_SECRET)
    assert valued.returncode == 70
    assert "HALT" in valued.stderr
    assert _SECRET_SCAN_SCHEMA not in valued.stdout
    assert valued.stderr != named.stderr


def test_secret_scan_halts_when_it_cannot_establish_the_no_leak_property(tmp_path: Path) -> None:
    # Fail-closed: a scan that could not run must not publish a receipt saying
    # it ran and found nothing. Unset and empty are separate arms because
    # `${VAR:-}` collapses them only if the wrapper is written to.
    root = tmp_path / "receipts"
    root.mkdir()
    (root / "inventory.json").write_text(json.dumps({"rows": 12}))

    for missing in (None, ""):
        refused = _secret_scan(root, secret=missing)
        assert refused.returncode == 70
        assert "HALT" in refused.stderr
        assert _SECRET_SCAN_SCHEMA not in refused.stdout

    # A receipt root the scan cannot read is the same class: grep exits 2, which
    # the original `if grep ...` form silently read as "no match, all clean".
    unreadable = _secret_scan(tmp_path / "absent-receipt-root", secret=_SYNTHETIC_SECRET)
    assert unreadable.returncode == 70
    assert "HALT" in unreadable.stderr
    assert _SECRET_SCAN_SCHEMA not in unreadable.stdout


def test_every_produced_receipt_has_a_schema_and_a_contract_entry() -> None:
    plan = _json(PACKAGE / "command-plans" / "beads112-rehearsal.command-plan.json")
    assert isinstance(plan, dict)
    schema_ids = {
        _json(path)["$id"]  # type: ignore[index]
        for path in (PACKAGE / "schemas").glob("*.schema.json")
    }
    produced = {
        line.split('"')[3]
        for path in WRAPPERS.glob("*.sh")
        for line in path.read_text().splitlines()
        if line.strip().startswith('"schema": "livespec.beads_v112_rehearsal.')
    }
    # Four receipts were produced by wrappers the command plan runs while
    # having no schema at all, so nothing downstream could reject them.
    assert produced <= schema_ids
