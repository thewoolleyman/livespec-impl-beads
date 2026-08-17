"""Tests for dispatcher Fabro failure-detail parsing."""

from __future__ import annotations

from livespec_orchestrator_beads_fabro.commands._dispatcher_fabro_failure import (
    FabroFailureDetail,
    fabro_failure_outcome_detail,
    parse_fabro_failure_detail,
)


def test_parse_fabro_failure_detail_extracts_nested_failure_block() -> None:
    detail = parse_fabro_failure_detail(
        stdout=(
            '{"events": [{"payload": {"failure": {'
            '"causes": [7, "script failed with exit 2"], '
            '"category": "deterministic", '
            '"signature": "fix|deterministic|script failed"}}}]}'
        )
    )

    assert detail == FabroFailureDetail(
        cause="script failed with exit 2",
        category="deterministic",
        signature="fix|deterministic|script failed",
    )


def test_parse_fabro_failure_detail_returns_none_for_unusable_payloads() -> None:
    assert parse_fabro_failure_detail(stdout="not json") is None
    assert parse_fabro_failure_detail(stdout="[]") is None
    assert parse_fabro_failure_detail(stdout='{"failure": {"causes": [7, "  "]}}') is None
    assert parse_fabro_failure_detail(stdout='{"failure": "not an object"}') is None


def test_parse_fabro_failure_detail_accepts_category_without_causes() -> None:
    detail = parse_fabro_failure_detail(
        stdout='{"failure": {"causes": "not a list", "category": "infra"}}'
    )

    assert detail == FabroFailureDetail(cause=None, category="infra", signature=None)


def test_fabro_failure_outcome_detail_formats_available_fields() -> None:
    assert (
        fabro_failure_outcome_detail(
            failure=FabroFailureDetail(
                cause=None,
                category="deterministic",
                signature="fix|deterministic|script failed",
            ),
            fallback="ACP turn failed",
        )
        == "category=deterministic; signature=fix|deterministic|script failed"
    )
    assert (
        fabro_failure_outcome_detail(failure=None, fallback="ACP turn failed") == "ACP turn failed"
    )
    assert (
        fabro_failure_outcome_detail(
            failure=FabroFailureDetail(cause=None, category=None, signature=None),
            fallback="ACP turn failed",
        )
        == "ACP turn failed"
    )
