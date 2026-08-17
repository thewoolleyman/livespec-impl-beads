"""Plan archive completeness-review evidence helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, TypedDict, cast

from typing_extensions import Unpack

from livespec_orchestrator_beads_fabro._beads_client import (
    EDGE_BLOCKS,
    EDGE_PARENT_CHILD,
    BeadsRecord,
    make_beads_client,
)

if TYPE_CHECKING:
    from livespec_orchestrator_beads_fabro._beads_client import BeadsClient
    from livespec_orchestrator_beads_fabro.types import StoreConfig

__all__: list[str] = [
    "ArchiveCompletenessReviewRequest",
    "CompletenessReviewLauncher",
    "archive_completeness_review_request",
    "blocking_dependency_ids",
    "has_blocks_edge_to_epic",
    "is_blocks_dependency_edge",
    "is_blocks_edge_to_epic",
    "record_completeness_review_evidence",
    "undisposed_plan_child_ids",
    "valid_completeness_review_evidence_id",
]

_PLAN_COMPLETENESS_REVIEW_PREFIX = "plan-completeness-review-evidence"
_TRUE = "true"


class CompletenessReviewEvidenceFields(TypedDict):
    """Keyword payload for a durable completeness-review evidence record."""

    evidence_id: str
    reviewer_identity: str
    separate_reviewer: bool
    attests_complete_requirement_coverage: bool
    body: str
    now: str


@dataclass(frozen=True, kw_only=True)
class ArchiveCompletenessReviewRequest:
    """Context handed to a fresh independent plan completeness reviewer."""

    project_root: Path
    slug: str
    epic_id: str
    child_ids: tuple[str, ...]
    research_paths: tuple[str, ...]


class CompletenessReviewLauncher(Protocol):
    """Callable seam that commissions one external completeness review."""

    def __call__(self, *, request: ArchiveCompletenessReviewRequest) -> str | None:
        """Launch the reviewer and return its durable evidence id, if any."""
        ...


def record_completeness_review_evidence(
    *,
    config: StoreConfig,
    epic_id: str,
    **evidence: Unpack[CompletenessReviewEvidenceFields],
) -> None:
    """Append a durable plan completeness-review evidence comment."""
    client = make_beads_client(config=config)
    client.add_comment(
        issue_id=epic_id,
        body=_evidence_comment_body(
            evidence_id=evidence["evidence_id"],
            reviewer_identity=evidence["reviewer_identity"],
            separate_reviewer=evidence["separate_reviewer"],
            attests_complete_requirement_coverage=evidence["attests_complete_requirement_coverage"],
            body=evidence["body"],
            now=evidence["now"],
        ),
    )


def archive_completeness_review_request(
    *,
    client: BeadsClient,
    project_root: Path,
    source: Path,
    slug: str,
    epic_id: str,
) -> ArchiveCompletenessReviewRequest:
    """Build the request context for a fresh archive completeness reviewer."""
    return ArchiveCompletenessReviewRequest(
        project_root=project_root,
        slug=slug,
        epic_id=epic_id,
        child_ids=_disposed_child_ids(client=client, epic_id=epic_id),
        research_paths=_research_paths(project_root=project_root, source=source),
    )


def undisposed_plan_child_ids(*, client: BeadsClient, epic_id: str) -> tuple[str, ...]:
    """Return sorted plan-child ids whose ledger status is not closed."""
    return tuple(
        sorted(record["id"] for record in _undisposed_plan_children(client=client, epic_id=epic_id))
    )


def valid_completeness_review_evidence_id(
    *,
    client: BeadsClient,
    epic_id: str,
    evidence_id: str | None,
    archive_actor: str,
) -> str | None:
    """Return `evidence_id` only when the ledger has a valid evidence comment."""
    if evidence_id is None:
        return None
    for comment in client.list_comments(issue_id=epic_id):
        text = comment.get("text")
        if not isinstance(text, str):
            continue
        fields = _evidence_fields(text=text)
        if not _is_valid_evidence(
            fields=fields,
            evidence_id=evidence_id,
            archive_actor=archive_actor,
        ):
            continue
        return evidence_id
    return None


def _undisposed_plan_children(*, client: BeadsClient, epic_id: str) -> list[BeadsRecord]:
    return [
        record
        for record in _plan_child_records(client=client, epic_id=epic_id)
        if _is_undisposed_plan_child(record=record)
    ]


def _plan_child_records(*, client: BeadsClient, epic_id: str) -> list[BeadsRecord]:
    records_by_id = {
        cast("str", record["id"]): record for record in client.children(parent_id=epic_id)
    }
    records = client.list_issues()
    linked_ids = _linked_child_ids_for_epic(records=records, epic_id=epic_id)
    for record in records:
        issue_id = record.get("id")
        if isinstance(issue_id, str) and issue_id in linked_ids:
            _ = records_by_id.setdefault(issue_id, record)
    return list(records_by_id.values())


def _disposed_child_ids(*, client: BeadsClient, epic_id: str) -> tuple[str, ...]:
    return tuple(
        sorted(
            record["id"]
            for record in _plan_child_records(client=client, epic_id=epic_id)
            if isinstance(record.get("id"), str) and record.get("status") == "closed"
        )
    )


def _research_paths(*, project_root: Path, source: Path) -> tuple[str, ...]:
    research_dir = source / "research"
    if not research_dir.is_dir():
        return ()
    return tuple(
        sorted(
            path.relative_to(project_root).as_posix()
            for path in research_dir.rglob("*")
            if path.is_file()
        )
    )


def _is_undisposed_plan_child(*, record: BeadsRecord) -> bool:
    issue_id = record.get("id")
    return isinstance(issue_id, str) and record.get("status") != "closed"


def _blocking_ids_for_epic(*, records: list[BeadsRecord], epic_id: str) -> frozenset[str]:
    for record in records:
        if record.get("id") == epic_id:
            return blocking_dependency_ids(record=record)
    return frozenset()


def _linked_child_ids_for_epic(*, records: list[BeadsRecord], epic_id: str) -> frozenset[str]:
    return frozenset(
        issue_id
        for record in records
        if isinstance(issue_id := record.get("id"), str)
        and _has_parent_child_edge_to_epic(record=record, epic_id=epic_id)
    ) | _blocking_ids_for_epic(records=records, epic_id=epic_id)


def _has_parent_child_edge_to_epic(*, record: BeadsRecord, epic_id: str) -> bool:
    dependencies = record.get("dependencies")
    if not isinstance(dependencies, list):
        return False
    typed_dependencies = cast("list[object]", dependencies)
    return any(
        _is_parent_child_edge_to_epic(edge=edge, epic_id=epic_id) for edge in typed_dependencies
    )


def _is_parent_child_edge_to_epic(*, edge: object, epic_id: str) -> bool:
    if not isinstance(edge, dict):
        return False
    typed_edge = cast("dict[str, Any]", edge)
    depends_on_id = typed_edge.get("depends_on_id")
    return typed_edge.get("type") == EDGE_PARENT_CHILD and depends_on_id == epic_id


def blocking_dependency_ids(*, record: BeadsRecord) -> frozenset[str]:
    """Return ids of records that block `record` through `blocks` dependencies."""
    dependencies = record.get("dependencies")
    if not isinstance(dependencies, list):
        return frozenset()
    typed_dependencies = cast("list[object]", dependencies)
    return frozenset(
        dependency_id
        for edge in typed_dependencies
        if (dependency_id := is_blocks_dependency_edge(edge=edge)) is not None
    )


def is_blocks_dependency_edge(*, edge: object) -> str | None:
    """Return the dependency id when one edge is a `blocks` dependency."""
    if not isinstance(edge, dict):
        return None
    typed_edge = cast("dict[str, Any]", edge)
    depends_on_id = typed_edge.get("depends_on_id")
    if typed_edge.get("type") != EDGE_BLOCKS or not isinstance(depends_on_id, str):
        return None
    return depends_on_id


def has_blocks_edge_to_epic(*, record: BeadsRecord, epic_id: str) -> bool:
    """Return whether `record` carries a legacy-shaped dependency on `epic_id`."""
    return epic_id in blocking_dependency_ids(record=record)


def is_blocks_edge_to_epic(*, edge: object, epic_id: str) -> bool:
    """Return whether one legacy-shaped dependency edge points at `epic_id`."""
    return is_blocks_dependency_edge(edge=edge) == epic_id


def _evidence_comment_body(
    *,
    evidence_id: str,
    reviewer_identity: str,
    separate_reviewer: bool,
    attests_complete_requirement_coverage: bool,
    body: str,
    now: str,
) -> str:
    separate = str(separate_reviewer).lower()
    coverage = str(attests_complete_requirement_coverage).lower()
    return (
        f"{_PLAN_COMPLETENESS_REVIEW_PREFIX}\n"
        f"evidence-id: {evidence_id}\n"
        f"reviewer-identity: {reviewer_identity}\n"
        f"separate-reviewer: {separate}\n"
        f"attests-complete-requirement-coverage: {coverage}\n"
        f"timestamp: {now}\n\n"
        f"{body}"
    )


def _evidence_fields(*, text: str) -> dict[str, str]:
    header = text.split("\n\n", maxsplit=1)[0]
    lines = header.splitlines()
    if not lines or lines[0] != _PLAN_COMPLETENESS_REVIEW_PREFIX:
        return {}
    fields: dict[str, str] = {}
    for line in lines[1:]:
        key, separator, value = line.partition(": ")
        if separator == "":
            return {}
        fields[key] = value
    return fields


def _is_valid_evidence(
    *,
    fields: dict[str, str],
    evidence_id: str,
    archive_actor: str,
) -> bool:
    reviewer_identity = fields.get("reviewer-identity")
    return (
        fields.get("evidence-id") == evidence_id
        and reviewer_identity not in (None, archive_actor)
        and fields.get("separate-reviewer") == _TRUE
        and fields.get("attests-complete-requirement-coverage") == _TRUE
    )
