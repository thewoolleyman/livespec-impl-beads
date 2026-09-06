"""Plan primitives backed by ledger-held handoff comments."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from livespec_orchestrator_beads_fabro._beads_client import make_beads_client
from livespec_orchestrator_beads_fabro.commands._plan_anchor import plan_anchor_epic
from livespec_orchestrator_beads_fabro.commands._plan_archive_gates import (
    PlanArchiveRefusedError,
    outside_plan_path_references,
)
from livespec_orchestrator_beads_fabro.commands._plan_archive_review import (
    ArchiveCompletenessReviewRequest,
    CompletenessReviewLauncher,
    archive_completeness_review_request,
    blocking_dependency_ids,
    is_blocks_dependency_edge,
    record_completeness_review_evidence,
    undisposed_plan_child_ids,
    valid_completeness_review_evidence_id,
)
from livespec_orchestrator_beads_fabro.commands._plan_disposition import (
    PlanDispositionRefusedError,
    close_plan_child,
    reparent_plan_child,
)
from livespec_orchestrator_beads_fabro.commands._plan_identity import (
    tag_epic_plan_slug,
    write_plan_anchor,
)
from livespec_orchestrator_beads_fabro.commands._plan_next_action import (
    NEXT_ACTION_KINDS,
    NextAction,
    ResumeDirective,
    resume_directive,
    set_next_action,
)
from livespec_orchestrator_beads_fabro.commands._plan_record_rate import (
    DEFAULT_DAILY_RECORD_THRESHOLD,
    PlanRecordRateWarning,
    plan_record_rate_warnings,
)
from livespec_orchestrator_beads_fabro.commands._plan_timeline import (
    PLAN_HANDOFF_PREFIX,
    PLAN_SCOPE_PREFIX,
    UNATTENDED_ENV_VAR,
    PlanTimelineEntry,
    handoff_timeline_findings,
    is_unattended_session,
    read_timeline,
    recorded_next_actions,
)
from livespec_orchestrator_beads_fabro.store import append_work_item

if TYPE_CHECKING:
    from livespec_orchestrator_beads_fabro._beads_client import BeadsClient, BeadsRecord
    from livespec_orchestrator_beads_fabro.types import StoreConfig

__all__: list[str] = [
    "DEFAULT_DAILY_RECORD_THRESHOLD",
    "NEXT_ACTION_KINDS",
    "UNATTENDED_ENV_VAR",
    "NextAction",
    "PlanArchiveRefusedError",
    "PlanDispositionRefusedError",
    "PlanRecordRateWarning",
    "PlanTimelineEntry",
    "ResumeDirective",
    "_blocking_dependency_ids",
    "_is_blocks_dependency_edge",
    "append_handoff",
    "append_supervisor_handoff",
    "archive_thread",
    "close_plan_child",
    "create_thread",
    "handoff_timeline_findings",
    "is_unattended_session",
    "plan_record_rate_warnings",
    "read_timeline",
    "record_completeness_review_evidence",
    "record_scope_event",
    "recorded_next_actions",
    "reparent_plan_child",
    "resume_directive",
    "set_next_action",
]

_PLAN_DIR = "plan"
_ARCHIVE_DIR = "archive"
_RESEARCH_DIR = "research"
_PLAN_ARCHIVE_ACTOR = "plan-archive"


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
    """Create a plan with one research note, one ledger epic, and its anchor."""
    topic_dir = project_root / _PLAN_DIR / slug
    research_path = topic_dir / _RESEARCH_DIR / research_filename
    # Write-once is enforced on the NOTE, not on its directory: an epic may
    # adopt a `plan/<slug>/` that already holds standalone research, so the
    # directory legitimately pre-exists while the note it adds may not. The
    # exclusive-create mode refuses that collision as the directory-level
    # `exist_ok=False` used to, without refusing the adoption.
    research_path.parent.mkdir(parents=True, exist_ok=True)
    with research_path.open("x", encoding="utf-8") as handle:
        _ = handle.write(research_text)
    epic = plan_anchor_epic(prefix=config.prefix, slug=slug, title=title, now=now)
    append_work_item(path=config, item=epic)
    _ = tag_epic_plan_slug(config=config, epic_id=epic.id, title=title, slug=slug)
    anchor_path = write_plan_anchor(project_root=project_root, slug=slug, epic_id=epic.id)
    return {
        "anchor_path": anchor_path.relative_to(project_root).as_posix(),
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
    next_action: NextAction,
) -> None:
    """Append one handoff entry AND update the epic's typed next_action.

    Per contracts.md's "Ledger-held handoff persistence": the next action is
    not carried by the comment. The entry holds rationale, warnings and
    pointers; the pointer to the next step is the typed metadata written here
    in the same call, so a handoff can never record a next step the resume
    path cannot see. `author` doubles as the `last_session` identity, because
    the session that signs the entry is the one that wrote the pointer.
    """
    client = make_beads_client(config=config)
    client.add_comment(
        issue_id=epic_id,
        body=_comment_body(prefix=PLAN_HANDOFF_PREFIX, author=author, now=now, body=body),
    )
    set_next_action(
        config=config,
        epic_id=epic_id,
        action=next_action,
        session=author,
        now=now,
    )


def append_supervisor_handoff(
    *,
    config: StoreConfig,
    epic_id: str,
    slug: str,
    body: str,
    now: str,
    next_action: NextAction,
) -> None:
    """Append one handoff entry authored as the plan's reserved supervisor literal.

    Per contracts.md's "Ledger-held handoff persistence": the supervisor
    role's `author:` field MUST be `<slug>-supervisor`, computed here rather
    than accepted as a caller-supplied string, mirroring `archive_thread`'s
    `author="plan-archive"` reservation.
    """
    append_handoff(
        config=config,
        epic_id=epic_id,
        body=body,
        author=f"{slug}-supervisor",
        now=now,
        next_action=next_action,
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
            prefix=PLAN_SCOPE_PREFIX,
            author=author,
            now=now,
            body=_scope_body(requirements=requirements, deferrals=deferrals),
        ),
    )


def archive_thread(
    *,
    project_root: Path,
    config: StoreConfig,
    slug: str,
    epic_id: str,
    completeness_review_comment_id: str | None,
    review_launcher: CompletenessReviewLauncher | None = None,
) -> dict[str, str]:
    """Archive a thread once the child, working-tree reference, and review gates pass.

    The working-tree gate sits between the two ledger gates deliberately.
    It is mechanical and cheap, like the child-disposition leg, so a plan
    the move would break refuses BEFORE a fresh independent reviewer is
    commissioned — and, decisively, before the epic is closed and stamped.
    """
    client = make_beads_client(config=config)
    undisposed = list(undisposed_plan_child_ids(client=client, epic_id=epic_id))
    if undisposed:
        raise PlanArchiveRefusedError.undisposed_children(child_ids=undisposed)
    referencing = outside_plan_path_references(project_root=project_root, slug=slug)
    if referencing:
        raise PlanArchiveRefusedError.outside_path_references(slug=slug, paths=referencing)
    source = project_root / _PLAN_DIR / slug
    evidence_id = _resolve_completeness_review_evidence(
        client=client,
        epic_id=epic_id,
        completeness_review_comment_id=completeness_review_comment_id,
        review_launcher=review_launcher,
        request=archive_completeness_review_request(
            client=client,
            project_root=project_root,
            source=source,
            slug=slug,
            epic_id=epic_id,
        ),
    )
    if evidence_id is None:
        raise PlanArchiveRefusedError.missing_completeness_review()
    archive = project_root / _PLAN_DIR / _ARCHIVE_DIR / slug
    archive.parent.mkdir(parents=True, exist_ok=True)
    _ = source.rename(archive)
    client.add_comment(
        issue_id=epic_id,
        body=_comment_body(
            prefix=PLAN_HANDOFF_PREFIX,
            author=_PLAN_ARCHIVE_ACTOR,
            now=_utc_now_iso(),
            body=f"Archived after completeness review {evidence_id}.",
        ),
    )
    client.close_issue(issue_id=epic_id, reason="plan archived")
    return {"archive_path": archive.relative_to(project_root).as_posix(), "epic_id": epic_id}


def _resolve_completeness_review_evidence(
    *,
    client: BeadsClient,
    epic_id: str,
    completeness_review_comment_id: str | None,
    review_launcher: CompletenessReviewLauncher | None,
    request: ArchiveCompletenessReviewRequest,
) -> str | None:
    evidence_id = valid_completeness_review_evidence_id(
        client=client,
        epic_id=epic_id,
        evidence_id=completeness_review_comment_id,
        archive_actor=_PLAN_ARCHIVE_ACTOR,
    )
    if evidence_id is not None or review_launcher is None:
        return evidence_id
    launched_id = review_launcher(request=request)
    return valid_completeness_review_evidence_id(
        client=client,
        epic_id=epic_id,
        evidence_id=launched_id,
        archive_actor=_PLAN_ARCHIVE_ACTOR,
    )


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _blocking_dependency_ids(*, record: BeadsRecord) -> frozenset[str]:
    return blocking_dependency_ids(record=record)


def _is_blocks_dependency_edge(*, edge: object) -> str | None:
    return is_blocks_dependency_edge(edge=edge)


def _comment_body(*, prefix: str, author: str, now: str, body: str) -> str:
    return f"{prefix}\nauthor: {author}\ntimestamp: {now}\n\n{body}"


def _scope_body(*, requirements: tuple[str, ...], deferrals: tuple[str, ...]) -> str:
    requirement_lines = "\n".join(f"- {requirement}" for requirement in requirements)
    deferral_lines = "\n".join(f"- {deferral}" for deferral in deferrals)
    return f"Requirement carriers:\n{requirement_lines}\n\nExplicit deferrals:\n{deferral_lines}"
