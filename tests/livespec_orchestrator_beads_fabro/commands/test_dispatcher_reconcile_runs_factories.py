"""Tests for enumerating the factories a reconciliation pass must survey."""

from __future__ import annotations

import json
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands import _dispatcher_reconcile_runs_factories as fac


def test_every_declared_factory_plus_the_default_is_enumerated() -> None:
    names = fac.declared_factory_names(
        block={
            "factories": {"vps": {"server": "https://vps"}, "hp": {"server": "https://hp"}},
            "default_factory": "hp",
        }
    )

    assert names == ("hp", "vps")


def test_a_default_naming_an_undeclared_factory_is_still_enumerated() -> None:
    names = fac.declared_factory_names(
        block={"factories": {"hp": {"server": "https://hp"}}, "default_factory": "ghost"}
    )

    assert names == ("hp", "ghost")


def test_a_block_declaring_nothing_enumerates_nothing() -> None:
    assert fac.declared_factory_names(block={}) == ()
    assert fac.declared_factory_names(block={"factories": "nope", "default_factory": ""}) == ()


def test_targets_resolve_per_factory_and_a_named_factory_narrows_the_survey(
    tmp_path: Path,
) -> None:
    _ = (tmp_path / ".livespec.jsonc").write_text(
        json.dumps(
            {
                "livespec-orchestrator-beads-fabro": {
                    "dispatcher": {
                        "default_factory": "hp",
                        "factories": {
                            "hp": {"server": "https://hp.example:32276"},
                            "vps": {"server": "https://vps.example:32276"},
                        },
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    every = fac.reconcile_factory_targets(repo=tmp_path)
    narrowed = fac.reconcile_factory_targets(repo=tmp_path, factory="vps")

    assert [(target.name, target.server) for target in every] == [
        ("hp", "https://hp.example:32276"),
        ("vps", "https://vps.example:32276"),
    ]
    assert [target.name for target in narrowed] == ["vps"]
