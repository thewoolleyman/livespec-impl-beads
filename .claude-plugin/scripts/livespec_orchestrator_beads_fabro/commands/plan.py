"""Plan-thread primitives backed by ledger-held handoff comments."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from livespec_runtime.work_items.rank import key_between

from livespec_orchestrator_beads_fabro._beads_client import make_beads_client
from livespec_orchestrator_beads_fabro._ids import new_work_item_id
from livespec_orchestrator_beads_fabro.store import append_work_item, read_work_item_comments
from livespec_orchestrator_beads_fabro.types import WorkItem

if TYPE_CHECKING:
    from livespec_orchestrator_beads_fabro.types import StoreConfig

__all__: list[str] = [
    "PlanArchiveRefusedError",
    "PlanTimelineEntry",
    "append_handoff",
    "archive_thread",
    "create_thread",
    "read_timeline",
    "record_scope_event",
]

_PLAN_DIR = "plan"
_ARCHIVE_DIR = "archive"
_PLAN_HANDOFF_PREFIX = "plan-handoff-entry"
_PLAN_SCOPE_PREFIX = "plan-scope-event"
_RESEARCH_DIR = "research"


class PlanArchiveRefusedError(Exception):
    """Expected refusal raised when a plan thread cannot be archived."""

    @classmethod
    def missing_completeness_review(cls) -> PlanArchiveRefusedError:
        return cls("independent completeness-review evidence is required")

    @classmethod
    def undisposed_children(cls, *, child_ids: list[str]) -> PlanArchiveRefusedError:
        return cls(f"undisposed child work-items: {', '.join(child_ids)}")


@dataclass(frozen=True, kw_only=True)
class PlanTimelineEntry:
    """One parsed plan-epic timeline entry."""

    body: str
    author: str
    created_at: str


def create_thread(  # noqa: PLR0913 — package primitive mirrors the plan-create inputs.
    *,
    project_root: Path,
    config: StoreConfig,
    slug: str,
    title: str,
    research_filename: str,
    research_text: str,
    now: str,
) -> dict[str, str]:
    """Create a plan thread with one research note and one ledger epic anchor."""
    topic_dir = project_root / _PLAN_DIR / slug
    research_path = topic_dir / _RESEARCH_DIR / research_filename
    research_path.parent.mkdir(parents=True, exist_ok=False)
    _ = research_path.write_text(research_text, encoding="utf-8")
    epic = WorkItem(
        id=new_work_item_id(prefix=config.prefix),
        type="epic",
        status="backlog",
        title=title,
        description=f"Plan thread anchor for plan/{slug}.",
        origin="freeform",
        gap_id=None,
        rank=key_between(a=None, b=None),
        assignee=None,
        depends_on=(),
        captured_at=now,
        resolution=None,
        reason=None,
        audit=None,
        superseded_by=None,
        spec_commitment_hint=f"plan:{slug}",
        notes=f"plan_slug={slug}",
    )
    append_work_item(path=config, item=epic)
    _tag_epic_anchor(config=config, epic_id=epic.id, slug=slug)
    return {
        "epic_id": epic.id,
        "research_path": research_path.relative_to(project_root).as_posix(),
    }


def append_handoff(
    *,
    config: StoreConfig,
    epic_id: str,
    body: str,
    author: str,
    now: str,
) -> None:
    """Append one handoff entry to the plan epic's ledger comments."""
    client = make_beads_client(config=config)
    client.add_comment(
        issue_id=epic_id,
        body=_comment_body(prefix=_PLAN_HANDOFF_PREFIX, author=author, now=now, body=body),
    )


def record_scope_event(
    *,
    config: StoreConfig,
    epic_id: str,
    requirements: tuple[str, ...],
    deferrals: tuple[str, ...],
    author: str,
    now: str,
) -> None:
    """Record scoped requirements and explicit deferrals before child admission."""
    client = make_beads_client(config=config)
    client.add_comment(
        issue_id=epic_id,
        body=_comment_body(
            prefix=_PLAN_SCOPE_PREFIX,
            author=author,
            now=now,
            body=_scope_body(requirements=requirements, deferrals=deferrals),
        ),
    )


def read_timeline(*, config: StoreConfig, epic_id: str) -> tuple[PlanTimelineEntry, ...]:
    """Read plan-epic handoff comments oldest-first."""
    entries: list[PlanTimelineEntry] = []
    for comment in read_work_item_comments(path=config, work_item_id=epic_id):
        if not comment.text.startswith((_PLAN_HANDOFF_PREFIX, _PLAN_SCOPE_PREFIX)):
            continue
        entries.append(_parse_entry(text=comment.text))
    return tuple(entries)


def archive_thread(
    *,
    project_root: Path,
    config: StoreConfig,
    slug: str,
    epic_id: str,
    completeness_review_comment_id: str | None,
) -> dict[str, str]:
    """Archive a thread after child-disposition and completeness-review gates pass."""
    if completeness_review_comment_id is None:
        raise PlanArchiveRefusedError.missing_completeness_review()
    client = make_beads_client(config=config)
    undisposed = sorted(
        record["id"]
        for record in client.children(parent_id=epic_id)
        if record.get("status") != "closed" and isinstance(record.get("id"), str)
    )
    if undisposed:
        raise PlanArchiveRefusedError.undisposed_children(child_ids=undisposed)
    source = project_root / _PLAN_DIR / slug
    archive = project_root / _PLAN_DIR / _ARCHIVE_DIR / slug
    archive.parent.mkdir(parents=True, exist_ok=True)
    _ = source.rename(archive)
    client.add_comment(
        issue_id=epic_id,
        body=_comment_body(
            prefix=_PLAN_HANDOFF_PREFIX,
            author="plan-archive",
            now=completeness_review_comment_id,
            body=f"Archived after completeness review {completeness_review_comment_id}.",
        ),
    )
    client.close_issue(issue_id=epic_id, reason="plan archived")
    return {"archive_path": archive.relative_to(project_root).as_posix(), "epic_id": epic_id}


def _tag_epic_anchor(*, config: StoreConfig, epic_id: str, slug: str) -> None:
    client = make_beads_client(config=config)
    record = client.show_issue(issue_id=epic_id)
    metadata = dict(record["metadata"])
    metadata["plan_slug"] = slug
    client.update_issue(issue_id=epic_id, metadata=metadata)


def _comment_body(*, prefix: str, author: str, now: str, body: str) -> str:
    return f"{prefix}\nauthor: {author}\ntimestamp: {now}\n\n{body}"


def _parse_entry(*, text: str) -> PlanTimelineEntry:
    header, body = text.split("\n\n", maxsplit=1)
    lines = header.splitlines()
    return PlanTimelineEntry(
        body=body,
        author=lines[1].removeprefix("author: "),
        created_at=lines[2].removeprefix("timestamp: "),
    )


def _scope_body(*, requirements: tuple[str, ...], deferrals: tuple[str, ...]) -> str:
    requirement_lines = "\n".join(f"- {requirement}" for requirement in requirements)
    deferral_lines = "\n".join(f"- {deferral}" for deferral in deferrals)
    return f"Requirement carriers:\n{requirement_lines}\n\nExplicit deferrals:\n{deferral_lines}"
