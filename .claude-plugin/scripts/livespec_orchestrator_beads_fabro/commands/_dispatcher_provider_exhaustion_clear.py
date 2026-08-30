"""Operator-facing early clearance of an observed provider-exhaustion record.

Two routes retire an observed-exhaustion record on their own: its bounded
expiry elapses, or a SUCCESSFUL dispatch against the same provider falsifies
it. Neither is reachable by an operator who KNOWS the provider is available
again — they just restarted the self-hosted model, freed the GPU, fixed the
config — because the admission gate refuses the very dispatch that would
falsify the record. Waiting out the bounded default is the only thing left,
and for a provider the operator directly controls that default is a guess
about someone else's rate-limit cadence.

This module is the third route, and it is deliberately HUMAN-ONLY: one
appended `provider-exhaustion-cleared` line that the reverse scan in
`_dispatcher_provider_exhaustion` reads as "the newest observation for this
provider is already retired". Nothing is rewritten or deleted — the store is
append-only by construction, so the observation, and the override of it,
both survive as separate readable facts.

Two refusals are what keep this from becoming a SECOND AUTOMATIC-EXPIRY PATH,
which is the one thing it must not become:

- A `--reason` that is absent or blank is refused. A clearance asserts a fact
  about the world that no observation supports, so the assertion has to be
  stated on the record rather than inferred from the act.
- An invocation asserting NO identity is refused OUTRIGHT — unconditionally,
  not under the `dispatcher.require_invoker` dial that governs the dispatch
  entry points. The fallback `unattributed:<user>@<host>` mark is exactly the
  identity an unattended process carries by default, so refusing it is what
  makes "a human triggered this" a property of the record instead of a hope.
  An automated caller CAN still assert an identity, and that is the point:
  doing so is an explicit, journaled, attributable act rather than a silent
  second expiry rule.

A clearance for a provider holding no unexpired record is refused too, before
anything is written: there is nothing to clear, and appending a clearance
against no observation would leave a record asserting an override that never
happened.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._dispatcher_command_common import (
    EXIT_PRECONDITION_ERROR,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_invoker import (
    FALLBACK_SOURCE,
    INVOKER_ENV_VAR,
    INVOKER_FLAG,
    add_invoker_argument,
    invoker_from_args,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_io import (
    JournalFile,
    utc_now_iso,
)
from livespec_orchestrator_beads_fabro.commands._dispatcher_paths import journal_path
from livespec_orchestrator_beads_fabro.commands._dispatcher_provider_exhaustion import (
    active_provider_exhaustion,
    provider_exhaustion_clearance_record,
)
from livespec_orchestrator_beads_fabro.io import write_stderr, write_stdout

__all__: list[str] = [
    "add_clear_provider_exhaustion_arguments",
    "run_clear_provider_exhaustion_command",
]

_BLANK_REASON_REFUSAL = (
    "ERROR: clear-provider-exhaustion refused: --reason is blank.\n"
    "A clearance asserts the provider is available again, which no observation "
    "supports; state why on the record.\n"
)
_NOTHING_HELD_REFUSAL = (
    "ERROR: clear-provider-exhaustion refused: no unexpired exhaustion record is held "
    "for provider {provider}; nothing to clear.\n"
)


def _unattributed_refusal(*, invoker: str) -> str:
    """The refusal text for an invocation that asserted no identity.

    A function rather than a template constant because it names the two
    accepted identity inputs, and naming them is what makes the refusal
    actionable rather than merely correct.
    """
    return (
        "ERROR: clear-provider-exhaustion refused: this invocation asserted no identity "
        f"(resolved {invoker} as {FALLBACK_SOURCE}).\n"
        "Manual clearance is a human act by construction and is never taken on an "
        f"unattributed invocation: pass {INVOKER_FLAG} <id> or set the {INVOKER_ENV_VAR} "
        "environment variable.\n"
    )


def add_clear_provider_exhaustion_arguments(*, parser: argparse.ArgumentParser) -> None:
    """Attach the operator-clearance flag surface to its subparser."""
    add_invoker_argument(parser=parser)
    _ = parser.add_argument("--repo", dest="repo", default=None)
    _ = parser.add_argument(
        "--provider",
        dest="provider",
        required=True,
        help="the model provider whose unexpired exhaustion record to retire",
    )
    _ = parser.add_argument(
        "--reason",
        dest="reason",
        required=True,
        help="why the operator knows this provider is available again",
    )
    _ = parser.add_argument("--journal", dest="journal", default=None)


def run_clear_provider_exhaustion_command(*, args: argparse.Namespace) -> int:
    """Retire one provider's unexpired exhaustion record on an operator's say-so."""
    reason = str(args.reason).strip()
    if not reason:
        _ = write_stderr(text=_BLANK_REASON_REFUSAL)
        return EXIT_PRECONDITION_ERROR
    identity = invoker_from_args(args=args)
    if identity.invoker_source == FALLBACK_SOURCE:
        _ = write_stderr(text=_unattributed_refusal(invoker=identity.invoker))
        return EXIT_PRECONDITION_ERROR
    repo = Path(args.repo) if args.repo is not None else Path.cwd()
    path = journal_path(args=args, repo=repo)
    held = active_provider_exhaustion(
        provider=args.provider,
        journal_path=path,
        now_iso=utc_now_iso(),
    )
    if held is None:
        _ = write_stderr(text=_NOTHING_HELD_REFUSAL.format(provider=args.provider))
        return EXIT_PRECONDITION_ERROR
    JournalFile(path=path, identity=identity).append(
        record=provider_exhaustion_clearance_record(provider=held.provider, reason=reason)
    )
    _ = write_stdout(
        text=(
            f"CLEARED  {held.provider}  held until {held.record_expires_at}  "
            f"by {identity.invoker}: {reason}\n"
        )
    )
    return 0
