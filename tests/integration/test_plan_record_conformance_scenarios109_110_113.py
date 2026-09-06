"""Scenarios 109, 110 and 113 — the shipped plan-record conformance check, armed.

Binds `SPECIFICATION/scenarios.md` "Scenario 109 — Every epic carries a
canonical, tenant-unique `plan_slug`", "Scenario 110 — The
`associated_work_item_id` anchor matches its epic in both directions" and
"Scenario 113 — A plan epic closed without completeness-review evidence is
reported", and the `SPECIFICATION/contracts.md` plan-record conformance clauses
they realize.

WHAT IS DRIVEN. The check itself lives in the fleet's shared checks package
beside `plan_epic_parity` — the ratified home the contract names — so this
repository's leg is a CONSUMER leg: `just check` wires
`check-plan-record-conformance` beside `check-plan-epic-parity` under the same
armed-only lever, and these cases drive the module that recipe runs
(`livespec_dev_tooling.checks.plan_record_conformance`) over a fixture tenant.
The whole check runs as production code — the arming gate, the tenant prefix
read off the repository's own `.livespec.jsonc`, the ledger read through the
shipped `bd_items_reader` export path, every slug, anchor and timeline verdict,
the delegated lifecycle leg, and the structured report. Only the COMMENT reader
is injected, through the seam the module ships for it: comments have no on-disk
export shape, so the alternative is the `bd` subprocess this tier does not
spawn.

WHY THE FIXTURE CARRIES CONTROLS. Each case asserts the offender AND a
same-family record the check must leave alone, because a check that reported
everything would satisfy the offender assertion just as well: `clean-plan` is a
correctly slugged, correctly anchored epic, and `archived-evidenced` is a closed
plan epic carrying real completeness-review evidence. Both must appear in NO
finding.

THE ARMING GATE IS ASSERTED IN BOTH DIRECTIONS in one case, for the same reason.
An unarmed run reporting nothing is indistinguishable from a fixture that
produces nothing, so the self-skip case re-runs the SAME fixture armed and
requires the verdicts to appear.

THE DELEGATED LEG IS ASSERTED RATHER THAN ASSUMED. `plan_lifecycle_parity` is
delegated to `plan_epic_parity`, which reads its OWN lever, so the family can be
half-armed. The scenario-109 case asserts the run says which lever governed that
leg and what it returned — otherwise a silently skipped delegate reads exactly
like a clean one. That lever is deliberately deleted from the environment here:
left inherited, an ambient arming would run the delegate over the fixture and
add a verdict these exact-equality assertions do not expect.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from livespec_dev_tooling.checks import plan_record_conformance

_RUN_LEVER = "LIVESPEC_RUN_PLAN_RECORD_CONFORMANCE"
_PARITY_LEVER = "LIVESPEC_RUN_PLAN_EPIC_PARITY"
_CRED_ENV = "BEADS_DOLT_PASSWORD"
_ANCHOR_FILENAME = "associated_work_item_id"

# The fixture tenant's epics. `clean` and `evidenced` are the controls the check
# must leave unreported; the other three each carry exactly one ratified defect.
_CLEAN = "bd-ib-s109clean"
_UNTAGGED = "bd-ib-s109untagged"
_MISMATCH = "bd-ib-s110mismatch"
_UNEVIDENCED = "bd-ib-s113unevidenced"
_EVIDENCED = "bd-ib-s113evidenced"

_CLEAN_SLUG = "clean-plan"
_MISMATCH_SLUG = "mismatched-plan"
_ORPHAN_SLUG = "orphan-anchor"
_EVIDENCED_SLUG = "archived-evidenced"
_UNEVIDENCED_SLUG = "archived-unevidenced"

_LIVESPEC_CONFIG = json.dumps(
    {
        "implementation": {"plugin": "livespec-orchestrator-beads-fabro"},
        "livespec-orchestrator-beads-fabro": {"connection": {"prefix": "bd-ib"}},
    }
)

_EVIDENCE_COMMENT = (
    "plan-completeness-review-evidence\n"
    "reviewer-identity: agent:independent-reviewer\n"
    "separate-reviewer: true\n"
    "attests-complete-requirement-coverage: true\n"
    "\n"
    "Every requirement carrier under the plan is covered."
)
_PLAIN_HANDOFF_COMMENT = (
    "plan-handoff-entry\nauthor: console\ntimestamp: 2026-09-05T10:00:00Z\n\nWrapping up."
)

# The five verdicts the fixture earns, in the order the check emits them: the
# slug family, then the anchor family (per directory, then the converse
# direction), then the timeline family.
_EXPECTED_FINDINGS = [
    {
        "check_id": "plan_slug_present",
        "subject": _UNTAGGED,
        "verdict": "error",
        "event": "epic carries no `plan_slug` metadata",
    },
    {
        "check_id": "plan_anchor_consistent",
        "subject": f"plan/{_MISMATCH_SLUG}",
        "verdict": "error",
        "event": (
            f"anchor names epic {_CLEAN} whose plan_slug {_CLEAN_SLUG!r} differs from the "
            "directory name"
        ),
    },
    {
        "check_id": "plan_anchor_present",
        "subject": f"plan/{_ORPHAN_SLUG}",
        "verdict": "error",
        "event": f"plan directory has no `{_ANCHOR_FILENAME}` file",
    },
    {
        "check_id": "plan_anchor_consistent",
        "subject": _MISMATCH,
        "verdict": "error",
        "event": f"epic's plan_slug names plan/{_MISMATCH_SLUG}, whose anchor holds {_CLEAN!r}",
    },
    {
        "check_id": "plan_close_evidence",
        "subject": _UNEVIDENCED,
        "verdict": "error",
        "event": "closed plan epic carries no completeness-review evidence comment",
    },
]


def _epic(
    *,
    epic_id: str,
    status: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """One ledger record, `omitempty`-sparse exactly as `bd` exports one."""
    record: dict[str, Any] = {"id": epic_id, "type": "epic", "status": status}
    if metadata is not None:
        record["metadata"] = metadata
    return record


def _pointer(*, ref: str) -> dict[str, Any]:
    """A conformant typed `next_action`, so an open epic owes no pointer verdict."""
    return {"kind": "impl", "ref": ref, "text": f"run impl:{ref} in the factory"}


def _records() -> list[dict[str, Any]]:
    return [
        _epic(
            epic_id=_CLEAN,
            status="ready",
            metadata={
                "plan_slug": _CLEAN_SLUG,
                "next_action": _pointer(ref="bd-ib-s109slice"),
                "last_session": "console 2026-09-06T00:00:00Z",
            },
        ),
        # No `metadata` key at all: the sparse shape `plan_slug_present` exists
        # to report, and the one a subscripting reader would raise on.
        _epic(epic_id=_UNTAGGED, status="ready"),
        _epic(
            epic_id=_MISMATCH,
            status="ready",
            metadata={
                "plan_slug": _MISMATCH_SLUG,
                "next_action": _pointer(ref="bd-ib-s110slice"),
                "last_session": "console 2026-09-06T00:00:00Z",
            },
        ),
        _epic(epic_id=_UNEVIDENCED, status="closed", metadata={"plan_slug": _UNEVIDENCED_SLUG}),
        _epic(epic_id=_EVIDENCED, status="closed", metadata={"plan_slug": _EVIDENCED_SLUG}),
    ]


def _timelines() -> dict[str, list[dict[str, Any]]]:
    return {
        _UNEVIDENCED: [
            {"text": _PLAIN_HANDOFF_COMMENT, "created_at": "2026-09-05T10:00:00Z"},
        ],
        _EVIDENCED: [
            {"text": _EVIDENCE_COMMENT, "created_at": "2026-09-05T11:00:00Z"},
        ],
    }


def _write_anchor(*, directory: Path, anchor: str) -> None:
    directory.mkdir(parents=True)
    _ = (directory / _ANCHOR_FILENAME).write_text(f"{anchor}\n", encoding="utf-8")


def _fixture_tenant(*, repo: Path) -> None:
    """A repository holding this tenant's ledger export and its plan records."""
    _ = (repo / ".livespec.jsonc").write_text(_LIVESPEC_CONFIG, encoding="utf-8")
    beads = repo / ".beads"
    beads.mkdir()
    _ = (beads / "issues.jsonl").write_text(
        "".join(f"{json.dumps(record)}\n" for record in _records()), encoding="utf-8"
    )
    plan = repo / "plan"
    _write_anchor(directory=plan / _CLEAN_SLUG, anchor=_CLEAN)
    # The forward mismatch: this directory answers to the epic next door.
    _write_anchor(directory=plan / _MISMATCH_SLUG, anchor=_CLEAN)
    # A live plan record with no anchor file at all.
    (plan / _ORPHAN_SLUG).mkdir(parents=True)
    _write_anchor(directory=plan / "archive" / _EVIDENCED_SLUG, anchor=_EVIDENCED)
    _write_anchor(directory=plan / "archive" / _UNEVIDENCED_SLUG, anchor=_UNEVIDENCED)


def _run(*, repo: Path, seen_repos: list[Path]) -> int:
    """Run the check as the `check-plan-record-conformance` recipe runs it."""
    timelines = _timelines()

    def read_comments(*, repo: Path, item_id: str) -> list[dict[str, Any]]:
        seen_repos.append(repo)
        return timelines.get(item_id, [])

    assert repo == Path.cwd()
    return plan_record_conformance.main(comment_reader=read_comments)


def _lines(*, captured: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in captured.splitlines() if line.strip()]


def _findings(*, captured: str) -> list[dict[str, Any]]:
    """Every emitted verdict, projected to the fields the contract requires."""
    return [
        {key: line[key] for key in ("check_id", "subject", "verdict", "event")}
        for line in _lines(captured=captured)
        if "verdict" in line
    ]


def _remediations(*, captured: str) -> dict[str, str]:
    return {
        line["check_id"]: line["remediation"]
        for line in _lines(captured=captured)
        if "verdict" in line
    }


@pytest.fixture(name="armed_tenant")
def _armed_tenant_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """The fixture tenant, cwd, and the family armed except for the delegate."""
    _fixture_tenant(repo=tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(_RUN_LEVER, "1")
    monkeypatch.setenv(_CRED_ENV, "fixture-tenant-password")
    monkeypatch.delenv(_PARITY_LEVER, raising=False)
    return tmp_path


def test_scenario109_an_epic_carrying_no_plan_slug_is_reported_as_an_error_verdict(
    armed_tenant: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    seen_repos: list[Path] = []

    exit_code = _run(repo=armed_tenant, seen_repos=seen_repos)

    captured = capsys.readouterr().err
    assert exit_code == 1
    # The whole verdict set, so a later case's offender cannot be a stray hit.
    assert _findings(captured=captured) == _EXPECTED_FINDINGS
    slug_findings = [
        finding
        for finding in _findings(captured=captured)
        if finding["check_id"].startswith("plan_slug_")
    ]
    assert slug_findings == [_EXPECTED_FINDINGS[0]]
    assert (
        "write the epic's canonical `plan_slug` metadata"
        in (_remediations(captured=captured)["plan_slug_present"])
    )
    # The delegated lifecycle leg names its own lever and its verdict, so a
    # half-armed family cannot read as a clean one.
    delegation = [line for line in _lines(captured=captured) if "delegate" in line]
    assert [
        (line["delegate"], line["delegate_run_lever"], line["delegate_exit_code"])
        for line in delegation
    ] == [("plan_epic_parity", _PARITY_LEVER, 0)]
    assert seen_repos == [armed_tenant] * len(_records())


def test_scenario110_the_anchor_pair_is_graded_from_the_directory_and_from_the_epic(
    armed_tenant: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    seen_repos: list[Path] = []

    exit_code = _run(repo=armed_tenant, seen_repos=seen_repos)

    captured = capsys.readouterr().err
    assert exit_code == 1
    anchor_findings = [
        finding
        for finding in _findings(captured=captured)
        if finding["check_id"].startswith("plan_anchor_")
    ]
    # Three verdicts: the absent anchor, the directory-side mismatch, and the
    # SAME mismatch reported from the epic side. A one-directional check passes
    # a tenant where every anchor is legible and one epic points elsewhere.
    assert anchor_findings == [
        _EXPECTED_FINDINGS[1],
        _EXPECTED_FINDINGS[2],
        _EXPECTED_FINDINGS[3],
    ]
    assert {finding["subject"] for finding in anchor_findings} == {
        f"plan/{_MISMATCH_SLUG}",
        f"plan/{_ORPHAN_SLUG}",
        _MISMATCH,
    }
    # The two correctly anchored records — one live, one archived — are silent.
    subjects = {finding["subject"] for finding in _findings(captured=captured)}
    assert subjects.isdisjoint(
        {
            f"plan/{_CLEAN_SLUG}",
            f"plan/archive/{_EVIDENCED_SLUG}",
            f"plan/archive/{_UNEVIDENCED_SLUG}",
        }
    )


def test_scenario113_a_closed_plan_epic_without_completeness_evidence_is_reported(
    armed_tenant: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    seen_repos: list[Path] = []

    exit_code = _run(repo=armed_tenant, seen_repos=seen_repos)

    captured = capsys.readouterr().err
    assert exit_code == 1
    evidence_findings = [
        finding
        for finding in _findings(captured=captured)
        if finding["check_id"] == "plan_close_evidence"
    ]
    assert evidence_findings == [_EXPECTED_FINDINGS[4]]
    # The control: a closed plan epic whose timeline DOES carry the three
    # attestations is reported by nothing at all. Both closed epics carry a
    # comment, so presence-of-a-comment cannot be what separated them.
    assert _EVIDENCED not in {finding["subject"] for finding in _findings(captured=captured)}
    assert (
        "durable independent completeness-review evidence"
        in (_remediations(captured=captured)["plan_close_evidence"])
    )


def test_the_armed_only_lever_governs_the_run_and_its_absence_self_skips(
    armed_tenant: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    seen_repos: list[Path] = []
    monkeypatch.delenv(_RUN_LEVER)

    unarmed = _run(repo=armed_tenant, seen_repos=seen_repos)

    unarmed_output = capsys.readouterr().err
    assert unarmed == 0
    assert _findings(captured=unarmed_output) == []
    skip_line = _lines(captured=unarmed_output)
    assert [(line["run_lever"], line["credential"]) for line in skip_line] == [
        (_RUN_LEVER, _CRED_ENV)
    ]
    # No ledger was read: the gate is ahead of the tenant read, not a filter on it.
    assert seen_repos == []

    # The control, on the SAME fixture: armed, the verdicts appear. Without it,
    # a tenant that produces nothing would pass the assertions above.
    monkeypatch.setenv(_RUN_LEVER, "1")
    armed = _run(repo=armed_tenant, seen_repos=seen_repos)

    assert armed == 1
    assert _findings(captured=capsys.readouterr().err) == _EXPECTED_FINDINGS
