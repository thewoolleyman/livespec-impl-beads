"""Coverage tests for dispatcher readiness diagnostic helpers."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest
from livespec_orchestrator_beads_fabro.commands import _sibling_status_lookup as sibling_sut
from livespec_orchestrator_beads_fabro.commands._dispatcher_readiness_diagnostics import (
    not_ready_requested_items_error,
)
from livespec_orchestrator_beads_fabro.commands._sibling_status_lookup import (
    make_sibling_status_lookup,
    sibling_dependency_diagnostics,
)
from livespec_orchestrator_beads_fabro.types import DependsOnRaw, WorkItem
from livespec_runtime.cross_repo.types import RefStatus

_SIBLING_REPO = "sibling-repo"
_MANIFEST = '{"owner": "someowner", "fleet": [{"repo": "sibling-repo"}]}'


def _item(
    *,
    id_: str = "consumer",
    status: str = "ready",
    depends_on: tuple[DependsOnRaw, ...] = (),
) -> WorkItem:
    return WorkItem(
        id=id_,
        type="task",
        status=status,  # type: ignore[arg-type]
        title=id_,
        description="d",
        origin="freeform",
        gap_id=None,
        rank="a1",
        assignee=None,
        depends_on=depends_on,
        captured_at="2026-05-19T00:00:00Z",
        resolution=None,
        reason=None,
        audit=None,
        superseded_by=None,
    )


def _project_root(*, tmp_path: Path) -> Path:
    project_root = tmp_path / "orchestrator"
    project_root.mkdir()
    (tmp_path / _SIBLING_REPO).mkdir()
    return project_root


def _install_fleet(
    *,
    monkeypatch: pytest.MonkeyPatch,
    manifest_text: str | None,
    items: list[WorkItem],
) -> None:
    def _fetch() -> str | None:
        return manifest_text

    def _load(**_kwargs: object) -> list[WorkItem]:
        return list(items)

    monkeypatch.setattr(sibling_sut, "fetch_fleet_manifest_text", _fetch)
    monkeypatch.setattr(sibling_sut, "load_items", _load)


def test_lookup_diagnostic_cache_miss_resolves_before_returning_none(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_root(tmp_path=tmp_path)
    _install_fleet(
        monkeypatch=monkeypatch,
        manifest_text=_MANIFEST,
        items=[_item(id_="sib-1", status="done")],
    )
    lookup = make_sibling_status_lookup(project_root=project_root)

    assert lookup.diagnostic(repo=_SIBLING_REPO, work_item_id="sib-1") is None


def test_sibling_dependency_diagnostics_ignores_malformed_sibling_entry() -> None:
    item = _item(
        depends_on=(
            cast(
                DependsOnRaw,
                {"kind": "sibling_work_item", "repo": 7, "work_item_id": "sib-1"},
            ),
        )
    )

    assert (
        sibling_dependency_diagnostics(
            item=item,
            sibling_status_lookup=_LookupWithoutDiagnostics(),
        )
        == ()
    )


def test_sibling_dependency_diagnostics_ignores_closed_sibling(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_root(tmp_path=tmp_path)
    _install_fleet(
        monkeypatch=monkeypatch,
        manifest_text=_MANIFEST,
        items=[_item(id_="sib-1", status="done")],
    )
    item = _item(
        depends_on=(
            {
                "kind": "sibling_work_item",
                "repo": _SIBLING_REPO,
                "work_item_id": "sib-1",
            },
        )
    )

    assert (
        sibling_dependency_diagnostics(
            item=item,
            sibling_status_lookup=make_sibling_status_lookup(project_root=project_root),
        )
        == ()
    )


def test_sibling_dependency_diagnostics_ignores_unknown_without_message() -> None:
    item = _item(
        depends_on=(
            {
                "kind": "sibling_work_item",
                "repo": _SIBLING_REPO,
                "work_item_id": "sib-1",
            },
        )
    )

    assert (
        sibling_dependency_diagnostics(
            item=item,
            sibling_status_lookup=_LookupWithoutDiagnostics(),
        )
        == ()
    )


def test_not_ready_requested_items_error_tolerates_absent_item(tmp_path: Path) -> None:
    assert (
        not_ready_requested_items_error(
            requested_ids={"missing"},
            items=[],
            repo=tmp_path,
        )
        == "ERROR: requested work-item(s) not in the ready set: missing\n"
    )


def test_not_ready_requested_items_error_names_claimed_item(tmp_path: Path) -> None:
    assert not_ready_requested_items_error(
        requested_ids={"claimed"},
        items=[_item(id_="claimed", status="active")],
        repo=tmp_path,
    ) == (
        "ERROR: requested work-item(s) already claimed by a dispatch: claimed; "
        "status=active assignee=<unassigned>; Inspect the dispatch journal and "
        "reconcile-runs for a stranded claim before checking dependencies.\n"
    )


class _LookupWithoutDiagnostics:
    def __call__(self, repo: str, work_item_id: str) -> RefStatus:
        _ = (repo, work_item_id)
        return RefStatus.UNKNOWN

    def diagnostic(self, *, repo: str, work_item_id: str) -> str | None:
        _ = (repo, work_item_id)
        return None
