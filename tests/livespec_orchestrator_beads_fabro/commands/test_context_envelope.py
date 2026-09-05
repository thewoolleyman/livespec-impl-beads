"""The context envelope's assembly rules, exercised at their own seam.

`test_context.py` drives the whole primitive through its CLI. This module
covers the assembly decisions that CLI cannot reach from a well-formed
tenant: the sparse-record tolerances beads' `omitempty` encoding produces, the
untagged plan epic that still carries a `plan:<slug>` anchor marker, the
archived plan directory, and the ancestor walk that skips a parent carrying no
plan slug.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from livespec_orchestrator_beads_fabro.commands._context_envelope import (
    child_ids_of,
    dependency_edges,
    plan_slug_of,
    record_index,
    record_metadata,
    research_entry,
    resolve_subject,
)

if TYPE_CHECKING:
    from pathlib import Path

_EPIC_ID = "bd-ib-env"
_SLUG = "envelope-topic"


def _record(*, issue_id: str, **fields: Any) -> dict[str, Any]:
    return {"id": issue_id, **fields}


def test_metadata_of_a_record_carrying_none_is_the_empty_mapping() -> None:
    """Beads omits an empty metadata object entirely rather than emitting `{}`."""
    assert record_metadata(record=_record(issue_id=_EPIC_ID)) == {}
    assert record_metadata(record=_record(issue_id=_EPIC_ID, metadata=None)) == {}


def test_plan_slug_falls_back_to_the_anchor_marker_when_the_tag_is_absent() -> None:
    """The `plan:<slug>` marker predates the metadata tag and still stands."""
    assert plan_slug_of(record=_record(issue_id=_EPIC_ID, spec_id=f"plan:{_SLUG}")) == _SLUG
    assert (
        plan_slug_of(record=_record(issue_id=_EPIC_ID, metadata={"plan_slug": ""}, spec_id=None))
        is None
    )
    assert plan_slug_of(record=_record(issue_id=_EPIC_ID, spec_id="plan:")) is None
    assert plan_slug_of(record=_record(issue_id=_EPIC_ID, spec_id="obligation-x")) is None


def test_dependency_edges_tolerate_an_absent_or_ragged_array() -> None:
    assert dependency_edges(record=_record(issue_id=_EPIC_ID)) == []
    assert dependency_edges(
        record=_record(
            issue_id=_EPIC_ID,
            dependencies=["not-an-edge", {"depends_on_id": "b", "type": "blocks"}],
        )
    ) == [{"depends_on_id": "b", "type": "blocks"}]


def test_child_enumeration_ignores_a_link_to_a_record_the_read_never_returned() -> None:
    """A dangling id is not projected: the envelope only carries records it has."""
    records = [_record(issue_id=_EPIC_ID), _record(issue_id=f"{_EPIC_ID}.1")]

    assert child_ids_of(records=records, epic_id=_EPIC_ID) == (f"{_EPIC_ID}.1",)


def test_record_index_drops_a_record_carrying_no_id() -> None:
    assert sorted(record_index(records=[_record(issue_id=_EPIC_ID), {"title": "no id"}])) == [
        _EPIC_ID
    ]


def test_the_ancestor_walk_skips_a_parent_that_carries_no_plan_slug() -> None:
    """A grandchild resolves to the epic, not to the intermediate slice."""
    records = [
        _record(issue_id=_EPIC_ID, issue_type="epic", metadata={"plan_slug": _SLUG}),
        _record(issue_id=f"{_EPIC_ID}.1", issue_type="task"),
        _record(issue_id=f"{_EPIC_ID}.1.1", issue_type="task"),
    ]

    assert resolve_subject(records=records, key=f"{_EPIC_ID}.1.1") == (
        f"{_EPIC_ID}.1.1",
        _EPIC_ID,
    )


def test_an_orphan_leaf_resolves_to_itself_as_its_own_plan_epic() -> None:
    records = [_record(issue_id="bd-ib-orphan", issue_type="task")]

    assert resolve_subject(records=records, key="bd-ib-orphan") == (
        "bd-ib-orphan",
        "bd-ib-orphan",
    )


def test_a_slug_carried_by_two_epics_resolves_to_the_lowest_id_every_time() -> None:
    records = [
        _record(issue_id="bd-ib-zzz", issue_type="epic", metadata={"plan_slug": _SLUG}),
        _record(issue_id="bd-ib-aaa", issue_type="epic", metadata={"plan_slug": _SLUG}),
    ]

    assert resolve_subject(records=records, key=_SLUG) == ("bd-ib-aaa", "bd-ib-aaa")


def test_research_resolves_an_archived_plan_directory(tmp_path: Path) -> None:
    directory = tmp_path / "plan" / "archive" / _SLUG
    _ = directory.mkdir(parents=True)
    _ = (directory / "associated_work_item_id").write_text("unassigned\n", encoding="utf-8")

    entry = research_entry(project_root=tmp_path, slug=_SLUG, epic_id=_EPIC_ID)

    assert entry == {
        "slug": _SLUG,
        "directory": f"plan/archive/{_SLUG}",
        "anchor": "unassigned",
        "anchors_this_epic": False,
        "files": [],
    }


def test_research_reports_a_directory_carrying_no_anchor_file(tmp_path: Path) -> None:
    """An anchor-less directory is REPORTED, not hidden — the gap is the finding."""
    _ = (tmp_path / "plan" / _SLUG).mkdir(parents=True)

    entry = research_entry(project_root=tmp_path, slug=_SLUG, epic_id=_EPIC_ID)

    assert entry is not None
    assert entry["anchor"] is None
    assert entry["anchors_this_epic"] is False


def test_research_is_absent_when_the_slug_names_no_directory(tmp_path: Path) -> None:
    assert research_entry(project_root=tmp_path, slug=_SLUG, epic_id=_EPIC_ID) is None
    assert research_entry(project_root=tmp_path, slug=None, epic_id=_EPIC_ID) is None
