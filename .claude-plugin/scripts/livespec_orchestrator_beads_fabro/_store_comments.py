"""Comment sidecar reads and appends for the beads-backed store."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from livespec_orchestrator_beads_fabro._beads_client import make_beads_client

if TYPE_CHECKING:
    from livespec_orchestrator_beads_fabro.types import StoreConfig

__all__: list[str] = [
    "WorkItemComment",
    "append_work_item_comment",
    "read_work_item_comments",
]


@dataclass(frozen=True, kw_only=True)
class WorkItemComment:
    """One comment on a work-item, mapped from a `bd comments` record.

    Comments are operator RIDERS appended to an item after filing (e.g.
    pre-authorizations, scope amendments). They are deliberately NOT a
    `WorkItem` field — the work-item record schema is codified by
    SPECIFICATION/contracts.md and comments are a beads-native sidecar,
    read on demand by the Dispatcher to fold into the dispatch goal.
    """

    text: str
    author: str | None
    created_at: str | None
    comment_id: str | None = None


def read_work_item_comments(
    *,
    path: StoreConfig,
    work_item_id: str,
) -> tuple[WorkItemComment, ...]:
    """Read the comments on one work-item, oldest-first.

    `bd show` carries only `comment_count` (never bodies), so this is a
    dedicated `bd comments <id> --json` read via the client seam.
    Fail-soft per record: an entry without a non-empty string `text` is
    skipped (it cannot brief anyone), and non-string `author` /
    `created_at` values map to None — one malformed comment must not
    blind the whole read.
    """
    client = make_beads_client(config=path)
    comments: list[WorkItemComment] = []
    for record in client.list_comments(issue_id=work_item_id):
        text_raw: object = record.get("text")
        if not isinstance(text_raw, str) or text_raw == "":
            continue
        comments.append(
            WorkItemComment(
                text=text_raw,
                author=_comment_field_str(value=record.get("author")),
                created_at=_comment_field_str(value=record.get("created_at")),
                comment_id=_comment_field_str(value=record.get("id")),
            )
        )
    return tuple(comments)


def append_work_item_comment(*, path: StoreConfig, work_item_id: str, body: str) -> None:
    """Append one comment to a work-item — the write half of the sidecar.

    Beads comments are APPEND-ONLY: `bd comments` offers neither an edit nor a
    delete verb, so a body that turns out to be unusable can only be superseded
    by a further comment, never repaired. Grading a body is therefore the
    CALLER's obligation and has to happen before this call rather than inside
    it, because what counts as unusable depends on where the body is bound —
    the goal brief, a handoff export, a recurrence bump.
    """
    make_beads_client(config=path).add_comment(issue_id=work_item_id, body=body)


def _comment_field_str(*, value: object) -> str | None:
    """Map a raw comment field onto `str | None` (non-strings drop to None).

    Deliberately laxer than the issue-record `_optional_str` (which
    RAISES on a non-string): a malformed comment sidecar field fails
    soft, because a rider read must never blind the dispatch.
    """
    return value if isinstance(value, str) else None
