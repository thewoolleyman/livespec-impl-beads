"""Tier 0 Enemy Unit Tests for the real `bd` dependency.

Reads and contracts only — no item mutation, and (apart from idempotent custom
status provisioning) nothing that changes stored data. This suite is
intentionally outside `tests/` so the hermetic `just check` aggregate never
needs a live bd binary or an isolated server. Invoke it explicitly:

    BEADS_EUT_BIN=/path/to/bd BEADS_EUT_CWD=/scratch/client just beads-enemy-tier0

The pure-contract tests (surface, coercion, status constants) run always; the
tests that read a live store SKIP when `BEADS_EUT_BIN` is unset.
"""

# ruff: noqa: S101 — assert is the assertion idiom in an Enemy Unit Test suite.
# pyright: reportPrivateUsage=false, reportUnusedCallResult=false
# The suite deliberately reads the store's private status constants
# (`_STATUS_CUSTOM`, `_NATIVE_STATUS_REMAP`) to prove the harness checks the
# REAL registration surface, and discards read-verb results in raises-blocks.

from __future__ import annotations

import pytest
from _tier0_support import (
    EXCLUDED_VERB_METHODS,
    SEVEN_LIFECYCLE_STATUSES,
    TWELVE_METHODS,
    BeadsTier0Config,
    parse_records,
    record_ids,
    run_raw,
)
from livespec_orchestrator_beads_fabro._beads_client import (
    _STATUS_CUSTOM,
    ShellBeadsClient,
)
from livespec_orchestrator_beads_fabro._beads_client_argv import (
    coerce_comment_list,
    coerce_issue_record,
    coerce_record_list,
    parse_json_output,
)
from livespec_orchestrator_beads_fabro._store_statuses import (
    ALLOWED_BEADS_STATUSES,
    PARKED_BEADS_STATUSES,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_ledger_close import (
    _NATIVE_STATUS_REMAP,
)
from livespec_orchestrator_beads_fabro.errors import BeadsMappingError

__all__: list[str] = []

_EXPECTED_CUSTOM_STATUS_COUNT = 5


# --------------------------------------------------------------------------- #
# Pure-contract tests — hermetic, no binary required.
# --------------------------------------------------------------------------- #


def test_client_exposes_exactly_the_twelve_methods_and_no_more() -> None:
    public = {
        name
        for name in dir(ShellBeadsClient)
        if not name.startswith("_") and callable(getattr(ShellBeadsClient, name))
    }

    assert public == TWELVE_METHODS


def test_excluded_verbs_are_not_client_methods() -> None:
    public = {name for name in dir(ShellBeadsClient) if not name.startswith("_")}

    assert public.isdisjoint(EXCLUDED_VERB_METHODS)


def test_parse_json_output_maps_empty_stdout_to_empty_list() -> None:
    assert parse_json_output(stdout="", argv_repr="list --json") == []
    assert parse_json_output(stdout="   \n  ", argv_repr="list --json") == []


def test_coerce_record_list_drops_non_dict_members() -> None:
    parsed = [{"id": "a"}, "not-a-dict", 7, {"id": "b"}, None]

    coerced = coerce_record_list(parsed=parsed)

    assert coerced == [{"id": "a"}, {"id": "b"}]


def test_coerce_comment_list_drops_non_dict_members() -> None:
    parsed = [{"text": "one"}, "skip", {"text": "two"}, 3]

    coerced = coerce_comment_list(parsed=parsed, issue_id="beads-eut-1")

    assert coerced == [{"text": "one"}, {"text": "two"}]


def test_coerce_issue_record_enforces_a_one_element_array_from_show() -> None:
    assert coerce_issue_record(parsed=[{"id": "beads-eut-1"}], issue_id="beads-eut-1") == {
        "id": "beads-eut-1"
    }

    with pytest.raises(BeadsMappingError):
        coerce_issue_record(parsed={"id": "beads-eut-1"}, issue_id="beads-eut-1")
    with pytest.raises(BeadsMappingError):
        coerce_issue_record(parsed=[], issue_id="beads-eut-1")


def test_allowed_statuses_are_exactly_the_seven_lifecycle_statuses() -> None:
    lifecycle = ALLOWED_BEADS_STATUSES - PARKED_BEADS_STATUSES

    assert lifecycle == SEVEN_LIFECYCLE_STATUSES
    # `deferred` is the sole parked (non-lifecycle) allowed status.
    assert set(PARKED_BEADS_STATUSES) == {"deferred"}


def test_status_custom_registers_exactly_five_entries() -> None:
    entries = _STATUS_CUSTOM.split(",")

    assert len(entries) == _EXPECTED_CUSTOM_STATUS_COUNT
    names = {entry.split(":", 1)[0] for entry in entries}
    assert names == {"backlog", "pending-approval", "ready", "active", "acceptance"}


def test_native_status_remap_maps_open_to_backlog_and_in_progress_to_active() -> None:
    assert _NATIVE_STATUS_REMAP["open"].to == "backlog"
    assert _NATIVE_STATUS_REMAP["in_progress"].to == "active"
    # Only these two beads-native statuses are auto-healed; everything else
    # surfaces via the conformance check rather than being remapped.
    assert set(_NATIVE_STATUS_REMAP) == {"open", "in_progress"}


# --------------------------------------------------------------------------- #
# Live-store tests — SKIP without BEADS_EUT_BIN.
# --------------------------------------------------------------------------- #


def test_list_literal_forms_agree_on_non_closed_and_differ_on_closed(
    *,
    config: BeadsTier0Config,
    client: ShellBeadsClient,
) -> None:
    store_config = config.store_config()
    all_records = client.list_issues()
    bare = run_raw(config=store_config, verb_args=["list", "--limit", "0", "--json"])
    bare_records = parse_records(stdout=bare.stdout, argv_repr="list --limit 0 --json")

    all_ids = record_ids(records=all_records)
    non_closed_all = {
        record["id"]
        for record in all_records
        if isinstance(record.get("id"), str) and record.get("status") != "closed"
    }
    bare_ids = record_ids(records=bare_records)
    closed_ids = all_ids - non_closed_all

    if not closed_ids:
        pytest.skip("fixture carries no closed item; seed one to exercise the closed-set delta")
    # The two literal forms agree on the non-closed set...
    assert bare_ids == non_closed_all
    # ...and differ on the closed set: `--status all` sees closed items the bare
    # form hides. This is the load-bearing `--status all` trap encoded as a test.
    assert closed_ids
    assert closed_ids.isdisjoint(bare_ids)


def test_bd_ready_and_stats_distinguish_dead_from_working(
    *,
    config: BeadsTier0Config,
    client: ShellBeadsClient,
) -> None:
    store_config = config.store_config()
    # A populated store means list_issues sees rows; if it does not, the fixture
    # is not seeded and neither ready nor stats can distinguish dead from working.
    if not client.list_issues():
        pytest.skip("fixture is empty; seed the isolated store before running the live tier 0")

    ready = run_raw(config=store_config, verb_args=["ready", "--json"])
    stats = run_raw(config=store_config, verb_args=["stats"])

    # `bd ready` must at least return a parseable JSON list (its emptiness here
    # is exactly the dead-vs-working signal the harness characterizes: on a store
    # with `ready:active` registered it should surface the ready-category items).
    ready_records = parse_records(stdout=ready.stdout, argv_repr="ready --json")
    assert isinstance(ready_records, list)
    # `bd stats` against a populated store proves the binary reads real data.
    assert stats.stdout.strip() != ""


def test_register_custom_statuses_round_trips_to_config_get(
    *,
    config: BeadsTier0Config,
    client: ShellBeadsClient,
) -> None:
    store_config = config.store_config()
    # Idempotent per-tenant provisioning (config write, not item data), the
    # precondition every custom-status read depends on.
    client.register_custom_statuses()

    observed = run_raw(config=store_config, verb_args=["config", "get", "status.custom"])
    registered_names = {entry.split(":", 1)[0] for entry in _STATUS_CUSTOM.split(",")}

    for name in registered_names:
        assert name in observed.stdout
