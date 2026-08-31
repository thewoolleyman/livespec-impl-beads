"""The dispatch-time notice an undeclared conformance premise earns.

`SPECIFICATION/contracts.md`'s factory-sandbox-toolchain-disposition clause
forbids a SILENT degrade: a conformance premise is either declared-and-validated
or ratified-as-a-no-op, and the two must be distinguishable. The schema and the
resolver make the distinction; these cases pin the surface that makes it
OBSERVABLE, which is the only place an adopter ever meets it.

The cases are written around the one thing a value comparison cannot see: an
absent key and an explicitly declared `no_op` resolve to the SAME empty argv, so
every assertion here keys on the ARM and on what reaches stderr, never on the
value alone.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType

import pytest
from livespec_orchestrator_beads_fabro.commands._dispatcher_conformance_premises import (
    CONFORMANCE_CAVEAT_STAGE,
    CONFORMANCE_WARNING_STAGE,
    absent_conformance_keys,
    conformance_field,
    conformance_mode,
    conformance_warning_block,
    emit_conformance_premise_notices,
    internal_conformance_keys,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_contract import (
    ResolvedIntegrationContract,
    resolve_integration_contract,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_defaults import (
    CONFORMANCE_HOOK_INSTALL_INTERNAL_ARGV,
    CONFORMANCE_MODE_INTERNAL,
    CONFORMANCE_MODE_NO_OP,
    CONFORMANCE_MODE_SHELL_ARGV,
    CONFORMANCE_MODES,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_resolver import (
    Defective,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_schema import (
    CONFORMANCE_FIELDS,
    CONFORMANCE_HOOK_INSTALL_FIELD,
    CONFORMANCE_HOOK_INSTALL_KEY,
    CONFORMANCE_VERIFY_COMMIT_REFUSE_HOOK_KEY,
    CONFORMANCE_VERIFY_PLUGIN_RESOLUTION_KEY,
)

_MODULE_PATH = Path(
    ".claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands"
    "/_dispatcher_conformance_premises.py"
)

_ALL_KEYS = (
    CONFORMANCE_HOOK_INSTALL_KEY,
    CONFORMANCE_VERIFY_COMMIT_REFUSE_HOOK_KEY,
    CONFORMANCE_VERIFY_PLUGIN_RESOLUTION_KEY,
)


@dataclass(kw_only=True)
class _Journal:
    """A journal that keeps its records, so a notice's stage is asserted, not inferred."""

    records: list[dict[str, object]] = field(default_factory=list)

    def append(self, *, record: dict[str, object]) -> None:
        self.records.append(record)


def _resolved(*, conformance: dict[str, object] | None = None) -> ResolvedIntegrationContract:
    block: dict[str, object] = {} if conformance is None else {"conformance": conformance}
    return resolve_integration_contract(declaration={"dispatcher": block})


def test_the_module_owning_the_dispatch_time_notice_exists() -> None:
    """The notice has a home of its own; the schema and resolver cannot discharge it."""
    assert _MODULE_PATH.is_file()
    module: ModuleType = importlib.import_module(
        "livespec_orchestrator_beads_fabro.commands._dispatcher_conformance_premises"
    )
    assert set(module.__all__) >= {"emit_conformance_premise_notices"}


def test_an_absent_premise_is_named_by_its_key_and_an_explicit_no_op_is_not() -> None:
    """The warning keys on the ARM: declaring the skip is what silences it."""
    assert absent_conformance_keys(resolved=_resolved()) == _ALL_KEYS
    declared_all = _resolved(
        conformance={
            "hook_install": {"mode": CONFORMANCE_MODE_NO_OP},
            "verify_commit_refuse_hook": {"mode": CONFORMANCE_MODE_NO_OP},
            "verify_plugin_resolution": {"mode": CONFORMANCE_MODE_NO_OP},
        }
    )
    assert absent_conformance_keys(resolved=declared_all) == ()
    # ... and the two resolve to the SAME value, which is why the arm is the test.
    assert declared_all.contract.conformance_hook_install == (
        _resolved().contract.conformance_hook_install
    )


def test_the_warning_block_names_every_absent_key_and_explains_all_three_modes() -> None:
    """Its reader has no fleet context, so it names the file, the keys and each mode."""
    block = conformance_warning_block(keys=_ALL_KEYS)

    for key in _ALL_KEYS:
        assert f"`{key}`" in block
    for mode in CONFORMANCE_MODES:
        assert f"`{mode}`" in block
    assert ".livespec.jsonc" in block
    assert "SKIP" in block
    assert "UNSUPPORTED" in block
    assert "livespec-dev-tooling" in block
    assert "the dispatch proceeds either way" in block


def test_the_notices_reach_stderr_and_the_journal_without_refusing_the_dispatch(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Informational: nothing is returned, nothing is raised, the dispatch goes on."""
    journal = _Journal()

    assert emit_conformance_premise_notices(resolved=_resolved(), journal=journal) is None

    captured = capsys.readouterr()
    assert captured.out == ""
    assert CONFORMANCE_HOOK_INSTALL_KEY in captured.err
    assert [record["stage"] for record in journal.records] == [CONFORMANCE_WARNING_STAGE]
    assert journal.records[0]["keys"] == list(_ALL_KEYS)
    assert journal.records[0]["blocking"] is False


def test_a_fully_declared_repository_earns_no_undeclared_warning_at_all(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An explicit `no_op` puts the choice on the record, which is what was asked for."""
    journal = _Journal()
    resolved = _resolved(
        conformance={
            "hook_install": {"mode": CONFORMANCE_MODE_NO_OP},
            "verify_commit_refuse_hook": {
                "mode": CONFORMANCE_MODE_SHELL_ARGV,
                "argv": ["make", "verify-hook"],
            },
            "verify_plugin_resolution": {"mode": CONFORMANCE_MODE_NO_OP},
        }
    )

    emit_conformance_premise_notices(resolved=resolved, journal=journal)

    assert capsys.readouterr().err == ""
    assert journal.records == []


def test_an_internally_declared_premise_gets_the_one_line_caveat_not_the_block(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The adopter opted in, so it is a reminder -- but the caveat still fires."""
    journal = _Journal()
    resolved = _resolved(
        conformance={
            "hook_install": {"mode": CONFORMANCE_MODE_INTERNAL},
            "verify_commit_refuse_hook": {"mode": CONFORMANCE_MODE_INTERNAL},
            "verify_plugin_resolution": {"mode": CONFORMANCE_MODE_INTERNAL},
        }
    )

    assert internal_conformance_keys(resolved=resolved) == _ALL_KEYS
    emit_conformance_premise_notices(resolved=resolved, journal=journal)

    err = capsys.readouterr().err
    assert err.count("UNSUPPORTED") == len(_ALL_KEYS)
    assert "Declare each key" not in err
    assert [record["stage"] for record in journal.records] == [CONFORMANCE_CAVEAT_STAGE]
    assert journal.records[0]["mode"] == CONFORMANCE_MODE_INTERNAL
    assert resolved.contract.conformance_hook_install == CONFORMANCE_HOOK_INSTALL_INTERNAL_ARGV


def test_the_mode_is_derived_totally_from_the_resolution_including_the_defective_arm() -> None:
    """Every arm answers: three modes partition the value space, a defect answers None."""
    absent = _resolved()
    shell = _resolved(
        conformance={"hook_install": {"mode": CONFORMANCE_MODE_SHELL_ARGV, "argv": ["make"]}}
    )
    internal = _resolved(conformance={"hook_install": {"mode": CONFORMANCE_MODE_INTERNAL}})

    attribute = CONFORMANCE_HOOK_INSTALL_FIELD.attribute
    assert (
        conformance_mode(
            field=CONFORMANCE_HOOK_INSTALL_FIELD, resolution=absent.resolutions[attribute]
        )
        == CONFORMANCE_MODE_NO_OP
    )
    assert (
        conformance_mode(
            field=CONFORMANCE_HOOK_INSTALL_FIELD, resolution=shell.resolutions[attribute]
        )
        == CONFORMANCE_MODE_SHELL_ARGV
    )
    assert (
        conformance_mode(
            field=CONFORMANCE_HOOK_INSTALL_FIELD, resolution=internal.resolutions[attribute]
        )
        == CONFORMANCE_MODE_INTERNAL
    )
    assert (
        conformance_mode(
            field=CONFORMANCE_HOOK_INSTALL_FIELD,
            resolution=Defective(key=CONFORMANCE_HOOK_INSTALL_KEY, reason="unusable"),
        )
        is None
    )


def test_only_a_schema_conformance_field_is_recognised_as_one() -> None:
    """Read off the schema's own tuple, so no other field can be mistaken for a premise."""
    for premise in CONFORMANCE_FIELDS:
        assert conformance_field(attribute=premise.attribute) is premise
    assert conformance_field(attribute="merge_mode") is None
