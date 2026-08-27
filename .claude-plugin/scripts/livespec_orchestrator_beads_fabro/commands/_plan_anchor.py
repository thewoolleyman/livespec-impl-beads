"""The plan anchor marker, and its discrimination from a spec commitment.

A plan is anchored in the ledger by one epic, and that epic is stamped with
`spec_commitment_hint = "plan:<slug>"` so the plan's topic is recoverable
from the ledger alone. The store bridge maps `spec_commitment_hint` onto
the beads-native `spec_id` column — the SAME column a genuine commitment
to ratified spec text uses. The field is therefore OVERLOADED, and every
consumer of it is really asking one of two different questions.

⛔ PRESENCE IS NOT THE ANSWER TO EITHER QUESTION. A consumer that tests
the field for presence alone answers "was this created by the plan
primitive", not "does this commit to ratified spec text" — and it answers
it with the wrong one's name. Three consumers did exactly that, and the
collision made every plan epic permanently non-disposable: the
disposition guard refused every plan child, so the archive gate never
opened; the calibration proxy counted a plan anchor as touching spec
surface; and the admission-policy resolver pinned every plan-anchored
item to the manual floor that config cannot override.

THE DISCRIMINATOR IS THE PREFIX, and it is sound rather than merely
convenient. A genuine `spec_id` is an obligation `id_hint` parsed out of
proposed-change front-matter, and those are bare slugs; the plan prefix is
punctuated in a way no obligation slug is. Un-overloading the field was
considered and rejected for this module's change: `WorkItem` is defined in
the vendored runtime, so splitting the field would take an upstream
runtime change plus a data migration across every live tenant, and adopter
tenants are not hand-edited.

The literal lives here ONCE, and both the minting side (`plan_anchor_epic`,
the only place a marker is created) and every reading side import it from
here, so the two halves cannot drift apart again.
"""

from __future__ import annotations

from livespec_runtime.work_items.rank import key_between

from livespec_orchestrator_beads_fabro._ids import new_work_item_id
from livespec_orchestrator_beads_fabro.types import WorkItem

__all__: list[str] = [
    "PLAN_HINT_PREFIX",
    "is_plan_anchor",
    "is_spec_commitment",
    "plan_anchor_epic",
]

PLAN_HINT_PREFIX = "plan:"


def is_plan_anchor(*, spec_id: str | None) -> bool:
    """Whether the hint marks a plan anchor rather than committing to spec text."""
    return spec_id is not None and spec_id.startswith(PLAN_HINT_PREFIX)


def is_spec_commitment(*, spec_id: str | None) -> bool:
    """Whether the hint commits its work-item to ratified spec text.

    The question the spec-change-tier consumers mean to ask. An absent or
    empty hint commits to nothing, and a plan anchor marker commits to
    nothing either — it names where the work is TRACKED, not what the
    specification REQUIRES.
    """
    return bool(spec_id) and not is_plan_anchor(spec_id=spec_id)


def plan_anchor_epic(*, prefix: str, slug: str, title: str, now: str) -> WorkItem:
    """Mint the ledger epic that anchors one plan topic.

    The ONE place a plan anchor marker is created. The returned epic is not
    yet persisted; the caller owns the store write.
    """
    return WorkItem(
        id=new_work_item_id(prefix=prefix),
        type="epic",
        status="backlog",
        title=title,
        description=f"Plan anchor for plan/{slug}.",
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
        spec_commitment_hint=f"{PLAN_HINT_PREFIX}{slug}",
        notes=f"plan_slug={slug}",
    )
