# pyright: reportMissingImports=none, reportMissingTypeStubs=none, reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none
"""seam_equivalence — the three integration-input surfaces say the same thing, statically.

`SPECIFICATION/contracts.md`, the repository-integration-contract section's
typed-workflow-inputs clause, requires that the set of `inputs.*` tokens the
`implement-work-item` workflow references, the set of inputs the Dispatcher
renders from the `ResolvedIntegrationContract`, and the schema's projectable
fields be IDENTICAL, and that every such token sit in a position the engine
renders. This module is the entry point of that check. It answers a templating
question statically instead of by a production dispatch, which is the whole
point: a token the engine silently drops costs one dispatch to discover and
gives no error when it happens.

IT OWNS THE READING AND THE CONTROLS, NOT THE RULES. Two sibling private
modules carry the two concerns that change for their own reasons:
`_seam_equivalence_scan` knows where a token may sit and which positions the
pinned engine expands, and `_seam_equivalence_findings` knows the three input
families and what a disagreement between the surfaces is called. What is left
here is what a CHECK does: resolve the payload, read it, render what the
Dispatcher would send, compose the findings, and refuse to report a clean
payload it could not have seen.

TWO POSITIVE CONTROLS, because this check reports an ABSENCE. The committed
payload references no integration token today — the payload edit that introduces
them is a separate, attended change — so a broken scanner would print exactly
what a conformant payload prints, forever. `main` therefore refuses to report a
clean payload unless both hold:

- the DISCOVERY control asserts the scan of the REAL payload reached its files
  and returned the tokens that are actually there (the six per-node adapter
  tokens, each in an `acp.command`), so a mis-scoped path or a pattern that
  cannot match fails loudly instead of passing silently;
- the MATCHER control asserts the checked-in fixture graph, which carries an
  integration token in a `timeout` attribute and another in a comment, still
  produces non-rendered-position findings through the SAME scan path.

Output discipline: `print` and direct `sys.stderr.write` are banned here, so
diagnostics flow through structlog (JSON to stderr).
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent
_SCRIPTS = _REPO_ROOT / ".claude-plugin" / "scripts"
for _path in (_SCRIPT_DIR, _SCRIPTS, _SCRIPTS / "_vendor"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

# structlog is the only sanctioned stderr surface for an enforcement script
# (per the `no_write_direct` ban on direct `sys.stderr.write`). It is not
# vendored in this repo's own tree, so it is imported from the installed
# `livespec_dev_tooling` package's vendored copy.
#
# The two scan/findings modules beside it are sibling PRIVATE modules in this
# same directory. This file's own directory is on `sys.path` above, so the
# sibling imports resolve both under `python <path>` and under the
# importlib-by-path load the paired test uses.
import livespec_dev_tooling  # noqa: E402

_DT_VENDOR = Path(livespec_dev_tooling.__file__).resolve().parent / "_vendor"
if str(_DT_VENDOR) not in sys.path:
    sys.path.insert(0, str(_DT_VENDOR))

import structlog  # noqa: E402
from _seam_equivalence_findings import (  # noqa: E402  — sibling private import
    Finding,
    equivalence_findings,
    non_rendered_occurrences,
    position_findings,
    referenced_integration_inputs,
    schema_findings,
    scoping_findings,
)
from _seam_equivalence_scan import (  # noqa: E402  — sibling private import
    OUTSIDE_ATTRIBUTE_POSITION,
    Occurrence,
    graph_occurrences,
    prompt_occurrences,
    run_config_occurrences,
)
from livespec_orchestrator_beads_fabro.commands._acp_node_adapters import (  # noqa: E402
    NODE_INPUT_CANDIDATES,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_projection import (  # noqa: E402
    contract_run_inputs,
    workflow_declared_inputs,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_plan_build import (  # noqa: E402
    resolve_repo_integration_contract,
)

__all__: list[str] = [
    "control_failures",
    "declared_inputs",
    "fixture_path",
    "main",
    "payload_dir",
    "payload_findings",
    "payload_occurrences",
    "rendered_input_names",
]

_PAYLOAD_RELPATH = (".claude-plugin", ".fabro", "workflows", "implement-work-item")
_FIXTURE_RELPATH = ("dev-tooling", "checks", "fixtures", "seam_equivalence_control.fabro.txt")
_CONFIG_RELPATH = (".livespec.jsonc",)
_ADAPTER_POSITION = "acp.command"


def payload_dir(*, repo_root: Path) -> Path:
    """The dispatched `implement-work-item` payload this check reads."""
    return repo_root.joinpath(*_PAYLOAD_RELPATH)


def fixture_path(*, repo_root: Path) -> Path:
    """The positive-control graph carrying known non-rendered token positions."""
    return repo_root.joinpath(*_FIXTURE_RELPATH)


def payload_occurrences(*, repo_root: Path) -> list[Occurrence]:
    """Every token across the graph, the run config, and every node prompt."""
    root = payload_dir(repo_root=repo_root)
    occurrences = graph_occurrences(
        text=(root / "workflow.fabro").read_text(encoding="utf-8"), venue="workflow.fabro"
    )
    occurrences.extend(
        run_config_occurrences(
            text=(root / "workflow.toml").read_text(encoding="utf-8"), venue="workflow.toml"
        )
    )
    for prompt in sorted((root / "prompts").glob("*.md")):
        occurrences.extend(
            prompt_occurrences(
                text=prompt.read_text(encoding="utf-8"), venue=f"prompts/{prompt.name}"
            )
        )
    return occurrences


def declared_inputs(*, repo_root: Path) -> dict[str, str]:
    """Every input the payload's `[run.inputs]` table declares, with its default."""
    run_config = payload_dir(repo_root=repo_root) / "workflow.toml"
    return dict(workflow_declared_inputs(committed_text=run_config.read_text(encoding="utf-8")))


def rendered_input_names(*, repo_root: Path) -> frozenset[str]:
    """The integration inputs the Dispatcher would render for this payload.

    Rendered THROUGH the projection, off a contract resolved from this
    repository's own declaration, rather than re-derived from the schema: the
    question is what the Dispatcher sends, and it sends the intersection of the
    contract's projectable fields with what the payload declares.
    """
    resolved = resolve_repo_integration_contract(
        config_text=repo_root.joinpath(*_CONFIG_RELPATH).read_text(encoding="utf-8"),
        default_branch=None,
    )
    pairs = contract_run_inputs(resolved=resolved, declared=declared_inputs(repo_root=repo_root))
    return frozenset(pair.split("=", 1)[0] for pair in pairs)


def payload_findings(*, repo_root: Path) -> list[Finding]:
    """Every way this repository's payload breaks the seam equivalence."""
    occurrences = payload_occurrences(repo_root=repo_root)
    findings = position_findings(occurrences=occurrences)
    findings.extend(
        equivalence_findings(
            referenced=referenced_integration_inputs(occurrences=occurrences),
            rendered=rendered_input_names(repo_root=repo_root),
        )
    )
    findings.extend(scoping_findings(declared=declared_inputs(repo_root=repo_root)))
    findings.extend(schema_findings())
    return findings


def control_failures(*, repo_root: Path) -> list[str]:
    """Why a clean report on `repo_root` would not be trustworthy, if it would not."""
    failures = _discovery_failures(occurrences=payload_occurrences(repo_root=repo_root))
    fixture = fixture_path(repo_root=repo_root)
    if not fixture.is_file():
        failures.append(f"matcher control: the fixture is missing at {fixture}")
        return failures
    occurrences = graph_occurrences(text=fixture.read_text(encoding="utf-8"), venue=fixture.name)
    failures.extend(_matcher_failures(occurrences=occurrences))
    return failures


def _discovery_failures(*, occurrences: list[Occurrence]) -> list[str]:
    """That the scan of the REAL payload still returns the tokens that are in it."""
    seen = {
        occurrence.name for occurrence in occurrences if occurrence.position == _ADAPTER_POSITION
    }
    return [
        f"discovery control: the graph scan found no `{_ADAPTER_POSITION}` token for node {node}"
        for node, candidates in sorted(NODE_INPUT_CANDIDATES.items())
        if not any(name in seen for name in candidates)
    ]


def _matcher_failures(*, occurrences: list[Occurrence]) -> list[str]:
    """That the fixture's known non-rendered positions still reach a reported finding."""
    expected = non_rendered_occurrences(occurrences=occurrences)
    positions = {occurrence.position for occurrence in expected}
    failures = [
        f"matcher control: the fixture produced no non-rendered occurrence at `{position}`"
        for position in ("timeout", OUTSIDE_ATTRIBUTE_POSITION)
        if position not in positions
    ]
    reported = position_findings(occurrences=occurrences)
    if len(reported) != len(expected):
        counts = f"{len(expected)} non-rendered occurrence(s), {len(reported)} finding(s)"
        failures.append(f"matcher control: the fixture and its findings disagree — {counts}")
    return failures


def main() -> int:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )
    log = structlog.get_logger("seam_equivalence")
    repo_root = Path.cwd()
    findings = payload_findings(repo_root=repo_root)
    for finding in findings:
        log.error(finding.detail, kind=finding.kind, input_name=finding.subject)
    failures = control_failures(repo_root=repo_root)
    for failure in failures:
        log.error(failure, kind="control")
    return 1 if findings or failures else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
