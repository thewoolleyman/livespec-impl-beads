from __future__ import annotations

from importlib import util
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
ANCHOR_PROBE = (
    ROOT
    / "plan"
    / "archive"
    / "beads-v1-1-2-upgrade"
    / "rehearsal-package"
    / "wrappers"
    / "anchor-probe.py"
)


def _anchor_probe_module() -> ModuleType:
    spec = util.spec_from_file_location("beads_v112_anchor_probe_edges", ANCHOR_PROBE)
    assert spec is not None
    assert spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_anchor_probe_refuses_empty_direct_credential() -> None:
    module = _anchor_probe_module()
    with pytest.raises(SystemExit) as error:
        module.probe_identity(
            host="127.0.0.1",
            port=13307,
            user="b112_20260817t010203z_dp_s",
            password="",
            database="beads112_20260817t010203z_dense_policy_source",
        )
    assert str(error.value) == module.ERROR_CREDENTIAL_REQUIRED


def test_anchor_probe_cli_refuses_missing_credential(monkeypatch) -> None:
    module = _anchor_probe_module()
    monkeypatch.delenv("BEADS_DOLT_PASSWORD", raising=False)
    with pytest.raises(SystemExit) as error:
        module.main(
            argv=[
                "--host",
                "127.0.0.1",
                "--port",
                "13307",
                "--user",
                "b112_20260817t010203z_dp_s",
                "--database",
                "beads112_20260817t010203z_dense_policy_source",
            ],
        )
    assert str(error.value) == module.ERROR_CREDENTIAL_REQUIRED
