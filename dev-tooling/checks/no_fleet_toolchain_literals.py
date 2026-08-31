# pyright: reportMissingImports=none, reportMissingTypeStubs=none, reportUnknownMemberType=none, reportUnknownVariableType=none, reportUnknownArgumentType=none
"""no_fleet_toolchain_literals — no fleet premise is hardcoded outside the fleet-defaults module.

`SPECIFICATION/constraints.md`, the fleet-toolchain-literal-ban clause, requires
that a fleet-toolchain literal -- this fleet's tool runner, a fleet recipe name,
its hook manager, its shared dev-tooling package, its step timer, or a bare
default-branch name used as a ref -- appear in the dispatcher package and the
workflow payload ONLY inside the single fleet-defaults module the
`RepoIntegrationContract` schema designates, so a new hardcoded premise cannot be
reintroduced by a later change.

WHY A GATE RATHER THAN THE SCHEMA ALONE. Every one of these literals used to sit
at its point of use, and each was a silent assumption imposed on an adopter that
carries none of this fleet's tooling. Gathering them into the fleet-defaults
module fixed the instances that existed; nothing stopped the NEXT one. A defaults
module is only load-bearing if putting a fleet literal anywhere else fails a
build.

This module owns the SCOPE and the POLICY; the sibling matcher module owns what
counts as a literal in the first place.

ONE ALLOW-LIST, MEASURED AND SELF-RETIRING. It is not an exemption in the
"this is fine" sense; it names work already sliced under the
typed-repository-integration-contract plan epic:

- `MEASURED_EXEMPTIONS` names the dispatcher-package sites that still resolve a
  fleet premise from a constant. Each was measured, not guessed, and each is a
  ratified-conversion follow-up rather than a judgement that the site is correct.

THE PAYLOAD HAS NO ALLOW-LIST. The workflow payload and the prompt files are
scanned in full: the typed-workflow-inputs carrier (C5-payload) converted every
fleet premise they carried into an `inputs.<name>` projection of the resolved
integration contract and deleted the list that had excused them while that
conversion was pending. A fleet literal reintroduced into the payload is a
finding, exactly as one in the package is.

A STALE ENTRY IN THE LIST IS A FAILURE, which is what makes those deletions
mechanical rather than remembered: the moment a site is converted, its entry
stops matching and this check fails until the entry is removed. An allow-list
that can only be removed by hand is an allow-list that outlives its reason.

FOUR POSITIVE CONTROLS, because this check reports an ABSENCE for a living. A
broken pattern or a mis-scoped glob would make it permanently green while printing
exactly what a clean repo prints, so `main` refuses to report a clean scan unless
all four hold: the DISCOVERY controls assert the package and payload walks reached
the modules and files that carry the literals; the DESIGNATION control asserts the
exempt module is the one the schema actually designates, so the exemption cannot
drift onto a module the contract never named; and the MATCHER control asserts the
checked-in fixture still produces findings through the same parse/match path.

Output discipline: `print` and direct `sys.stderr.write` are banned here, so
diagnostics flow through structlog (JSON to stderr).
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent
_SCRIPTS = _REPO_ROOT / ".claude-plugin" / "scripts"
for _path in (_SCRIPT_DIR, _SCRIPTS, _SCRIPTS / "_vendor"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

# structlog is the only sanctioned stderr surface for an enforcement script (per
# the `no_write_direct` ban on direct `sys.stderr.write`). It is not vendored in
# this repo's own tree, so it is imported from the installed shared dev-tooling
# package's vendored copy, whose path is added to `sys.path` below.
#
# The matcher beside it is a sibling PRIVATE module in this same directory. This
# file's own directory is on `sys.path` above, so the sibling import resolves
# both under `python <path>` and under the importlib-by-path load the paired
# test uses.
import livespec_dev_tooling  # noqa: E402
from _fleet_toolchain_literals_matcher import (  # noqa: E402  — sibling private import
    Finding,
    source_findings,
    text_findings,
)

_DT_VENDOR = Path(livespec_dev_tooling.__file__).resolve().parent / "_vendor"
if str(_DT_VENDOR) not in sys.path:
    sys.path.insert(0, str(_DT_VENDOR))

import structlog  # noqa: E402

__all__: list[str] = [
    "DISCOVERY_ANCHORS",
    "FLEET_DEFAULTS_MODULE",
    "MEASURED_EXEMPTIONS",
    "SCHEMA_MODULE",
    "control_failures",
    "main",
    "package_findings",
    "payload_findings",
    "payload_paths",
    "stale_exemptions",
    "unexempted_findings",
]

# The single fleet-defaults module. Package-relative, and asserted below to be
# the module the schema designates rather than merely a module named here.
FLEET_DEFAULTS_MODULE = "commands/_dispatcher_integration_defaults.py"
SCHEMA_MODULE = "commands/_dispatcher_integration_schema.py"

# Package-relative paths the walk MUST reach: the two contract modules, plus the
# argv builder that carries the largest measured residue. A walk that misses one
# is mis-scoped, and its clean report means nothing.
DISCOVERY_ANCHORS: tuple[str, ...] = (
    "commands/_dispatcher_fabro_argv.py",
    FLEET_DEFAULTS_MODULE,
    SCHEMA_MODULE,
)

# (package-relative path, literal) pairs MEASURED to still resolve a fleet
# premise from a constant. Each is a conversion follow-up, not an approval.
MEASURED_EXEMPTIONS: frozenset[tuple[str, str]] = frozenset(
    {
        # `pull_primary_argv` and `janitor_trust_argv` still prepend this fleet's
        # runner wrapper (and, inside the former's shell string, still fall back
        # to a bare branch name) to commands run against the governed repository.
        ("commands/_dispatcher_fabro_argv.py", "mise"),
        # The command name whose arguments are recipe names in a repository's
        # justfile. It reads an ADOPTER's declared recipe rather than imposing
        # one, but the discrimination belongs in the contract, not in a parser
        # constant.
        ("commands/_dispatcher_hook_install_recipe.py", "just"),
        # A second default-branch resolution carrying the constant fallback the
        # ratified default-branch-resolution clause retired; the shared resolver
        # in the default-branch module deliberately falls back to nothing.
        ("commands/_dispatcher_probe_wiring.py", "master"),
        # The merged-PR search pins its `--base` and filters its `baseRefName`
        # against a branch an adopter may not have.
        ("commands/_dispatcher_reconcile_merged_pr.py", "master"),
        # The dry-run source push falls back to a branch name when `HEAD` is
        # detached.
        ("commands/_dispatcher_source_preflight.py", "master"),
        # This repo's OWN release/master probe refs. Not an imposition on a
        # governed repository, but still a constant the contract should carry.
        ("commands/_dispatcher_staleness_gate.py", "refs/heads/master"),
    }
)

_PACKAGE_RELPATH = ".claude-plugin/scripts/livespec_orchestrator_beads_fabro"
_PAYLOAD_RELPATH = ".claude-plugin/.fabro/workflows"
_FIXTURE_RELPATH = "dev-tooling/checks/fixtures/fleet_toolchain_literal_control.py.txt"
_PAYLOAD_SUFFIXES = frozenset({".fabro", ".md", ".toml"})
_FINDING_MESSAGE = "fleet-toolchain literal outside the fleet-defaults module"


def _module_paths(*, package: Path) -> list[Path]:
    return sorted(package.rglob("*.py"))


def payload_paths(*, repo_root: Path) -> list[Path]:
    """Every payload and prompt file the payload scan walks."""
    root = repo_root / _PAYLOAD_RELPATH
    return sorted(path for path in root.rglob("*") if path.suffix in _PAYLOAD_SUFFIXES)


def package_findings(*, repo_root: Path) -> list[Finding]:
    """Every literal in the dispatcher package, measured exemptions NOT applied."""
    package = repo_root / _PACKAGE_RELPATH
    findings: list[Finding] = []
    for path in _module_paths(package=package):
        relpath = path.relative_to(package).as_posix()
        if relpath == FLEET_DEFAULTS_MODULE:
            continue
        findings.extend(source_findings(source=path.read_text(encoding="utf-8"), relpath=relpath))
    return findings


def payload_findings(*, repo_root: Path) -> list[Finding]:
    """Every literal in the workflow payload; nothing excuses one there."""
    findings: list[Finding] = []
    for path in payload_paths(repo_root=repo_root):
        findings.extend(
            text_findings(
                text=path.read_text(encoding="utf-8"),
                relpath=path.relative_to(repo_root).as_posix(),
            )
        )
    return findings


def unexempted_findings(*, repo_root: Path) -> list[Finding]:
    """Every literal the measured exemptions do not excuse, plus every payload literal."""
    package = [
        finding
        for finding in package_findings(repo_root=repo_root)
        if (finding.relpath, finding.literal) not in MEASURED_EXEMPTIONS
    ]
    return package + payload_findings(repo_root=repo_root)


def stale_exemptions(*, repo_root: Path) -> list[str]:
    """Allow-list entries the tree no longer needs, so a converted site cannot stay exempt."""
    measured = {
        (finding.relpath, finding.literal) for finding in package_findings(repo_root=repo_root)
    }
    return [
        f"measured exemption {entry} matches no literal; the site is converted, so delete it"
        for entry in sorted(MEASURED_EXEMPTIONS)
        if entry not in measured
    ]


def _designates_defaults(*, source: str) -> bool:
    module_name = Path(FLEET_DEFAULTS_MODULE).stem
    return any(
        isinstance(node, ast.ImportFrom)
        and node.module is not None
        and node.module.endswith(module_name)
        for node in ast.walk(ast.parse(source))
    )


def control_failures(*, repo_root: Path) -> list[str]:
    """Why a clean scan of `repo_root` would not be trustworthy, if it would not."""
    failures: list[str] = []
    package = repo_root / _PACKAGE_RELPATH
    discovered = {path.relative_to(package).as_posix() for path in _module_paths(package=package)}
    failures.extend(
        f"discovery control: the walk of {package} did not reach {anchor}"
        for anchor in DISCOVERY_ANCHORS
        if anchor not in discovered
    )
    if not payload_paths(repo_root=repo_root):
        failures.append(f"discovery control: the walk of {_PAYLOAD_RELPATH} reached no file")
    # The exemption is only legitimate while the schema still designates that
    # module; without this control it could silently drift onto a module the
    # contract never named.
    schema = package / SCHEMA_MODULE
    if not schema.is_file() or not _designates_defaults(source=schema.read_text(encoding="utf-8")):
        failures.append(
            f"designation control: {SCHEMA_MODULE} does not import {FLEET_DEFAULTS_MODULE}"
        )
    fixture = repo_root / _FIXTURE_RELPATH
    if not fixture.is_file():
        failures.append(f"matcher control: the positive-control fixture is missing at {fixture}")
        return failures
    if not source_findings(source=fixture.read_text(encoding="utf-8"), relpath=fixture.name):
        failures.append(f"matcher control: no fleet-toolchain literal was found in {fixture}")
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
    log = structlog.get_logger("no_fleet_toolchain_literals")
    repo_root = Path.cwd()
    failures = control_failures(repo_root=repo_root)
    for failure in failures:
        log.error(
            "positive control failed; this scan cannot report a trustworthy absence",
            detail=failure,
        )
    stale = stale_exemptions(repo_root=repo_root)
    for entry in stale:
        log.error("allow-list entry is stale; a converted site must not stay exempt", detail=entry)
    findings = unexempted_findings(repo_root=repo_root)
    for finding in findings:
        log.error(
            _FINDING_MESSAGE,
            path=finding.relpath,
            line=finding.lineno,
            token=finding.token,
            literal=finding.literal,
        )
    return 1 if failures or stale or findings else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
