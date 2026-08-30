# pyright: reportMissingImports=none, reportMissingTypeStubs=none
"""_seam_equivalence_findings — what a disagreement between the surfaces IS, and its name.

The comparison half of `seam_equivalence`. It owns the three input FAMILIES the
`[run.inputs]` table carries, and the four ways the integration subset of those
inputs can fail to say one thing: a position the engine will not render, either
direction of the token/rendered-input equality, a scoping rot, and a schema-leg
mismatch. It is deliberately free of filesystem and reporting concerns -- every
function here takes sets and returns findings -- so the rules can be read and
tested without a payload on disk.

SCOPED TO THE INTEGRATION SUBSET. The `[run.inputs]` table also carries the six
ACP adapter inputs and the two review/cap POLICY inputs
(`review_fix_visit_cap`, `merge_on_review_cap_outcome`). Those are NOT
projections of the integration contract -- the adapters ride the plan's ACP
overlay and the policy pair is per-item policy -- so the equality deliberately
excludes them. The exclusion is checked rather than assumed: the three name sets
must be pairwise disjoint, and every input the payload declares must fall in one
of them, so an input added tomorrow cannot be silently dropped out of the
comparison by belonging to nothing.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from itertools import combinations

# NO `sys.path` bootstrap here, deliberately. This is a PRIVATE module of
# `seam_equivalence`, imported only through it, and that owner already puts this
# directory and the orchestrator package's root on the path before importing
# this file. A second copy of the bootstrap would be dead code that no caller
# can reach and no test can exercise.
from _seam_equivalence_scan import Occurrence
from livespec_orchestrator_beads_fabro.commands._acp_node_adapters import NODE_INPUT_CANDIDATES
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_projection import (
    CONTRACT_INPUT_NAMES,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_schema import (
    INTEGRATION_FIELDS,
)

__all__: list[str] = [
    "ADAPTER_INPUT_NAMES",
    "POLICY_INPUT_NAMES",
    "SCHEMA_PROJECTABLE_INPUTS",
    "Finding",
    "equivalence_findings",
    "non_rendered_occurrences",
    "position_findings",
    "referenced_integration_inputs",
    "schema_findings",
    "scoping_findings",
]

# The schema's PROJECTABLE fields, named by the workflow input each crosses as.
# Read off the projection's own closed mapping rather than restated, so this
# check cannot come to disagree with the thing it is comparing.
SCHEMA_PROJECTABLE_INPUTS: frozenset[str] = frozenset(CONTRACT_INPUT_NAMES.values())

# The per-node ACP adapter inputs, likewise read off their owning module.
ADAPTER_INPUT_NAMES: frozenset[str] = frozenset(
    name for candidates in NODE_INPUT_CANDIDATES.values() for name in candidates
)

# The two review/cap POLICY inputs. Named here because they are per-item policy
# the Dispatcher renders from the item's own settings, not from the integration
# contract -- there is no contract object to read them off.
POLICY_INPUT_NAMES: frozenset[str] = frozenset(
    {"review_fix_visit_cap", "merge_on_review_cap_outcome"}
)


@dataclass(frozen=True, kw_only=True)
class Finding:
    """One way the three integration-input surfaces fail to say the same thing."""

    kind: str
    detail: str
    subject: str


def referenced_integration_inputs(*, occurrences: Iterable[Occurrence]) -> frozenset[str]:
    """The INTEGRATION inputs the payload references, whatever else it also carries."""
    return frozenset(
        occurrence.name
        for occurrence in occurrences
        if occurrence.name in SCHEMA_PROJECTABLE_INPUTS
    )


def non_rendered_occurrences(*, occurrences: Iterable[Occurrence]) -> list[Occurrence]:
    """Every integration token sitting where the pinned engine would not expand it.

    Separate from the finding it produces so the matcher control can assert the
    two agree: a predicate that silently stopped selecting would otherwise take
    the finding with it, and the control would confirm the silence.
    """
    return [
        occurrence
        for occurrence in occurrences
        if occurrence.name in SCHEMA_PROJECTABLE_INPUTS and not occurrence.rendered
    ]


def position_findings(*, occurrences: Iterable[Occurrence]) -> list[Finding]:
    """Every integration token the pinned engine would not expand where it sits."""
    return [
        Finding(
            kind="non-rendered-position",
            subject=occurrence.name,
            detail=(
                f"`inputs.{occurrence.name}` sits at {occurrence.venue} "
                f"`{occurrence.position}`, which the pinned engine does not render"
            ),
        )
        for occurrence in non_rendered_occurrences(occurrences=occurrences)
    ]


def equivalence_findings(*, referenced: frozenset[str], rendered: frozenset[str]) -> list[Finding]:
    """The two directions of the equality, each reported by name."""
    findings = [
        Finding(
            kind="token-without-rendered-input",
            subject=name,
            detail=(
                f"the workflow references `inputs.{name}` but the Dispatcher renders no "
                "such input from the resolved integration contract"
            ),
        )
        for name in sorted(referenced - rendered)
    ]
    findings.extend(
        Finding(
            kind="rendered-input-without-token",
            subject=name,
            detail=(
                f"the Dispatcher renders `{name}` from the resolved integration contract "
                "but no workflow position references it"
            ),
        )
        for name in sorted(rendered - referenced)
    )
    return findings


def scoping_findings(*, declared: Mapping[str, str]) -> list[Finding]:
    """That the equality is scoped to the integration subset, and to all of it.

    Two ways the scoping can rot, both silent: a name could belong to two
    families at once, which would make the exclusion ambiguous; or a newly
    declared input could belong to none, which would drop it out of every
    comparison while the payload happily sends it.
    """
    families = (
        ("schema-projectable", SCHEMA_PROJECTABLE_INPUTS),
        ("acp-adapter", ADAPTER_INPUT_NAMES),
        ("review-cap-policy", POLICY_INPUT_NAMES),
    )
    findings = [
        Finding(
            kind="overlapping-input-families",
            subject=name,
            detail=f"`{name}` is both {left} and {right}, so the exclusion is ambiguous",
        )
        for (left, left_names), (right, right_names) in combinations(families, 2)
        for name in sorted(left_names & right_names)
    ]
    classified = SCHEMA_PROJECTABLE_INPUTS | ADAPTER_INPUT_NAMES | POLICY_INPUT_NAMES
    findings.extend(
        Finding(
            kind="unclassified-declared-input",
            subject=name,
            detail=(
                f"`{name}` is declared by the payload but is neither an integration field, "
                "an ACP adapter, nor a review/cap policy input"
            ),
        )
        for name in sorted(set(declared) - classified)
    )
    return findings


def schema_findings() -> list[Finding]:
    """That the rendered names and the schema's projectable fields are one vocabulary.

    Both directions, and neither is book-keeping. A projected name that is no
    schema field would mean the Dispatcher renders a point the closed field set
    does not carry. A projected name that DIFFERS from the field it is keyed by
    would be worse and quieter: the equality above compares a set of workflow
    tokens against a set of rendered input names, so the two are only the same
    question while the input name and the schema attribute are the same word --
    which is exactly what the projection's own mapping undertakes to keep.
    """
    schema_attributes = {field.attribute for field in INTEGRATION_FIELDS}
    findings = [
        Finding(
            kind="projection-names-no-schema-field",
            subject=attribute,
            detail=f"the projection names `{attribute}`, which is no field of the schema",
        )
        for attribute in sorted(set(CONTRACT_INPUT_NAMES) - schema_attributes)
    ]
    findings.extend(
        Finding(
            kind="projected-name-differs-from-field",
            subject=name,
            detail=(
                f"schema field `{attribute}` crosses as input `{name}`; the two must be the "
                "same word for a token set and a rendered-input set to be comparable at all"
            ),
        )
        for attribute, name in sorted(CONTRACT_INPUT_NAMES.items())
        if attribute != name
    )
    return findings
