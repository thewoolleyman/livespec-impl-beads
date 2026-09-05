"""`/livespec-orchestrator-beads-fabro:context` thin-transport command.

CLI surface per SPECIFICATION/contracts.md:

  context <plan_slug | work_item_id> [--json]
          [--work-items-path <path>] [--project-root <path>]

A QUERY-ONLY read primitive in the family of `list-work-items` and
`needs-attention`: it never mutates the work-items store. It resolves one
subject — a plan epic named by its `plan_slug` metadata, or any work-item
named by its id — and emits the single deterministic envelope
`_context_envelope` assembles for it: the resolved record, its comments, its
children (unioned across BOTH the dotted-id hierarchy and the `parent-child`
edge), its dependency edges, the plan's typed `next_action`, the research
directory its `associated_work_item_id` anchor resolves, and the spec clauses
it and its children cite.

This is what the `discuss-work-item` heavyweight skill and the console chat
pane read to resume a plan with no chat history, so an absent key is a
not-found REFUSAL rather than an empty envelope: an envelope whose fields are
all empty is indistinguishable from a plan that has not started yet, and a
front-end that cannot tell those apart resumes the wrong thing silently.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from livespec_orchestrator_beads_fabro._beads_client import make_beads_client
from livespec_orchestrator_beads_fabro.commands._config import resolve_store_config
from livespec_orchestrator_beads_fabro.commands._context_envelope import (
    build_envelope,
    resolve_subject,
)
from livespec_orchestrator_beads_fabro.errors import WorkItemNotFoundError
from livespec_orchestrator_beads_fabro.io import write_stderr, write_stdout

if TYPE_CHECKING:
    from livespec_orchestrator_beads_fabro.types import StoreConfig

__all__: list[str] = ["item_context", "main", "render_human"]

_EXIT_NOT_FOUND = 3


def main(*, argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="context")
    _ = parser.add_argument("key", help="A plan_slug or a work-item id.")
    _ = parser.add_argument("--json", dest="as_json", action="store_true")
    _ = parser.add_argument("--work-items-path", dest="work_items_path", default=None)
    _ = parser.add_argument("--project-root", dest="project_root", default=None)
    args = parser.parse_args(argv)
    project_root = Path(args.project_root) if args.project_root is not None else Path.cwd()
    config = resolve_store_config(cwd=project_root, work_items_arg=args.work_items_path)
    try:
        envelope = item_context(config=config, project_root=project_root, key=args.key)
    except WorkItemNotFoundError as exc:
        _ = write_stderr(text=f"ERROR: {exc}\n")
        return _EXIT_NOT_FOUND
    if args.as_json:
        _ = write_stdout(text=json.dumps(envelope, indent=2, sort_keys=True) + "\n")
    else:
        _ = write_stdout(text=render_human(envelope=envelope))
    return 0


def item_context(
    *,
    config: StoreConfig,
    project_root: Path,
    key: str,
) -> dict[str, Any]:
    """Assemble one subject's context envelope from a single tenant read.

    ONE `list_issues` read backs the whole assembly. Child enumeration,
    dependency reading and parent resolution all need the same population, and
    re-reading per question would let the tenant move underneath the envelope —
    which is the one thing the byte-identical-on-an-unchanged-store contract
    cannot tolerate.

    Raises `WorkItemNotFoundError` when the key names neither a work-item id
    nor a plan epic's `plan_slug` — the expected misuse the CLI maps to its
    not-found exit code.
    """
    client = make_beads_client(config=config)
    records = client.list_issues()
    resolved = resolve_subject(records=records, key=key)
    if resolved is None:
        raise WorkItemNotFoundError(item_id=key)
    subject_id, plan_epic_id = resolved
    return build_envelope(
        client=client,
        project_root=project_root,
        records=records,
        subject_id=subject_id,
        plan_epic_id=plan_epic_id,
    )


def render_human(*, envelope: dict[str, Any]) -> str:
    """Render the envelope as the operator-facing summary of the same facts.

    A COUNT, not a dump: the machine surface is `--json`, and a human reading
    this wants to know what is there and how much of it before deciding what to
    open. Each line names the field it summarizes so the two surfaces stay
    legibly the same envelope.
    """
    subject = cast("dict[str, Any]", envelope["subject"])
    epic = cast("dict[str, Any]", envelope["epic"])
    children = cast("list[dict[str, Any]]", envelope["children"])
    research = cast("dict[str, Any] | None", envelope["research"])
    spec = cast("dict[str, Any]", envelope["spec"])
    child_ids = [str(child["id"]) for child in children]
    citations = [str(entry) for entry in cast("list[Any]", spec["citations"])]
    lines = [
        f"subject: {subject['id']} (plan_slug={subject['plan_slug']})",
        f"epic: {epic['title']}",
        f"comments: {len(cast('list[Any]', envelope['comments']))}",
        f"children: {', '.join(child_ids) or '(none)'}",
        f"dependencies: {len(cast('list[Any]', envelope['dependencies']))}",
        f"next_action: {_next_action_line(action=envelope['next_action'])}",
        f"research: {'(none)' if research is None else research['directory']}",
        f"spec: {', '.join(citations) or '(none)'}",
    ]
    return "".join(f"{line}\n" for line in lines)


def _next_action_line(*, action: object) -> str:
    if action is None:
        return "(none)"
    typed = cast("dict[str, Any]", action)
    return f"{typed['kind']} {typed['ref']} — {typed['text']}"
