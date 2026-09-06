"""Integration-tier acceptance for needs-attention envelope conformance.

Binds the two halves of the needs-attention machine-envelope contract in
`SPECIFICATION/contracts.md` that this repository owns as producer and consumer:

    A consumer MUST be able to skip an item it cannot parse ... while consuming
    the rest of the envelope, surfacing what it skipped; a consumer whose parse
    discards the WHOLE envelope on one bad item is non-conforming.

    The producer ... MUST NOT silently omit a candidate that failed validation:
    a composition-time validation failure MUST surface as a visible failure
    alongside the valid items.

Both are driven end to end rather than against hand-built fixtures. The producer
case seeds real work-items through the store/client seam against the in-memory
`FakeBeadsClient` and composes the snapshot, so the invalid candidate is one a
real derivation actually produces. The consumer cases parse the bytes that
composition emitted, so what is under test is the wire envelope this repository
really ships — not a stand-in for it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from livespec_orchestrator_beads_fabro._beads_client import reset_fake_singleton
from livespec_orchestrator_beads_fabro.commands import needs_attention
from livespec_orchestrator_beads_fabro.commands._needs_attention_envelope import (
    parse_envelope,
    render_envelope_markdown,
)
from livespec_orchestrator_beads_fabro.commands.needs_attention import (
    build_attention,
    render_json,
)
from livespec_orchestrator_beads_fabro.store import append_work_item
from livespec_orchestrator_beads_fabro.types import StoreConfig, WorkItem
from livespec_runtime.attention_item import AttentionItem
from livespec_runtime.needs_attention import SpecNextOutput

# A purely decimal work-item id is the reachable production case: the
# `hygiene:<type>:<resource>` derivation is correct, and the runtime validator
# still rejects the result because a decimal component is not a stable key. That
# makes it an INVALID CANDIDATE produced by a real lane rather than by a fixture
# reaching around the composition.
_DECIMAL_ITEM_ID = "4242"
_VALID_ITEM_ID = "bd-auto"
_FAILURE_ID_PREFIX = "hygiene:attention-invalid:"


@pytest.fixture(autouse=True)
def _hermetic_fake_backend() -> object:
    """Reset the process-singleton fake tenant before and after each case."""
    reset_fake_singleton()
    yield
    reset_fake_singleton()


def _config() -> StoreConfig:
    return StoreConfig(
        tenant="livespec-impl-beads",
        prefix="livespec-impl-beads",
        server_user="livespec-impl-beads",
        database="livespec-impl-beads",
        bd_path="bd",
        fake=True,
    )


def _write_config(project_root: Path) -> None:
    (project_root / ".livespec.jsonc").write_text(
        json.dumps(
            {
                "livespec-orchestrator-beads-fabro": {
                    "connection": {
                        "tenant": "livespec-impl-beads",
                        "prefix": "bd",
                        "server_user": "livespec-impl-beads",
                        "database": "livespec-impl-beads",
                        "bd_path": "bd",
                        "fake": True,
                    },
                    "dispatcher": {"auto_approve_ready": True},
                }
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _seed(*, id_: str, rank: str) -> None:
    append_work_item(
        path=_config(),
        item=WorkItem(
            id=id_,
            type="task",
            status="pending-approval",
            title=f"{id_} title",
            description="d",
            origin="freeform",
            gap_id=None,
            rank=rank,
            assignee=None,
            depends_on=(),
            captured_at="2026-05-19T00:00:00Z",
            resolution=None,
            reason=None,
            audit=None,
            superseded_by=None,
            blocked_reason=None,
            factory_safety=None,
            admission_policy=None,
            acceptance_policy=None,
            spec_commitment_hint=None,
        ),
    )


def _no_spec_next(*, project_root: Path) -> SpecNextOutput | None:
    _ = project_root
    return None


def _compose(*, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> list[AttentionItem]:
    """Compose the snapshot with the cross-plane spec lane stubbed out."""
    monkeypatch.setattr(needs_attention, "spec_next", _no_spec_next)
    return build_attention(project_root=tmp_path, repo_name="repo", include_hygiene=False)


def _valid_only_envelope(*, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    """The real wire bytes for a snapshot whose every candidate is valid."""
    _write_config(tmp_path)
    _seed(id_=_VALID_ITEM_ID, rank="a1")
    return render_json(attention=_compose(tmp_path=tmp_path, monkeypatch=monkeypatch))


def test_producer_emits_the_valid_item_and_surfaces_the_validation_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The valid candidate is emitted; the rejected one is loud, not absent."""
    _write_config(tmp_path)
    _seed(id_=_VALID_ITEM_ID, rank="a1")
    _seed(id_=_DECIMAL_ITEM_ID, rank="a2")

    attention = _compose(tmp_path=tmp_path, monkeypatch=monkeypatch)
    ids = [item.id for item in attention]

    # The valid candidate is still emitted, unchanged, alongside the failure.
    assert f"hygiene:awaiting-admission:{_VALID_ITEM_ID}" in ids
    # The invalid candidate is NOT on the wire under its own id ...
    assert f"hygiene:awaiting-admission:{_DECIMAL_ITEM_ID}" not in ids
    # ... and it is NOT silently absent either: a visible failure names it.
    [failure] = [item for item in attention if item.id.startswith(_FAILURE_ID_PREFIX)]
    assert _DECIMAL_ITEM_ID in failure.summary
    assert failure.urgency == "high"
    assert "never because the underlying fact resolved" in failure.summary


def test_producer_failure_item_itself_satisfies_the_runtime_validator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The loud half must not be droppable by the mechanism it reports on."""
    _write_config(tmp_path)
    _seed(id_=_DECIMAL_ITEM_ID, rank="a1")

    envelope = render_json(attention=_compose(tmp_path=tmp_path, monkeypatch=monkeypatch))
    consumed = parse_envelope(envelope=envelope)

    assert not consumed.skipped
    assert [item.id for item in consumed.items if item.id.startswith(_FAILURE_ID_PREFIX)]


def test_consumer_skips_one_malformed_item_and_consumes_the_rest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One malformed item costs itself; the envelope is not discarded."""
    payload = json.loads(_valid_only_envelope(tmp_path=tmp_path, monkeypatch=monkeypatch))
    well_formed_ids = [entry["id"] for entry in payload["attention"]]
    assert len(well_formed_ids) >= 1
    # One malformed item among the well-formed ones: `summary` is absent, so the
    # per-item field guarantees do not hold for it.
    payload["attention"].insert(
        0, {"id": "hygiene:broken:subject", "kind": "hygiene", "urgency": "high"}
    )
    mixed = json.dumps(payload)

    consumed = parse_envelope(envelope=mixed)

    assert [item.id for item in consumed.items] == well_formed_ids
    assert [entry.position for entry in consumed.skipped] == [0]
    assert "summary" in consumed.skipped[0].reason
    rendered = render_envelope_markdown(envelope=mixed)
    assert "## Skipped malformed items" in rendered
    assert "- item 0: " in rendered
    for identifier in well_formed_ids:
        assert f"`{identifier}`" in rendered


def test_consumer_treats_an_unknown_kind_as_well_formed_and_renders_it_generically(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An unknown `kind` is a well-formed item, never a skip reason."""
    payload = json.loads(_valid_only_envelope(tmp_path=tmp_path, monkeypatch=monkeypatch))
    payload["attention"].append(
        {
            "id": "hygiene:future-fact:subject",
            "kind": "a-kind-this-build-predates",
            "urgency": "low",
            "summary": "A fact class shipped after this consumer was built.",
            "source_ref": {"repo": "repo", "work_item": None, "path": None},
            "handoff": {"kind": "shell", "command": "true", "action_id": None},
        }
    )
    widened = json.dumps(payload)

    consumed = parse_envelope(envelope=widened)

    assert not consumed.skipped
    assert consumed.items[-1].kind == "a-kind-this-build-predates"
    rendered = render_envelope_markdown(envelope=widened)
    assert "(kind `a-kind-this-build-predates`)" in rendered
    assert "A fact class shipped after this consumer was built." in rendered
