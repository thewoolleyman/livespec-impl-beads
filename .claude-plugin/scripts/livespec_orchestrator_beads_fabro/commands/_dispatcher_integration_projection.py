"""The seams a resolved integration contract PROJECTS into, and nothing else.

`SPECIFICATION/contracts.md`, the repository-integration-contract section's
resolve-once-project-everywhere clause, requires the Dispatcher to resolve the
contract exactly ONCE per dispatch, on the host, at plan-build time, and then to
make every seam -- the host janitor argv, the `fabro run` inputs, the prompt
variables, the prepare-step parameters -- a PROJECTION of that one resolved
object. This module is the projection side of that rule: it turns a
`ResolvedIntegrationContract` into what each seam consumes, and it is the only
place that knows what any seam's wire format looks like.

THE SANDBOX RECEIVES VALUES AND NEVER RESOLVES. `CONTRACT_INPUT_NAMES` is the
closed set of fields that cross the host/sandbox boundary; every other schema
field is answered on the host (the master-CI preflight, the host janitor's own
check-suite and bootstrap recipe, the livespec-core clone) and has no business
being restated inside a run. A field crossing that boundary does so as a NAMED
WORKFLOW INPUT, because the three sandbox-side consumers -- the `--input` pairs
themselves, the node prompts, and the `[[run.prepare.steps]]` scripts -- all read
`inputs.<name>` and therefore all read ONE value. That is what makes them
projections of the same object rather than three restatements of it.

AN INPUT THE WORKFLOW DOES NOT DECLARE IS NEVER SENT. fabro REJECTS an `--input`
name the run config does not declare, so the rendering is INTERSECTED with what
the dispatched workflow actually declares -- the same discipline
`_dispatcher_acp_nodes` already keeps for adapter inputs, and for the same
reason: the set of inputs that exist is a property of the DISPATCHED workflow,
not of this plugin's build, so a target still carrying an older payload is sent
what it can receive and nothing more.

COMMAND-SHAPED VALUES CROSS AS ONE SHELL WORD-LIST. The contract holds argv
tuples so nothing downstream re-tokenizes; a workflow input is a scalar, so the
tuple is rendered with `shlex.join` at this one seam and read back by a
`[[run.prepare.steps]]` script that is itself a shell command line. The join
happens HERE rather than at each consumer for the same reason the split happens
once in the resolver.
"""

from __future__ import annotations

import re
import shlex
from collections.abc import Collection, Mapping
from dataclasses import dataclass

from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_resolver import (
    Declared,
    Defective,
    FleetDefault,
    IntegrationResolution,
    ResolvedIntegrationContract,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_integration_schema import (
    DEFAULT_BRANCH_FIELD,
    MERGE_MODE_FIELD,
    PREPARE_TOOLCHAIN_LEFTHOOK_FIELD,
    PREPARE_TOOLCHAIN_MISE_FIELD,
    SANDBOX_CHECK_SUITE_FIELD,
    SANDBOX_EXEMPT_MARKER_FIELD,
)

__all__: list[str] = [
    "CONTRACT_INPUT_NAMES",
    "MERGE_METHOD_FLAGS",
    "ContractPrepareParameters",
    "contract_prepare_parameters",
    "contract_prompt_variables",
    "contract_run_inputs",
    "contract_workflow_inputs",
    "integration_contract_journal_record",
    "merge_method_flag",
    "workflow_declared_inputs",
]

# The CLOSED set of fields that cross into the sandbox, and the workflow-input
# name each crosses as. Keyed by the schema field's own attribute so the mapping
# cannot name a point the schema does not carry; the input names match the
# attributes deliberately, because a rendered input and the `inputs.*` token a
# prompt or prepare step reads have to be the same word for the ratified
# seam-equivalence check to be able to compare the two sets at all.
CONTRACT_INPUT_NAMES: Mapping[str, str] = {
    SANDBOX_CHECK_SUITE_FIELD.attribute: "sandbox_check_suite",
    PREPARE_TOOLCHAIN_MISE_FIELD.attribute: "prepare_toolchain_mise",
    PREPARE_TOOLCHAIN_LEFTHOOK_FIELD.attribute: "prepare_toolchain_lefthook",
    SANDBOX_EXEMPT_MARKER_FIELD.attribute: "sandbox_exempt_marker",
    DEFAULT_BRANCH_FIELD.attribute: "default_branch",
    MERGE_MODE_FIELD.attribute: "merge_mode",
}

# How each admitted `dispatcher.merge_mode` value spells itself as the `gh pr
# merge` METHOD flag. The mapping is total over the schema's admitted set, so a
# value that resolved at all has a flag; an unresolvable merge mode carries the
# name sentinel instead and is refused rather than defaulted, on the same
# reasoning every other unresolved point records.
MERGE_METHOD_FLAGS: Mapping[str, str] = {
    "rebase": "--rebase",
    "squash": "--squash",
}

# `[run.inputs]` and its body, up to the next table header. A full TOML parser is
# unavailable on the pinned Python (tomllib is 3.11+; the family vendors no TOML
# library) and the run config is repo-owned with a stable shape, so a
# section-scoped regex is sufficient and dependency-free -- the same reasoning
# `_dispatcher_overlay._toml_section_string` records.
_RUN_INPUTS_RE = re.compile(r"(?ms)^\[run\.inputs\][ \t]*\r?$(?P<body>.*?)(?=^\[|\Z)")
_INPUT_ASSIGNMENT_RE = re.compile(r'(?m)^(?P<key>\w+)[ \t]*=[ \t]*"(?P<value>[^"]*)"[ \t]*\r?$')


@dataclass(frozen=True, kw_only=True)
class ContractPrepareParameters:
    """The integration values the sandbox's `[[run.prepare.steps]]` consume.

    Named as PARAMETERS rather than as rendered scripts because the scripts
    themselves live in the dispatched workflow payload, which templates
    `inputs.*`; this is the value side of that template, projected from the one
    resolved contract so the prepare chain and the node prompts cannot disagree
    about which check-suite or which exemption marker this repository uses.

    A toolchain premise an adopter does not carry resolves to the explicit
    no-op -- the empty argv -- which is a VALUE the ratified
    factory-sandbox-toolchain-disposition clause defines, never an absence to be
    inferred from silence.
    """

    sandbox_exempt_marker: str
    toolchain_mise: tuple[str, ...]
    toolchain_lefthook: tuple[str, ...]


def contract_prompt_variables(*, resolved: ResolvedIntegrationContract) -> Mapping[str, str]:
    """Project the sandbox-facing fields as the variables a run renders from.

    ONE mapping, consumed three ways: `contract_run_inputs` renders it as the
    `fabro run --input` pairs, fabro binds those pairs to the `inputs.*` tokens
    the node prompts template, and the same tokens are what the prepare-step
    scripts read. Any seam that wants one of these values reads it from here
    rather than from configuration, which is the whole of the resolve-once rule
    expressed as a function.
    """
    contract = resolved.contract
    return {
        name: _scalar(value=getattr(contract, attribute))
        for attribute, name in CONTRACT_INPUT_NAMES.items()
    }


def contract_run_inputs(
    *, resolved: ResolvedIntegrationContract, declared: Collection[str]
) -> tuple[str, ...]:
    """Render the `--input name=value` pairs this dispatch's workflow can receive.

    INTERSECTED with `declared` -- the input names the dispatched run config
    actually declares -- because fabro rejects an `--input` naming an input the
    workflow does not declare. A workflow that declares none of these fields
    receives none of them and runs on its own committed literals exactly as
    before, so supplying the values is separable from the payload edit that
    templates them.
    """
    variables = contract_prompt_variables(resolved=resolved)
    return tuple(f"{name}={variables[name]}" for name in sorted(variables) if name in set(declared))


def contract_prepare_parameters(
    *, resolved: ResolvedIntegrationContract
) -> ContractPrepareParameters:
    """Project the prepare chain's parameters off the one resolved contract."""
    contract = resolved.contract
    return ContractPrepareParameters(
        sandbox_exempt_marker=contract.sandbox_exempt_marker,
        toolchain_mise=contract.prepare_toolchain_mise,
        toolchain_lefthook=contract.prepare_toolchain_lefthook,
    )


def merge_method_flag(*, resolved: ResolvedIntegrationContract) -> str | None:
    """The `gh pr merge` METHOD flag the resolved merge mode projects to; None when unresolved.

    None is not "use the fleet default": it is the caller's cue that
    `dispatcher.merge_mode` resolved NOTHING, which the auto-merge argv reports
    rather than papering over with a strategy this repository never chose. A
    resolved mode always maps, because the schema admits only members of
    `MERGE_METHOD_FLAGS`.
    """
    return MERGE_METHOD_FLAGS.get(resolved.contract.merge_mode)


def contract_workflow_inputs(*, committed_text: str) -> frozenset[str]:
    """The CONTRACT input names a committed run config declares.

    Filtered to `CONTRACT_INPUT_NAMES` so the adapter inputs and the two
    policy inputs sharing the `[run.inputs]` table are not mistaken for
    integration points; an absent table declares nothing.
    """
    names = frozenset(CONTRACT_INPUT_NAMES.values())
    return frozenset(workflow_declared_inputs(committed_text=committed_text)) & names


def workflow_declared_inputs(*, committed_text: str) -> Mapping[str, str]:
    """Every input a committed run config's `[run.inputs]` table declares, with its default.

    The generic scan behind both input-name questions the dispatch path asks --
    which adapter inputs exist, and which integration inputs exist. It lives in
    ONE place because two copies of a `[run.inputs]` regex is exactly how the
    two questions would come to disagree about what a payload declares.
    """
    section = _RUN_INPUTS_RE.search(committed_text)
    if section is None:
        return {}
    return {
        match.group("key"): match.group("value")
        for match in _INPUT_ASSIGNMENT_RE.finditer(section.group("body"))
    }


def integration_contract_journal_record(
    *, resolved: ResolvedIntegrationContract
) -> dict[str, object]:
    """Project the resolved contract for the dispatch record.

    Every field reports the VALUE the run will use plus the ARM that produced it
    -- declared, fleet-default, or defective -- so a reader can tell an adopter's
    own declaration from the fleet convention without re-deriving the
    resolution. `defects` is restated as its own list because a reader asking
    "what was wrong with this repository at dispatch time" should not have to
    scan every field to find out.
    """
    return {
        "integration_contract": {
            "schema_version": resolved.contract.schema_version,
            "fields": {
                attribute: {
                    "key": resolution.key,
                    "arm": _arm(resolution=resolution),
                    "value": _resolution_value(resolution=resolution),
                }
                for attribute, resolution in sorted(resolved.resolutions.items())
            },
            "defects": [
                {"key": defect.key, "reason": defect.reason} for defect in resolved.defects
            ],
        }
    }


def _arm(*, resolution: IntegrationResolution) -> str:
    if isinstance(resolution, Declared):
        return "declared"
    if isinstance(resolution, FleetDefault):
        return "fleet-default"
    return "defective"


def _resolution_value(*, resolution: IntegrationResolution) -> str | None:
    """A resolution's value as one scalar; None where it resolved nothing."""
    if isinstance(resolution, Defective):
        return None
    return _scalar(value=resolution.value)


def _scalar(*, value: str | tuple[str, ...]) -> str:
    """One integration value as the single string a workflow input carries."""
    return value if isinstance(value, str) else shlex.join(value)
