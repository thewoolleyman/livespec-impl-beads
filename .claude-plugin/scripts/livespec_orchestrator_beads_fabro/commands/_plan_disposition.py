"""Session-performable disposition of a plan child.

The archive gate refuses while any child of the plan epic is undisposed, and
sessions have treated re-parenting or closing a child as a maintainer call. The
two together deadlock the archive for any epic that accumulated scope creep:
the session will not dispose, so the gate never opens, so the plan stays live
until somebody interrupts the maintainer for it.

Disposing a plan child is not a spec-change decision. It changes where work is
TRACKED, not what the specification REQUIRES, so it is one of the decisions a
session takes itself with a recorded rationale. The rationale is written to the
ledger BEFORE the mutation, so a failed mutation leaves an explained intent
rather than a silent disposition.

One refusal remains. A child carrying a spec commitment is design-human-gated
by routing, and this module refuses to dispose it, naming the child. That
refusal asks `is_spec_commitment` rather than testing `spec_id` for presence:
a plan ANCHOR MARKER shares that column with a genuine commitment, so refusing
on presence alone refused every plan child there is — reinstating the exact
deadlock the paragraphs above describe.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from livespec_orchestrator_beads_fabro._beads_client import EDGE_PARENT_CHILD, make_beads_client
from livespec_orchestrator_beads_fabro.commands._plan_anchor import is_spec_commitment

if TYPE_CHECKING:
    from livespec_orchestrator_beads_fabro._beads_client import BeadsClient
    from livespec_orchestrator_beads_fabro.types import StoreConfig

__all__: list[str] = [
    "DISPOSITION_PREFIX",
    "PlanDispositionRefusedError",
    "close_plan_child",
    "reparent_plan_child",
]

DISPOSITION_PREFIX = "plan-child-disposition"


class PlanDispositionRefusedError(Exception):
    """Expected refusal raised when a session may not dispose a plan child."""

    @classmethod
    def spec_change_tier(cls, *, child_id: str) -> PlanDispositionRefusedError:
        detail = "human-gated by routing and is not session-disposable"
        return cls(f"{child_id} carries a spec commitment; a spec-change-tier child is {detail}")


def close_plan_child(
    *,
    config: StoreConfig,
    epic_id: str,
    child_id: str,
    rationale: str,
    author: str,
    now: str,
) -> None:
    """Close one plan child, recording why, with no human valve."""
    client = make_beads_client(config=config)
    _refuse_spec_change_tier(client=client, child_id=child_id)
    _record_disposition(
        client=client,
        epic_id=epic_id,
        child_id=child_id,
        disposition="closed",
        rationale=rationale,
        author=author,
        now=now,
    )
    client.close_issue(issue_id=child_id, reason=rationale)


def reparent_plan_child(  # noqa: PLR0913 — one kw-only argument per recorded disposition field.
    *,
    config: StoreConfig,
    epic_id: str,
    child_id: str,
    new_parent_id: str,
    rationale: str,
    author: str,
    now: str,
) -> None:
    """Move one plan child to another parent, recording why, with no human valve."""
    client = make_beads_client(config=config)
    _refuse_spec_change_tier(client=client, child_id=child_id)
    _record_disposition(
        client=client,
        epic_id=epic_id,
        child_id=child_id,
        disposition=f"re-parented to {new_parent_id}",
        rationale=rationale,
        author=author,
        now=now,
    )
    client.remove_dependency(from_id=child_id, to_id=epic_id)
    client.add_dependency(from_id=child_id, to_id=new_parent_id, edge_type=EDGE_PARENT_CHILD)


def _refuse_spec_change_tier(*, client: BeadsClient, child_id: str) -> None:
    record = client.show_issue(issue_id=child_id)
    spec_id = record.get("spec_id")
    if isinstance(spec_id, str) and is_spec_commitment(spec_id=spec_id):
        raise PlanDispositionRefusedError.spec_change_tier(child_id=child_id)


def _record_disposition(  # noqa: PLR0913 — one kw-only argument per recorded disposition field.
    *,
    client: BeadsClient,
    epic_id: str,
    child_id: str,
    disposition: str,
    rationale: str,
    author: str,
    now: str,
) -> None:
    body = (
        f"{DISPOSITION_PREFIX}\nauthor: {author}\ntimestamp: {now}\n\n"
        f"{child_id} {disposition} out of plan epic {epic_id} by the plan session.\n\n"
        f"Rationale: {rationale}"
    )
    client.add_comment(issue_id=child_id, body=body)
    client.add_comment(issue_id=epic_id, body=body)
