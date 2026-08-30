"""The pre-dispatch pass that grades a declaration against the build's schema version.

`SPECIFICATION/contracts.md`, the repository-integration-contract section's
"contract version is schema version" clause, requires the executing plugin build
to NAME the contract schema version it requires, to validate a governed
repository's declaration against that version before the dispatch, and to refuse
as a pre-dispatch precondition error (exit `3`, journaled) enumerating EVERY
`Defective` point in ONE message. This module is that pass.

ONE MESSAGE, NOT ONE DISPATCH AT A TIME. The refusal lists every unmet point
together because the failure mode it retires is an adopter learning its
integration premises one broken dispatch at a time -- fix the first, dispatch
again, discover the second, with a merged item stranded somewhere in the middle.
It therefore supersedes the single-key check-suite refusal that used to stand at
the same point in the preamble, which could only ever name the first thing wrong.

THERE IS NO KEY LIST HERE. The graded points are `INTEGRATION_FIELDS` -- the
schema's own closed set -- so a newly ratified field is picked up with no edit to
this module, and the pass cannot fall behind the schema by omission. That is the
clause's "no hand-maintained list of keys exists anywhere" made structural rather
than promised: there is nothing here for a later field to be forgotten from.

IT GRADES WHAT THE REPOSITORY WROTE, NEVER WHAT IT LEFT UNWRITTEN, and that is
the whole of why a later build cannot strand an already-admitted item. A point
the declaration CARRIES -- a key present but unusable, an ancestor that is
present and is not a mapping -- is a defect OF THE DECLARATION and refuses here.
A point the repository never wrote is an ABSENCE, and an absence is exactly what
a schema field added by a LATER BUILD looks like in an EARLIER repository:
refusing on it would refuse every governed repository the moment the schema grew,
including the ones whose items are already mid-pipeline. So absence is left to
the arm that owns it -- a fleet default where the schema declares one, and
otherwise the step or seam that consumes the point, which refuses there naming
its own resolution and its own committed waiver. `SPECIFICATION/scenarios.md`
Scenario 97 ratifies this directly: a fleet-member repository that declares none
of the integration keys passes the validation pass and the dispatch is admitted.

AND IT GRADES A DECLARATION, SO IT SKIPS THE ONE FIELD A DECLARATION CANNOT
ANSWER. The default branch is a schema field whose declaration is the REPOSITORY
ITSELF -- nothing an adopter writes in `.livespec.jsonc` may answer it -- so the
schema marks it `declared_in_config=False` and this pass never grades it. That is
not a key list either: the discrimination is a property of the FIELD, read off
the same closed set. Its own ratified two-route resolution refuses at the seam
that probes it.

THE JOURNAL RECORD IS WRITTEN ON THE REFUSED ARM ONLY. The clause requires the
REFUSAL to be journaled, and an admitted dispatch already journals its whole
resolved contract -- every field, its arm and its value -- with the dispatch
record. A second record on the admitting path would restate that, and would cost
a refusal on some LATER preflight its zero-side-effect guarantee.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_declaration import (
    declaration_from_config_text,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_resolver import (
    Defective,
    declaration_carries,
    resolve_integration_field,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_schema import (
    INTEGRATION_CONTRACT_SCHEMA_VERSION,
    INTEGRATION_FIELDS,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_invoker import invoker_from_args
from livespec_orchestrator_beads_fabro.commands._dispatcher_io import JournalFile
from livespec_orchestrator_beads_fabro.commands._dispatcher_loop_selection import (
    livespec_config_text,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_paths import journal_path

__all__: list[str] = [
    "SCHEMA_VALIDATION_STAGE",
    "DeclarationValidation",
    "schema_validation_refusal",
    "validate_declaration",
    "validation_record",
    "validation_refusal",
]

# The journal stage the refusal records under.
SCHEMA_VALIDATION_STAGE = "schema-validation"


@dataclass(frozen=True, kw_only=True)
class DeclarationValidation:
    """One declaration graded against ONE schema version, with every defect kept.

    `schema_version` is the version the EXECUTING BUILD requires, carried on the
    verdict rather than looked up again by the refusal or the journal record, so
    the number an operator reads and the number the pass graded against are the
    same number by construction.

    `defects` is every unmet point, in the schema's own field order, because the
    ratified refusal enumerates all of them at once. An empty tuple is the whole
    of "this declaration satisfies the version": there is no partial arm.
    """

    schema_version: int
    defects: tuple[Defective, ...]


def validate_declaration(*, declaration: Mapping[str, object]) -> DeclarationValidation:
    """Grade a declaration against the schema version this build requires."""
    graded = (
        field
        for field in INTEGRATION_FIELDS
        if field.declared_in_config and declaration_carries(field=field, declaration=declaration)
    )
    resolutions = (
        resolve_integration_field(field=field, declaration=declaration) for field in graded
    )
    defects = tuple(resolution for resolution in resolutions if isinstance(resolution, Defective))
    return DeclarationValidation(
        schema_version=INTEGRATION_CONTRACT_SCHEMA_VERSION, defects=defects
    )


def validation_refusal(*, validation: DeclarationValidation) -> str | None:
    """The one enumerated refusal a defective declaration earns; None when it passes.

    Every defect is rendered as its own line naming the committed key verbatim
    and the reason that key resolved nothing, so an adopter can fix the whole set
    in one edit of `.livespec.jsonc`.
    """
    if not validation.defects:
        return None
    points = "".join(f"  - `{defect.key}`: {defect.reason}\n" for defect in validation.defects)
    return (
        "ERROR: refusing to dispatch; this repository's declaration does not satisfy "
        f"integration-contract schema version {validation.schema_version}, which this "
        "plugin build requires. No work-item was admitted and no factory run was "
        "created. Every unmet point is listed here so they can be fixed together "
        f"rather than one dispatch at a time:\n{points}"
    )


def validation_record(*, validation: DeclarationValidation) -> dict[str, object]:
    """The journal record for a refused grading, carrying every point it named."""
    return {
        "stage": SCHEMA_VALIDATION_STAGE,
        "schema_version": validation.schema_version,
        "outcome": "refused",
        "defects": [{"key": defect.key, "reason": defect.reason} for defect in validation.defects],
    }


def schema_validation_refusal(*, args: argparse.Namespace, repo: Path) -> str | None:
    """Grade the target's declaration, journal any refusal, and return it; else None."""
    validation = validate_declaration(
        declaration=declaration_from_config_text(config_text=livespec_config_text(repo=repo))
    )
    refusal = validation_refusal(validation=validation)
    if refusal is None:
        return None
    journal = JournalFile(
        path=journal_path(args=args, repo=repo), identity=invoker_from_args(args=args)
    )
    journal.append(record=validation_record(validation=validation))
    return refusal
