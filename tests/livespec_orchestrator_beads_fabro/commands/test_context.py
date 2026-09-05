"""The `context` read primitive's CLI surface.

Exercises `main()` (the supervisor: exit codes, the `--json` envelope, the
human rendering, the not-found refusal) and `item_context` directly, against
the hermetic in-memory tenant every test at this tier uses.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import pytest
from livespec_orchestrator_beads_fabro._beads_client import (
    EDGE_BLOCKS,
    FakeBeadsClient,
    IssueDraft,
    make_beads_client,
)
from livespec_orchestrator_beads_fabro.commands.context import item_context, main
from livespec_orchestrator_beads_fabro.errors import WorkItemNotFoundError
from livespec_orchestrator_beads_fabro.types import StoreConfig

if TYPE_CHECKING:
    from pathlib import Path

_EPIC_ID = "bd-ib-ctx"
_CHILD_ID = "bd-ib-ctx.1"
_GRANDCHILD_ID = "bd-ib-ctx.1.1"
_EDGE_CHILD_ID = "bd-ib-ctxedge"
_BLOCKER_ID = "bd-ib-ctxblocker"
_SLUG = "context-primitive"
_ENVELOPE_FIELDS = (
    "subject",
    "epic",
    "comments",
    "children",
    "dependencies",
    "next_action",
    "research",
    "spec",
)


def _config() -> StoreConfig:
    return StoreConfig(
        tenant="livespec-impl-beads",
        prefix="bd-ib",
        server_user="livespec-impl-beads",
        database="livespec-impl-beads",
        bd_path="bd",
        fake=True,
    )


def _fake() -> FakeBeadsClient:
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


def _seed_tenant(*, project_root: Path) -> None:
    """Seed the fixture tenant every case in this module reads.

    Deliberately carries BOTH child linkages — a dotted-id child and an
    edge-linked one — plus a grandchild, because a union enumeration that
    silently dropped either would still return a plausible non-empty list.
    """
    client = _fake()
    _ = client.create_issue(
        draft=_draft(
            issue_id=_EPIC_ID,
            issue_type="epic",
            metadata={
                "plan_slug": _SLUG,
                "next_action": {
                    "kind": "impl",
                    "ref": _CHILD_ID,
                    "text": "Dispatch the context loader slice.",
                },
            },
            spec_id=f"plan:{_SLUG}",
        )
    )
    _ = client.create_issue(draft=_draft(issue_id=_BLOCKER_ID))
    _ = client.create_issue(draft=_draft(issue_id=_CHILD_ID, spec_id="obligation-context-envelope"))
    _ = client.create_issue(
        draft=_draft(issue_id=_GRANDCHILD_ID, spec_id="obligation-context-json")
    )
    _ = client.create_issue(draft=_draft(issue_id=_EDGE_CHILD_ID, parent_id=_EPIC_ID))
    client.add_dependency(from_id=_EPIC_ID, to_id=_BLOCKER_ID, edge_type=EDGE_BLOCKS)
    client.add_dependency(from_id=_CHILD_ID, to_id=_BLOCKER_ID, edge_type=EDGE_BLOCKS)
    client.add_comment(issue_id=_EPIC_ID, body="Charter agreed with the maintainer.")
    client.add_comment(issue_id=_EPIC_ID, body="Dispatch factory: hp.")
    client.add_comment(issue_id=_CHILD_ID, body="Rider: union both child linkages.")
    _ = (project_root / ".livespec.jsonc").write_text(
        '{"livespec-orchestrator-beads-fabro": {"connection": {"prefix": "bd-ib"}}}',
        encoding="utf-8",
    )
    plan_dir = project_root / "plan" / _SLUG
    _ = (plan_dir / "research").mkdir(parents=True)
    _ = (plan_dir / "associated_work_item_id").write_text(f"{_EPIC_ID}\n", encoding="utf-8")
    _ = (plan_dir / "research" / "001-charter.md").write_text("charter\n", encoding="utf-8")


def _emitted(*, captured: str) -> dict[str, Any]:
    payload = json.loads(captured)
    assert isinstance(payload, dict)
    return payload


def test_json_envelope_for_an_epic_id_populates_every_field(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed_tenant(project_root=tmp_path)

    rc = main(argv=[_EPIC_ID, "--json", "--project-root", str(tmp_path)])

    envelope = _emitted(captured=capsys.readouterr().out)
    assert rc == 0
    assert tuple(sorted(envelope)) == tuple(sorted(_ENVELOPE_FIELDS))
    # Every field carries content — an all-empty envelope is exactly what the
    # not-found refusal exists to keep out of a resuming session's hands.
    assert all(envelope[field] for field in _ENVELOPE_FIELDS)
    assert envelope["epic"]["id"] == _EPIC_ID
    assert [comment["text"] for comment in envelope["comments"]] == [
        "Charter agreed with the maintainer.",
        "Dispatch factory: hp.",
    ]
    assert [child["id"] for child in envelope["children"]] == [
        _CHILD_ID,
        _GRANDCHILD_ID,
        _EDGE_CHILD_ID,
    ]
    assert envelope["dependencies"] == [{"depends_on_id": _BLOCKER_ID, "type": EDGE_BLOCKS}]
    assert envelope["next_action"] == {
        "kind": "impl",
        "ref": _CHILD_ID,
        "text": "Dispatch the context loader slice.",
    }
    assert envelope["research"]["directory"] == f"plan/{_SLUG}"
    assert envelope["research"]["files"] == [f"plan/{_SLUG}/research/001-charter.md"]
    assert envelope["research"]["anchors_this_epic"] is True
    assert envelope["spec"] == {
        "plan_anchor": _SLUG,
        "citations": ["obligation-context-envelope", "obligation-context-json"],
    }


def test_json_envelope_for_a_child_id_carries_the_same_shape(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed_tenant(project_root=tmp_path)

    rc = main(argv=[_CHILD_ID, "--json", "--project-root", str(tmp_path)])

    envelope = _emitted(captured=capsys.readouterr().out)
    assert rc == 0
    assert tuple(sorted(envelope)) == tuple(sorted(_ENVELOPE_FIELDS))
    assert all(envelope[field] for field in _ENVELOPE_FIELDS)
    assert envelope["subject"] == {
        "id": _CHILD_ID,
        "is_plan_epic": False,
        "plan_epic_id": _EPIC_ID,
        "plan_slug": _SLUG,
    }
    assert envelope["epic"]["id"] == _CHILD_ID
    assert [child["id"] for child in envelope["children"]] == [_GRANDCHILD_ID]
    # next_action and research describe the PLAN, which a leaf slice does not
    # carry itself — they resolve through the child's plan epic.
    assert envelope["next_action"]["ref"] == _CHILD_ID
    assert envelope["research"]["slug"] == _SLUG


def test_a_plan_slug_resolves_the_same_envelope_as_its_epic_id(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed_tenant(project_root=tmp_path)

    assert main(argv=[_SLUG, "--json", "--project-root", str(tmp_path)]) == 0
    by_slug = capsys.readouterr().out
    assert main(argv=[_EPIC_ID, "--json", "--project-root", str(tmp_path)]) == 0

    assert by_slug == capsys.readouterr().out


def test_two_invocations_are_byte_identical_and_leave_the_store_unmodified(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed_tenant(project_root=tmp_path)
    before = json.dumps(_fake().list_issues(), sort_keys=True)

    assert main(argv=[_EPIC_ID, "--json", "--project-root", str(tmp_path)]) == 0
    first = capsys.readouterr().out
    assert main(argv=[_EPIC_ID, "--json", "--project-root", str(tmp_path)]) == 0
    second = capsys.readouterr().out

    assert first == second
    assert json.dumps(_fake().list_issues(), sort_keys=True) == before


def test_an_absent_key_refuses_naming_it_rather_than_emitting_an_empty_envelope(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed_tenant(project_root=tmp_path)

    rc = main(argv=["bd-ib-nosuchthing", "--json", "--project-root", str(tmp_path)])

    captured = capsys.readouterr()
    assert rc == 3
    assert captured.out == ""
    assert "bd-ib-nosuchthing" in captured.err


def test_human_rendering_summarizes_the_same_envelope(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed_tenant(project_root=tmp_path)

    rc = main(argv=[_EPIC_ID, "--project-root", str(tmp_path)])

    captured = capsys.readouterr()
    assert rc == 0
    assert f"subject: {_EPIC_ID} (plan_slug={_SLUG})" in captured.out
    assert "comments: 2" in captured.out
    assert f"children: {_CHILD_ID}, {_GRANDCHILD_ID}, {_EDGE_CHILD_ID}" in captured.out
    assert "dependencies: 1" in captured.out
    assert f"next_action: impl {_CHILD_ID} — Dispatch the context loader slice." in captured.out
    assert f"research: plan/{_SLUG}" in captured.out
    assert "spec: obligation-context-envelope, obligation-context-json" in captured.out


def test_human_rendering_names_the_absent_fields_of_a_bare_item(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _ = _fake().create_issue(draft=_draft(issue_id=_BLOCKER_ID))
    _ = (tmp_path / ".livespec.jsonc").write_text(
        '{"livespec-orchestrator-beads-fabro": {"connection": {"prefix": "bd-ib"}}}',
        encoding="utf-8",
    )

    rc = main(argv=[_BLOCKER_ID, "--project-root", str(tmp_path)])

    captured = capsys.readouterr()
    assert rc == 0
    assert "children: (none)" in captured.out
    assert "next_action: (none)" in captured.out
    assert "research: (none)" in captured.out
    assert "spec: (none)" in captured.out


def test_item_context_raises_the_typed_not_found_error(tmp_path: Path) -> None:
    _seed_tenant(project_root=tmp_path)

    with pytest.raises(WorkItemNotFoundError) as excinfo:
        _ = item_context(config=_config(), project_root=tmp_path, key="bd-ib-absent")

    assert excinfo.value.item_id == "bd-ib-absent"
