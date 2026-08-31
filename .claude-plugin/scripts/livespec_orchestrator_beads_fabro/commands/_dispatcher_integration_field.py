"""What an integration POINT is, independent of which points exist.

The sibling schema module owns the CLOSED SET -- which obligations the
orchestrator may impose on a governed repository, and therefore what a reviewer
sees change when one is added. This module owns the orthogonal question: given
one point, what can be said about it. The two change for entirely different
reasons -- a newly ratified obligation adds a field descriptor over there, while
a newly admitted VALUE SHAPE or declaration DIMENSION changes the descriptor type
here -- which is why they are separate modules rather than one file.

Nothing here imports the schema, and that is load-bearing rather than incidental:
it is what lets a per-family field module (the conformance premises) build its own
descriptors without the closed set having to import them back.

VENUE IS A SCHEMA DIMENSION, NOT TWO LITERALS. The check-suite legitimately
differs between the host janitor and the in-sandbox gate, so BOTH venues are
fields, reading the SAME committed declaration and differing only in their fleet
default. Before this, the host argv lived in the janitor resolver and the sandbox
one lived as bare prose in a publish prompt, with nothing binding them -- which
is exactly the "two divergent literals" the clause forbids.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__: list[str] = [
    "SHAPE_ARGV",
    "SHAPE_CONFORMANCE",
    "SHAPE_ENUM",
    "SHAPE_NAME",
    "VENUE_HOST_JANITOR",
    "VENUE_IN_SANDBOX_GATE",
    "IntegrationField",
]

# The two venues a check-suite legitimately differs between.
VENUE_HOST_JANITOR = "host-janitor"
VENUE_IN_SANDBOX_GATE = "in-sandbox-gate"

# The four value shapes a field admits. `name` is a non-empty string, `argv` is
# a command the resolver hands back as argv tokens, `enum` is a closed set of
# admitted strings, and `conformance` is a mapping naming one of a closed MODE
# enumeration -- the shape a premise takes when "what to run" and "whether to run
# anything at all" are the same question, and answering it with a bare argv would
# leave the skip case unable to say it was chosen.
SHAPE_NAME = "name"
SHAPE_ARGV = "argv"
SHAPE_ENUM = "enum"
SHAPE_CONFORMANCE = "conformance"


@dataclass(frozen=True, kw_only=True)
class IntegrationField:
    """One integration point: where it is declared, and what resolving it means.

    `key` is the operator-facing name every refusal quotes; `path` is the dotted
    lookup into the declaration. They differ wherever the two nestings differ --
    the `compat` pair names the plugin block a reader must write under while
    being looked up relative to it.

    `required` marks a field whose ratified semantics admit NO safe default, so
    an absent key resolves to `Defective` naming the absence rather than to a
    substituted value.

    `parent_key` is the ONLY-AN-ABSENT-KEY-FALLS-BACK rule made generic. Where it
    is set, DECLARING the parent block makes this field required: a present
    `dispatcher.master_ci` that names no `workflow` is a defect, because
    defaulting the missing half would prove part of a pipeline the repository
    never named. Where it is None -- `dispatcher.janitor.check_suite` -- a
    present parent that omits the child is a genuine absence and falls back.

    `declared_in_config` says whether this point is one a repository ANSWERS in
    its committed declaration. It is True for every field an adopter writes and
    False for the default branch alone, whose declaration is the repository
    itself. The pre-dispatch schema-validation pass grades a DECLARATION, so it
    grades exactly the fields carrying True: refusing there on an unprobed
    branch would send an operator to fix a committed key that does not exist,
    and the branch's own two-route resolution already refuses at the seam that
    probes it.

    `internal_argv` is the invocation a `conformance`-shaped field renders when
    a repository declares the internal mode. It hangs off the FIELD because the
    three conformance premises differ only in which invocation they name, so
    carrying it here keeps the resolver generic; the values themselves belong to
    the fleet-defaults module and are never spelled in this one.
    """

    attribute: str
    key: str
    path: str
    shape: str
    required: bool = False
    fleet_default: str | tuple[str, ...] | None = None
    admitted: tuple[str, ...] = ()
    venue: str | None = None
    parent_key: str | None = None
    declared_in_config: bool = True
    internal_argv: tuple[str, ...] = ()
