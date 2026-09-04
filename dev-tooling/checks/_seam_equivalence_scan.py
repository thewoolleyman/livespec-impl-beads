"""_seam_equivalence_scan — where an `inputs.<name>` token sits, and whether that renders.

The private half of `seam_equivalence`. It owns ONE question — given the text of
a dispatched-payload file, which `{{ inputs.<name> }}` tokens are in it and at
what POSITION does each sit — and it owns the evidence about which positions the
pinned fabro build actually expands. The public half owns the comparison between
the surfaces and the controls over it.

The two are separate modules because they change for different reasons: this one
changes when the engine's templating behaviour changes or a new payload venue
appears, while the comparison changes when the integration schema does.

THE RENDERED-POSITION ALLOWLIST IS EVIDENCE-BASED AND FAIL-CLOSED. A token is
accepted only where the pinned fabro build is KNOWN to expand it:

- a graph node's `acp.command` -- the form the fabro enemy-unit-tier asserts on
  every ACP node, and the one every live dispatch exercises;
- a graph edge's `condition` -- the form the review/cap guards already ride;
- a script node's `script` -- a plain string attribute on both sides of the
  engine, like `acp.command` and unlike the typed `timeout` below. Admitted on
  the maintainer's confirmation of 2026-08-31 (recorded on plan epic
  bd-ib-vblnq2 while landing C5-payload, bd-ib-b7xpzl) that the pinned 0.254.0
  build expands `inputs.*` in a parallelogram node's `script`; the payload's
  janitor gate and dead-implementer breaker ride it;
- a node prompt body: the sandbox-side consumer the
  resolve-once-project-everywhere clause names, which reads `inputs.<name>`;
- a `[[run.prepare.steps]]` `script` in the run config -- RESOLVED, but NOT by
  the engine, and the distinction is why this entry now carries its own
  paragraph. The pinned 0.254.0 build leaves `run.prepare` commands verbatim.
  This position was admitted alongside the node `script` on 2026-08-31, but the
  maintainer confirmation recorded that day covered a parallelogram node's
  `script`; nothing established the same for a prepare command, and every
  dispatch through the templated payload died in setup at exit 127, the shell
  reporting `{{: command not found`, until the Dispatcher's own overlay began
  substituting the resolved values host-side
  (`_dispatcher_overlay._substitute_input_tokens`). It belongs in this set
  because the token IS resolved before the sandbox ever sees it -- by us rather
  than by the engine -- and it MUST move back out if that host-side
  substitution is removed.

Every OTHER position is reported. That is deliberate rather than conservative
book-keeping: the ratified ACP-node-timeouts clause records that the pinned
build types a quoted duration at parse time and its template expansion never
re-types a rendered string, so a templated `timeout` leaves the node with NO
timeout AND REPORTS NOTHING. A numeric attribute (`max_visits`, `max_retries`,
`weight`) is typed the same way, and a token in a comment or anywhere outside an
attribute value is not a template at all. Widening the allowlist is therefore a
reviewable diff carrying its own evidence, never an inference from "this
attribute looks like a string".
"""

from __future__ import annotations

import re
from dataclasses import dataclass

__all__: list[str] = [
    "GRAPH_RENDERED_ATTRIBUTES",
    "OUTSIDE_ATTRIBUTE_POSITION",
    "PREPARE_STEP_POSITION",
    "PROMPT_BODY_POSITION",
    "Occurrence",
    "graph_occurrences",
    "prompt_occurrences",
    "run_config_occurrences",
]

# Graph attributes the pinned engine expands. See the module docstring for the
# evidence behind each, and for why everything absent from this set is reported.
GRAPH_RENDERED_ATTRIBUTES: frozenset[str] = frozenset({"acp.command", "condition", "script"})

PREPARE_STEP_POSITION = "run.prepare.steps.script"
PROMPT_BODY_POSITION = "prompt-body"
OUTSIDE_ATTRIBUTE_POSITION = "outside-any-attribute-value"

_TOKEN_RE = re.compile(r"\{\{\s*inputs\.(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*\}\}")
_QUOTED_ATTRIBUTE_RE = re.compile(
    r"(?P<attribute>[A-Za-z_][A-Za-z0-9_.]*)\s*=\s*\"(?P<value>(?:\\.|[^\"\\])*)\""
)
_TOML_TABLE_RE = re.compile(r"^\[{1,2}(?P<table>[^\]]+)\]{1,2}\s*$")


@dataclass(frozen=True, kw_only=True)
class Occurrence:
    """One `inputs.<name>` token in the dispatched payload, with where it sits."""

    name: str
    venue: str
    position: str
    rendered: bool


def _attribute_at(*, text: str, offset: int) -> str | None:
    """The attribute whose quoted value spans `offset`, or None if no value does."""
    for match in _QUOTED_ATTRIBUTE_RE.finditer(text):
        if match.start("value") <= offset < match.end("value"):
            return match.group("attribute")
    return None


def graph_occurrences(*, text: str, venue: str) -> list[Occurrence]:
    """Every token in a DOT graph, positioned by the attribute whose value holds it.

    A token that falls in NO attribute value -- a comment, or loose text -- is
    reported at its own position rather than ignored: the payload's own header
    records that a brace token in a comment breaks the graph render, so silence
    there would be the wrong answer as well as an unrendered one.
    """
    occurrences: list[Occurrence] = []
    for match in _TOKEN_RE.finditer(text):
        attribute = _attribute_at(text=text, offset=match.start())
        position = OUTSIDE_ATTRIBUTE_POSITION if attribute is None else attribute
        occurrences.append(
            Occurrence(
                name=match.group("name"),
                venue=venue,
                position=position,
                rendered=position in GRAPH_RENDERED_ATTRIBUTES,
            )
        )
    return occurrences


def run_config_occurrences(*, text: str, venue: str) -> list[Occurrence]:
    """Every token in the run config, positioned by `<table>.<key>`.

    Only a `[[run.prepare.steps]]` `script` renders; the table is tracked by a
    line scan because the pinned Python ships no TOML reader and the run config
    is repo-owned with a stable shape -- the same reasoning the projection's own
    `[run.inputs]` scan records.
    """
    occurrences: list[Occurrence] = []
    table = ""
    for line in text.splitlines():
        header = _TOML_TABLE_RE.match(line.strip())
        if header is not None:
            table = header.group("table")
            continue
        for match in _TOKEN_RE.finditer(line):
            key = _attribute_at(text=line, offset=match.start())
            position = OUTSIDE_ATTRIBUTE_POSITION if key is None else f"{table}.{key}"
            occurrences.append(
                Occurrence(
                    name=match.group("name"),
                    venue=venue,
                    position=position,
                    rendered=position == PREPARE_STEP_POSITION,
                )
            )
    return occurrences


def prompt_occurrences(*, text: str, venue: str) -> list[Occurrence]:
    """Every token in a node prompt body -- a rendered position in whole."""
    return [
        Occurrence(
            name=match.group("name"),
            venue=venue,
            position=PROMPT_BODY_POSITION,
            rendered=True,
        )
        for match in _TOKEN_RE.finditer(text)
    ]
