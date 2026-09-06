"""Plan identity: the `plan_slug` epic tag and the `associated_work_item_id` anchor.

The WRITE side of the ratified plan-identity contract. Two facts identify
a plan and they are deliberately carried on OPPOSITE sides of the seam, so
either side resolves the other: the ledger epic carries the canonical
dash-cased slug in its metadata, and the plan directory carries that
epic's id in one file. The conformance checks that grade the pair read
both directions; this module is what makes them agree at creation time
instead of at migration time.

BOTH WRITES LIVE HERE, ONCE, because every epic-creating route owes them
— the `plan` front-end, which creates the directory and the epic in the
same act, and the `capture-work-item` operation, whose prose files an
epic with no directory at all. A route that hand-rolled either write is
exactly the drift the bidirectional checks exist to catch, and a second
copy of the canonicalization is how two routes come to disagree about
what "the same slug" means.

THE SLUG IS CANONICALIZED HERE RATHER THAN TRUSTED FROM THE CALLER. The
contract requires a written value to equal its own canonicalization, and
a caller-supplied hint has not been through it. Canonicalizing on the way
in is idempotent for an already-canonical slug, so the front-end's
confirmed slug survives unchanged while a raw hint is repaired rather
than written and later reported.

THE ANCHOR IS WRITE-ONCE, WITH EXACTLY ONE SANCTIONED REWRITE. A file
already naming an epic is left untouched: it is a re-derivable pointer,
not a mirror of children, status, handoffs, readiness, or archive state,
and nothing here updates it for any of those. The one permitted
transition is the literal `unassigned` — the research-before-work-items
state, a directory of standalone research that predates any epic — to the
id of the epic that ADOPTS the directory, which COMPLETES the anchor
rather than mirroring anything.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, cast

from livespec_orchestrator_beads_fabro._beads_client import make_beads_client

if TYPE_CHECKING:
    from pathlib import Path

    from livespec_orchestrator_beads_fabro._beads_client import BeadsRecord
    from livespec_orchestrator_beads_fabro.types import StoreConfig

__all__: list[str] = [
    "PLAN_ANCHOR_FILENAME",
    "PLAN_SLUG_METADATA_KEY",
    "UNASSIGNED_ANCHOR",
    "canonical_plan_slug",
    "tag_epic_plan_slug",
    "write_plan_anchor",
]

PLAN_ANCHOR_FILENAME = "associated_work_item_id"
UNASSIGNED_ANCHOR = "unassigned"
# Public because a READER of the tag needs the same key its writer uses: the
# migration reads `plan_slug` off every epic to decide which are untagged, and a
# second copy of the literal is how a reader and a writer come to disagree.
PLAN_SLUG_METADATA_KEY = "plan_slug"

_PLAN_DIR = "plan"
# The canonicalization the `propose-change` operation applies to a topic
# hint, restated as code: lowercase, one hyphen per run of non-`[a-z0-9]`,
# strip, truncate to 64.
_SLUG_SEPARATOR_RUN = re.compile(r"[^a-z0-9]+")
_MAX_SLUG_LENGTH = 64


def canonical_plan_slug(*, text: str) -> str:
    """Canonicalize a title or a raw slug hint into the tenant's plan-slug form."""
    hyphenated = _SLUG_SEPARATOR_RUN.sub("-", text.lower()).strip("-")
    # The trailing strip runs AGAIN after truncation because the cut can land
    # on a separator, and a value ending in a hyphen would not equal its own
    # canonicalization — the property the `plan_slug_canonical` verdict grades.
    return hyphenated[:_MAX_SLUG_LENGTH].strip("-")


def write_plan_anchor(*, project_root: Path, slug: str, epic_id: str) -> Path:
    """Anchor `plan/<slug>/` to its epic, completing an `unassigned` anchor.

    Returns the anchor path whether or not this call wrote it: an anchor
    already naming an epic is write-once and is left exactly as it stands.
    """
    anchor = project_root / _PLAN_DIR / slug / PLAN_ANCHOR_FILENAME
    anchor.parent.mkdir(parents=True, exist_ok=True)
    if anchor.is_file() and anchor.read_text(encoding="utf-8").strip() != UNASSIGNED_ANCHOR:
        return anchor
    _ = anchor.write_text(f"{epic_id}\n", encoding="utf-8")
    return anchor


def tag_epic_plan_slug(
    *,
    config: StoreConfig,
    epic_id: str,
    title: str,
    slug: str | None = None,
) -> str:
    """Write an epic's canonical `plan_slug`, deriving it from the title when unsupplied.

    Returns the value written, so a caller that supplied no slug learns the
    handle its epic now answers to.
    """
    resolved = canonical_plan_slug(text=title if slug is None else slug)
    client = make_beads_client(config=config)
    record = client.show_issue(issue_id=epic_id)
    metadata = _record_metadata(record=record)
    metadata[PLAN_SLUG_METADATA_KEY] = resolved
    client.update_issue(issue_id=epic_id, metadata=metadata)
    return resolved


def _record_metadata(*, record: BeadsRecord) -> dict[str, Any]:
    """Return a record's metadata, tolerating the key's absence.

    Beads records are `omitempty`-sparse: an epic holding no metadata omits
    the key ENTIRELY rather than carrying an empty object, so subscripting it
    raises on exactly the untagged epics this write exists to repair. The
    migration met that on its first real tenant and wrote nothing at all.
    """
    metadata = record.get("metadata")
    if not isinstance(metadata, dict):
        return {}
    return dict(cast("dict[str, Any]", metadata))
