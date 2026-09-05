"""Deterministic assembly of one item's full context envelope.

The read side of the `context` contract in SPECIFICATION/contracts.md. Given
a `plan_slug` or a work-item id, this module resolves ONE subject out of a
single `bd list --status all` read and assembles everything a session needs to
resume that item's plan without any chat history: the record itself, its
comments, its children, its dependency edges, the plan's typed `next_action`,
the research directory the `associated_work_item_id` anchor points at, and the
spec clauses the item and its children cite.

TWO RESOLUTIONS HAPPEN HERE, AND THEY ARE DELIBERATELY DIFFERENT. The SUBJECT
is whatever the caller named — an epic or a leaf work-item — and the record,
comment, child and dependency fields all describe it. The PLAN EPIC is the
epic that owns the plan the subject belongs to, which for a child is its
parent; `next_action` and `research` describe THAT, because a leaf slice
carries neither and a caller asking "what happens next" means the plan's next
step, not the slice's absence of one.

CHILD ENUMERATION UNIONS BOTH LINKAGES. Beads links a child to its epic two
ways and each hand-rolled filter is blind to one of them, so an
edge-only reading silently omits every dotted-id child and an id-prefix
reading silently omits every edge child. `_plan_child_edges` already owns that
union; this module composes it rather than re-deriving it.

EVERY LIST IS SORTED AND EVERY MAPPING IS DENSE. The contract requires two
invocations against an unchanged store to emit byte-identical envelopes, and
beads records are `omitempty`-sparse — a record holding no labels omits the
key rather than carrying an empty list — so a projection that passed records
through verbatim would vary its own key set with the data. Each projection
below names its keys explicitly and fills an absent one with `None`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from livespec_orchestrator_beads_fabro._beads_client import EDGE_PARENT_CHILD
from livespec_orchestrator_beads_fabro.commands._plan_anchor import (
    PLAN_HINT_PREFIX,
    is_plan_anchor,
    is_spec_commitment,
)
from livespec_orchestrator_beads_fabro.commands._plan_child_edges import (
    plan_child_ids_from_dependencies,
    plan_child_ids_from_id_hierarchy,
)
from livespec_orchestrator_beads_fabro.commands._plan_identity import (
    PLAN_ANCHOR_FILENAME,
    PLAN_SLUG_METADATA_KEY,
)
from livespec_orchestrator_beads_fabro.commands._plan_next_action import (
    NEXT_ACTION_METADATA_KEY,
    parse_next_action,
)

if TYPE_CHECKING:
    from pathlib import Path

    from livespec_orchestrator_beads_fabro._beads_client import BeadsClient, BeadsRecord

__all__: list[str] = [
    "build_envelope",
    "child_ids_of",
    "dependency_edges",
    "plan_slug_of",
    "record_index",
    "record_metadata",
    "research_entry",
    "resolve_subject",
]

_PLAN_DIR = "plan"
_ARCHIVE_DIR = "archive"
_RESEARCH_DIR = "research"
_EPIC_TYPE = "epic"

_RECORD_FIELDS: tuple[str, ...] = (
    "id",
    "issue_type",
    "status",
    "title",
    "description",
    "assignee",
    "created_at",
    "labels",
    "spec_id",
    "acceptance_criteria",
    "notes",
)
_CHILD_FIELDS: tuple[str, ...] = ("id", "issue_type", "status", "title")
_COMMENT_FIELDS: tuple[str, ...] = ("author", "created_at", "text")


def resolve_subject(*, records: list[BeadsRecord], key: str) -> tuple[str, str] | None:
    """Resolve one `plan_slug` or work-item id to `(subject_id, plan_epic_id)`.

    An id wins over a slug: ids are minted and slugs are derived, so a slug
    that happens to equal an id names that record either way. Returns None
    when the key names nothing, which is what the CLI turns into the
    not-found refusal — never an empty envelope.
    """
    index = record_index(records=records)
    subject = index.get(key)
    if subject is None:
        subject = _record_by_plan_slug(index=index, slug=key)
    if subject is None:
        return None
    subject_id = cast("str", subject["id"])
    return subject_id, _plan_epic_id(index=index, subject=subject)


def build_envelope(
    *,
    client: BeadsClient,
    project_root: Path,
    records: list[BeadsRecord],
    subject_id: str,
    plan_epic_id: str,
) -> dict[str, Any]:
    """Assemble the whole context envelope for one already-resolved subject."""
    index = record_index(records=records)
    subject = index[subject_id]
    plan_epic = index[plan_epic_id]
    slug = plan_slug_of(record=plan_epic)
    child_ids = child_ids_of(records=records, epic_id=subject_id)
    return {
        "subject": {
            "id": subject_id,
            "is_plan_epic": subject_id == plan_epic_id,
            "plan_epic_id": plan_epic_id,
            "plan_slug": slug,
        },
        "epic": _project(record=subject, fields=_RECORD_FIELDS),
        "comments": [
            _project(record=comment, fields=_COMMENT_FIELDS)
            for comment in client.list_comments(issue_id=subject_id)
        ],
        "children": [
            _project(record=index[child_id], fields=_CHILD_FIELDS) for child_id in child_ids
        ],
        "dependencies": dependency_edges(record=subject),
        "next_action": _next_action(record=plan_epic),
        "research": research_entry(project_root=project_root, slug=slug, epic_id=plan_epic_id),
        "spec": _spec_entry(index=index, subject=subject, child_ids=child_ids),
    }


def record_index(*, records: list[BeadsRecord]) -> dict[str, BeadsRecord]:
    """Index a tenant read by issue id, dropping any record carrying no id."""
    return {
        cast("str", record["id"]): record for record in records if isinstance(record.get("id"), str)
    }


def record_metadata(*, record: BeadsRecord) -> dict[str, Any]:
    """Return a record's metadata mapping, tolerating the key's absence."""
    metadata = record.get("metadata")
    if not isinstance(metadata, dict):
        return {}
    return dict(cast("dict[str, Any]", metadata))


def plan_slug_of(*, record: BeadsRecord) -> str | None:
    """Return an epic's plan slug from its metadata tag, else its anchor marker.

    The metadata tag is the ratified carrier, but the `plan:<slug>` marker in
    the overloaded spec-id column predates it and still stands on untagged
    epics, so reading only the tag would report a live plan as slug-less.
    """
    tagged = record_metadata(record=record).get(PLAN_SLUG_METADATA_KEY)
    if isinstance(tagged, str) and tagged != "":
        return tagged
    spec_id = record.get("spec_id")
    if not isinstance(spec_id, str) or not is_plan_anchor(spec_id=spec_id):
        return None
    marker = spec_id.removeprefix(PLAN_HINT_PREFIX)
    return marker if marker != "" else None


def child_ids_of(*, records: list[BeadsRecord], epic_id: str) -> tuple[str, ...]:
    """Return the union of edge-linked and dotted-id children, sorted."""
    linked = plan_child_ids_from_dependencies(
        records=records,
        epic_id=epic_id,
    ) | plan_child_ids_from_id_hierarchy(records=records, epic_id=epic_id)
    return tuple(sorted(linked & frozenset(record_index(records=records))))


def dependency_edges(*, record: BeadsRecord) -> list[dict[str, Any]]:
    """Return every dependency edge of one record, sorted and dense.

    The whole heterogeneous array is carried, not the `blocks` subset: a
    reader resuming a plan needs to see the parent-child linkage and the
    supersedes edges as well as the blockers, and the edge type is the field
    that discriminates them.
    """
    dependencies = record.get("dependencies")
    if not isinstance(dependencies, list):
        return []
    edges: list[dict[str, Any]] = [
        {
            "depends_on_id": cast("dict[str, Any]", edge).get("depends_on_id"),
            "type": cast("dict[str, Any]", edge).get("type"),
        }
        for edge in cast("list[Any]", dependencies)
        if isinstance(edge, dict)
    ]
    return sorted(edges, key=lambda edge: (str(edge["depends_on_id"]), str(edge["type"])))


def research_entry(
    *,
    project_root: Path,
    slug: str | None,
    epic_id: str,
) -> dict[str, Any] | None:
    """Return the research directory the plan's anchor resolves, else None.

    The anchor is `plan/<slug>/associated_work_item_id`, and an archived plan
    keeps the same layout one level down under `plan/archive/`, so both are
    tried. The anchor is REPORTED rather than gated on: a directory whose
    anchor still reads `unassigned`, or names another epic, is exactly the
    drift a resuming session needs shown, and refusing to report it would
    hide the one file that explains the mismatch.
    """
    if slug is None:
        return None
    for base in (project_root / _PLAN_DIR, project_root / _PLAN_DIR / _ARCHIVE_DIR):
        directory = base / slug
        if not directory.is_dir():
            continue
        anchor = directory / PLAN_ANCHOR_FILENAME
        return {
            "slug": slug,
            "directory": directory.relative_to(project_root).as_posix(),
            "anchor": anchor.read_text(encoding="utf-8").strip() if anchor.is_file() else None,
            "anchors_this_epic": anchor.is_file()
            and anchor.read_text(encoding="utf-8").strip() == epic_id,
            "files": _research_files(project_root=project_root, directory=directory),
        }
    return None


def _research_files(*, project_root: Path, directory: Path) -> list[str]:
    research = directory / _RESEARCH_DIR
    if not research.is_dir():
        return []
    return sorted(
        path.relative_to(project_root).as_posix() for path in research.rglob("*") if path.is_file()
    )


def _spec_entry(
    *,
    index: dict[str, BeadsRecord],
    subject: BeadsRecord,
    child_ids: tuple[str, ...],
) -> dict[str, Any]:
    """Return the spec clauses the subject and its children cite.

    The spec-id column is OVERLOADED — it carries both a genuine clause
    commitment and the `plan:<slug>` plan-anchor marker — so the two are asked
    for by name through `_plan_anchor` rather than by testing the field's
    presence, which would report every plan epic as citing a spec clause.
    A plan epic's own citations live on its children, which is why the child
    set is unioned in: an epic that cites nothing itself still resumes with
    the clauses its slices commit to.
    """
    candidates = [subject, *[index[child_id] for child_id in child_ids]]
    citations = {
        spec_id
        for record in candidates
        for spec_id in (record.get("spec_id"),)
        if isinstance(spec_id, str) and is_spec_commitment(spec_id=spec_id)
    }
    return {
        "plan_anchor": plan_slug_of(record=subject),
        "citations": sorted(citations),
    }


def _next_action(*, record: BeadsRecord) -> dict[str, Any] | None:
    action = parse_next_action(
        value=record_metadata(record=record).get(NEXT_ACTION_METADATA_KEY),
    )
    if action is None:
        return None
    return {"kind": action.kind, "ref": action.ref, "text": action.text}


def _project(*, record: BeadsRecord, fields: tuple[str, ...]) -> dict[str, Any]:
    return {field: record.get(field) for field in fields}


def _record_by_plan_slug(*, index: dict[str, BeadsRecord], slug: str) -> BeadsRecord | None:
    """Return the LOWEST-id record carrying `slug`, or None when none does.

    Ties are broken by id rather than by iteration order so a tenant that has
    somehow tagged two epics with one slug still emits the same envelope on
    every invocation. The duplicate itself is the plan-record conformance
    checks' finding to report, not this reader's.
    """
    matches = [record for record in index.values() if plan_slug_of(record=record) == slug]
    if not matches:
        return None
    return sorted(matches, key=lambda record: cast("str", record["id"]))[0]


def _plan_epic_id(*, index: dict[str, BeadsRecord], subject: BeadsRecord) -> str:
    """Return the epic owning the subject's plan — the subject itself, or its parent."""
    subject_id = cast("str", subject["id"])
    if plan_slug_of(record=subject) is not None or subject.get("issue_type") == _EPIC_TYPE:
        return subject_id
    for candidate in _parent_ids(index=index, subject=subject):
        if plan_slug_of(record=index[candidate]) is not None:
            return candidate
    return subject_id


def _parent_ids(*, index: dict[str, BeadsRecord], subject: BeadsRecord) -> tuple[str, ...]:
    """Return the subject's candidate parents, from BOTH linkages, nearest first.

    The dotted-id ancestry is walked from the nearest prefix outward so a
    grandchild resolves to its own epic rather than to the root of the id
    space, and the edge-linked parents follow so a child carrying no dotted id
    still resolves.
    """
    subject_id = cast("str", subject["id"])
    hierarchy = tuple(
        subject_id.rsplit(".", split)[0] for split in range(1, subject_id.count(".") + 1)
    )
    edges = tuple(
        sorted(
            edge["depends_on_id"]
            for edge in dependency_edges(record=subject)
            if edge["type"] == EDGE_PARENT_CHILD and isinstance(edge["depends_on_id"], str)
        )
    )
    return tuple(
        dict.fromkeys(candidate for candidate in (*hierarchy, *edges) if candidate in index)
    )
