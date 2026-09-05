"""Scenario 114 — the `context` read primitive's item-context envelope.

Binds `SPECIFICATION/scenarios.md` "Scenario 114 — The `context` read primitive
assembles a deterministic item-context envelope" and the `context` operation
contract it realizes, in `SPECIFICATION/contracts.md`.

The whole primitive runs as production code against the REAL store/client seam
— the in-memory `FakeBeadsClient` that is both the hermetic CI backend and the
no-live-connection runtime fallback — over a fixture tenant built entirely
through the client's public write verbs. Nothing is stood in: the argv parse,
the connection resolution, the tenant read, the child union, the anchor read
off the real filesystem and the JSON emission are all the shipped code.

The tenant is built to defeat the two readings that would look right and be
wrong. It carries a dotted-id child AND an edge-linked child, because either
enumeration alone returns a plausible non-empty list while silently dropping
the other linkage; and its epic's dependency array carries a `parent-child`
edge beside a `blocks` edge, because the array is heterogeneous and a
blocks-only projection would report the epic as unparented.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

import pytest
from livespec_orchestrator_beads_fabro._beads_client import (
    EDGE_BLOCKS,
    EDGE_PARENT_CHILD,
    FakeBeadsClient,
    IssueDraft,
    make_beads_client,
    reset_fake_singleton,
)
from livespec_orchestrator_beads_fabro.commands.context import main
from livespec_orchestrator_beads_fabro.types import StoreConfig

if TYPE_CHECKING:
    from pathlib import Path

_EPIC_ID = "bd-ib-s114"
_DOTTED_CHILD_ID = "bd-ib-s114.1"
_EDGE_CHILD_ID = "bd-ib-s114edge"
_BLOCKER_ID = "bd-ib-s114blocker"
_SLUG = "context-read-primitive"
_ENVELOPE_FIELDS = (
    "children",
    "comments",
    "dependencies",
    "epic",
    "next_action",
    "research",
    "spec",
    "subject",
)


@pytest.fixture(autouse=True)
def _hermetic_tenant(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("LIVESPEC_BEADS_FAKE", "1")
    reset_fake_singleton()
    yield
    reset_fake_singleton()


def _config() -> StoreConfig:
    return StoreConfig(
        tenant="livespec-impl-beads",
        prefix="bd-ib",
        server_user="livespec-impl-beads",
        database="livespec-impl-beads",
        bd_path="bd",
        fake=True,
    )


def _client() -> FakeBeadsClient:
    client = make_beads_client(config=_config())
    assert isinstance(client, FakeBeadsClient)
    return client


def _draft(
    *,
    issue_id: str,
    issue_type: str = "task",
    metadata: dict[str, Any] | None = None,
    spec_id: str | None = None,
    parent_id: str | None = None,
) -> IssueDraft:
    return IssueDraft(
        issue_id=issue_id,
        issue_type=issue_type,
        title=f"{issue_id} title",
        description=f"{issue_id} description",
        assignee=None,
        created_at="2026-09-05T00:00:00Z",
        metadata={"rank": "a1", **(metadata or {})},
        labels=["origin:freeform"],
        spec_id=spec_id,
        parent_id=parent_id,
    )


def _fixture_tenant(*, project_root: Path) -> None:
    client = _client()
    _ = client.create_issue(
        draft=_draft(
            issue_id=_EPIC_ID,
            issue_type="epic",
            metadata={
                "plan_slug": _SLUG,
                "next_action": {
                    "kind": "impl",
                    "ref": _DOTTED_CHILD_ID,
                    "text": "Land the context loader slice.",
                },
            },
            spec_id=f"plan:{_SLUG}",
        )
    )
    _ = client.create_issue(draft=_draft(issue_id=_BLOCKER_ID))
    _ = client.create_issue(
        draft=_draft(issue_id=_DOTTED_CHILD_ID, spec_id="obligation-context-read-primitive")
    )
    _ = client.create_issue(draft=_draft(issue_id=_EDGE_CHILD_ID, parent_id=_EPIC_ID))
    client.add_dependency(from_id=_EPIC_ID, to_id=_BLOCKER_ID, edge_type=EDGE_BLOCKS)
    client.add_dependency(from_id=_EPIC_ID, to_id=_BLOCKER_ID, edge_type=EDGE_PARENT_CHILD)
    client.add_comment(issue_id=_EPIC_ID, body="Console decision D6 ratified this surface.")
    client.add_comment(issue_id=_DOTTED_CHILD_ID, body="Rider: union both child linkages.")
    _ = (project_root / ".livespec.jsonc").write_text(
        '{"livespec-orchestrator-beads-fabro": {"connection": {"prefix": "bd-ib"}}}',
        encoding="utf-8",
    )
    plan_dir = project_root / "plan" / _SLUG
    _ = (plan_dir / "research").mkdir(parents=True)
    _ = (plan_dir / "associated_work_item_id").write_text(f"{_EPIC_ID}\n", encoding="utf-8")
    _ = (plan_dir / "research" / "001-charter.md").write_text("charter\n", encoding="utf-8")


def _run(*, project_root: Path, key: str, capsys: pytest.CaptureFixture[str]) -> str:
    assert main(argv=[key, "--json", "--project-root", str(project_root)]) == 0
    return capsys.readouterr().out


def test_scenario114_epic_envelope_populates_every_field(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _fixture_tenant(project_root=tmp_path)

    envelope = json.loads(_run(project_root=tmp_path, key=_EPIC_ID, capsys=capsys))

    assert tuple(sorted(envelope)) == _ENVELOPE_FIELDS
    assert all(envelope[field] for field in _ENVELOPE_FIELDS)
    assert envelope["epic"]["id"] == _EPIC_ID
    assert [comment["text"] for comment in envelope["comments"]] == [
        "Console decision D6 ratified this surface."
    ]
    # Both linkages, unioned — the dotted-id child and the edge-linked one.
    assert [child["id"] for child in envelope["children"]] == [
        _DOTTED_CHILD_ID,
        _EDGE_CHILD_ID,
    ]
    assert envelope["dependencies"] == [
        {"depends_on_id": _BLOCKER_ID, "type": EDGE_BLOCKS},
        {"depends_on_id": _BLOCKER_ID, "type": EDGE_PARENT_CHILD},
    ]
    assert envelope["next_action"]["ref"] == _DOTTED_CHILD_ID
    assert envelope["research"]["files"] == [f"plan/{_SLUG}/research/001-charter.md"]
    assert envelope["spec"]["citations"] == ["obligation-context-read-primitive"]


def test_scenario114_child_envelope_carries_the_same_field_shape(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _fixture_tenant(project_root=tmp_path)

    epic = json.loads(_run(project_root=tmp_path, key=_EPIC_ID, capsys=capsys))
    child = json.loads(_run(project_root=tmp_path, key=_DOTTED_CHILD_ID, capsys=capsys))

    assert tuple(sorted(child)) == tuple(sorted(epic))
    assert child["epic"]["id"] == _DOTTED_CHILD_ID
    assert child["subject"]["plan_epic_id"] == _EPIC_ID
    assert child["research"] == epic["research"]
    assert child["next_action"] == epic["next_action"]


def test_scenario114_two_runs_are_byte_identical_and_the_store_is_unmodified(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _fixture_tenant(project_root=tmp_path)
    before = json.dumps(_client().list_issues(), sort_keys=True)

    first = _run(project_root=tmp_path, key=_SLUG, capsys=capsys)
    second = _run(project_root=tmp_path, key=_SLUG, capsys=capsys)

    assert first == second
    assert json.dumps(_client().list_issues(), sort_keys=True) == before


def test_scenario114_an_unknown_key_fails_naming_it_and_emits_no_envelope(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _fixture_tenant(project_root=tmp_path)

    rc = main(argv=["bd-ib-never-filed", "--json", "--project-root", str(tmp_path)])

    captured = capsys.readouterr()
    assert rc == 3
    assert captured.out == ""
    assert "bd-ib-never-filed" in captured.err
