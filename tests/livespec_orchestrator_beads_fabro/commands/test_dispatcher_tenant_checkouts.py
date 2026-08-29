"""Tests for tenant-scoped checkout enumeration and the WIP-cap bound it widens."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from livespec_orchestrator_beads_fabro.commands._dispatcher_claim_reclaim import (
    claimed_active_count,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_io import JournalFile
from livespec_orchestrator_beads_fabro.commands._dispatcher_tenant_checkouts import (
    register_tenant_checkout,
    tenant_checkout_registry_dir,
    tenant_checkouts,
)
from livespec_orchestrator_beads_fabro.types import WorkItem

_TENANT = "livespec-impl-beads"


def test_an_unidentified_checkout_has_no_registry_and_enumerates_only_itself(
    tmp_path: Path,
) -> None:
    """No tenant declared is no grouping to join — the honest degradation.

    This is the monotonicity floor the WIP-cap predicate depends on: the answer
    is exactly the pre-existing per-checkout one, never fewer checkouts.
    """
    assert tenant_checkout_registry_dir(repo=tmp_path) is None
    assert tenant_checkouts(repo=tmp_path) == (tmp_path.resolve(),)


def test_registration_makes_a_sibling_checkout_visible_to_the_whole_tenant(
    tmp_path: Path,
) -> None:
    dispatching = _checkout(root=tmp_path, name="dispatching")
    peer = _checkout(root=tmp_path, name="peer")

    register_tenant_checkout(repo=dispatching)

    assert tenant_checkouts(repo=peer) == (peer.resolve(), dispatching.resolve())
    assert tenant_checkouts(repo=dispatching) == (dispatching.resolve(),)


def test_registration_is_idempotent_and_never_duplicates_a_checkout(
    tmp_path: Path,
) -> None:
    dispatching = _checkout(root=tmp_path, name="dispatching")
    peer = _checkout(root=tmp_path, name="peer")

    register_tenant_checkout(repo=dispatching)
    register_tenant_checkout(repo=dispatching)

    assert tenant_checkouts(repo=peer) == (peer.resolve(), dispatching.resolve())


def test_two_checkouts_of_one_tenant_share_one_registry_directory(tmp_path: Path) -> None:
    """Distinct checkouts, identical registry — the point of keying on tenant."""
    first = _checkout(root=tmp_path, name="first")
    second = _checkout(root=tmp_path, name="second")

    assert tenant_checkout_registry_dir(repo=first) == tenant_checkout_registry_dir(repo=second)


def test_a_registry_directory_name_substitutes_path_unsafe_tenant_characters(
    tmp_path: Path,
) -> None:
    checkout = _checkout(root=tmp_path, name="odd", tenant="fleet/tenant one")

    directory = tenant_checkout_registry_dir(repo=checkout)

    assert directory is not None
    assert directory.name == "fleet_tenant_one"


def test_registering_drops_the_entry_of_a_checkout_that_no_longer_exists(
    tmp_path: Path,
) -> None:
    """A deleted checkout is not a checkout — it can hold no live claim.

    Pruning at registration keeps the registry bounded across the many
    short-lived worktrees a drain creates, without a read pass ever mutating.
    """
    departed = _checkout(root=tmp_path, name="departed")
    surviving = _checkout(root=tmp_path, name="surviving")
    peer = _checkout(root=tmp_path, name="peer")
    register_tenant_checkout(repo=departed)
    _remove_tree(path=departed)

    register_tenant_checkout(repo=surviving)

    assert tenant_checkouts(repo=peer) == (peer.resolve(), surviving.resolve())


def test_an_unreadable_registry_directory_yields_no_peers(tmp_path: Path) -> None:
    """A registry we cannot list degrades to today's answer, never below it."""
    checkout = _checkout(root=tmp_path, name="solo")
    directory = tenant_checkout_registry_dir(repo=checkout)
    assert directory is not None
    directory.parent.mkdir(parents=True, exist_ok=True)
    _ = directory.write_text("not a directory\n", encoding="utf-8")

    assert tenant_checkouts(repo=checkout) == (checkout.resolve(),)


def test_registry_entries_that_do_not_parse_are_skipped_not_trusted(
    tmp_path: Path,
) -> None:
    checkout = _checkout(root=tmp_path, name="solo")
    peer = _checkout(root=tmp_path, name="peer")
    register_tenant_checkout(repo=peer)
    directory = tenant_checkout_registry_dir(repo=checkout)
    assert directory is not None
    _ = (directory / "unreadable-entry.json").mkdir()
    _ = (directory / "not-json.json").write_text("{{{", encoding="utf-8")
    _ = (directory / "not-an-object.json").write_text("[]", encoding="utf-8")
    _ = (directory / "no-checkout-key.json").write_text('{"other": 1}', encoding="utf-8")
    _ = (directory / "empty-checkout.json").write_text('{"checkout": ""}', encoding="utf-8")

    assert tenant_checkouts(repo=checkout) == (checkout.resolve(), peer.resolve())


@pytest.mark.parametrize(
    "body",
    [
        "{ not json at all",
        json.dumps(["not", "an", "object"]),
        json.dumps({"livespec-orchestrator-beads-fabro": "not-a-block"}),
        json.dumps({"livespec-orchestrator-beads-fabro": {"connection": "not-a-block"}}),
        json.dumps({"livespec-orchestrator-beads-fabro": {"connection": {"tenant": 7}}}),
        json.dumps({"livespec-orchestrator-beads-fabro": {"connection": {"tenant": "  "}}}),
    ],
)
def test_a_config_that_declares_no_usable_tenant_leaves_the_checkout_unidentified(
    tmp_path: Path, body: str
) -> None:
    _ = (tmp_path / ".livespec.jsonc").write_text(body, encoding="utf-8")

    assert tenant_checkout_registry_dir(repo=tmp_path) is None


def test_registering_an_unidentified_checkout_writes_nothing(tmp_path: Path) -> None:
    register_tenant_checkout(repo=tmp_path)

    assert list(tmp_path.iterdir()) == []


def test_a_green_terminal_row_is_still_uncounted_with_a_registered_peer(
    tmp_path: Path,
) -> None:
    """The widened scope does not weaken the green-terminal reclamation.

    Its existing controls run against an UNIDENTIFIED checkout, which cannot
    reach the tenant enumeration at all — so a regression there would pass
    them. This exercises the same guarantee on the widened path.
    """
    querying = _checkout(root=tmp_path, name="querying")
    peer = _checkout(root=tmp_path, name="peer")
    register_tenant_checkout(repo=peer)
    item = _active_item(item_id="bd-green-tenant")
    journal = JournalFile(path=querying / "tmp" / "journal.jsonl")
    journal.append(record={"stage": "ledger-admit", "work_item_id": item.id})
    journal.append(
        record={
            "stage": "outcome",
            "outcome": {"work_item_id": item.id, "status": "green", "stage": "done"},
        }
    )

    assert claimed_active_count(repo=querying, items=[item], journal=journal) == 0


def test_an_unreadable_journal_still_counts_more_with_a_registered_peer(
    tmp_path: Path,
) -> None:
    """The widened scope does not weaken the fail-closed journal term either.

    Losing the journal must count MORE rows, never fewer: an unreadable journal
    with no lock anywhere in the tenant still occupies its slot.
    """
    querying = _checkout(root=tmp_path, name="querying")
    peer = _checkout(root=tmp_path, name="peer")
    register_tenant_checkout(repo=peer)
    item = _active_item(item_id="bd-unreadable-tenant")
    journal = JournalFile(path=querying)

    assert claimed_active_count(repo=querying, items=[item], journal=journal) == 1


def _active_item(*, item_id: str) -> WorkItem:
    return WorkItem(
        id=item_id,
        type="task",
        status="active",
        title="Claim",
        description="Tenant-scoped dispatch claim fixture.",
        origin="freeform",
        gap_id=None,
        rank="a1",
        assignee=None,
        depends_on=(),
        captured_at="2026-08-29T00:00:00Z",
        resolution=None,
        reason=None,
        audit=None,
        superseded_by=None,
        admission_policy="auto",
        acceptance_policy="ai-only",
    )


def _checkout(*, root: Path, name: str, tenant: str = _TENANT) -> Path:
    checkout = root / name
    checkout.mkdir(parents=True)
    _ = (checkout / ".livespec.jsonc").write_text(
        "// A checkout of one tenant, declared the way a real one declares it.\n"
        + json.dumps({"livespec-orchestrator-beads-fabro": {"connection": {"tenant": tenant}}}),
        encoding="utf-8",
    )
    return checkout


def _remove_tree(*, path: Path) -> None:
    for child in sorted(path.iterdir()):
        child.unlink()
    path.rmdir()
