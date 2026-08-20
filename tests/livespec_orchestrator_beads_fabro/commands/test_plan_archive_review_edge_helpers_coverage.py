"""Coverage for legacy helper methods in the Red probe test module."""

from __future__ import annotations

import importlib.util
import types
from collections.abc import Callable
from pathlib import Path


def _load_edge_test_module() -> types.ModuleType:
    module_path = Path(__file__).with_name("test_plan_archive_review_edges.py")
    spec = importlib.util.spec_from_file_location(
        "plan_archive_review_edges_for_coverage", module_path
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_legacy_edge_clients_keep_children_surface_available_for_probe() -> None:
    module = _load_edge_test_module()

    factories = [
        getattr(module, name)
        for name in (
            "_MalformedParentChildEdgeClient",
            "_RelationCoverageClient",
            "_ClosedTrackedChildClient",
        )
    ]
    assert all(isinstance(factory, Callable) for factory in factories)
    malformed, relation, closed = (factory() for factory in factories)

    assert malformed.children(parent_id="bd-ib-epic") == []
    assert relation.children(parent_id="bd-ib-epic") == []
    assert closed.children(parent_id="bd-ib-closed-epic") == []
