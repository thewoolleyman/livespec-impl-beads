"""Tests for the consumer-side tolerant envelope parse."""

from __future__ import annotations

import json
from typing import Any

from livespec_orchestrator_beads_fabro.commands._needs_attention_envelope import (
    parse_envelope,
    render_envelope_markdown,
)


def _entry(**overrides: Any) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "id": "hygiene:capacity:repo",
        "kind": "hygiene",
        "urgency": "high",
        "summary": "Capacity reached.",
        "source_ref": {"repo": "repo", "work_item": None, "path": None},
        "handoff": {"kind": "shell", "command": "true", "action_id": None},
    }
    entry.update(overrides)
    return entry


def _envelope(*entries: Any) -> str:
    return json.dumps({"attention": list(entries)})


def test_a_well_formed_envelope_consumes_every_item_and_skips_nothing() -> None:
    consumed = parse_envelope(envelope=_envelope(_entry(), _entry(id="impl:bd-1", kind="impl")))

    assert [item.id for item in consumed.items] == ["hygiene:capacity:repo", "impl:bd-1"]
    assert consumed.skipped == ()
    assert consumed.items[0].repo == "repo"
    assert consumed.items[0].handoff_kind == "shell"


def test_an_unknown_kind_is_well_formed_and_never_a_skip_reason() -> None:
    consumed = parse_envelope(envelope=_envelope(_entry(kind="not-yet-invented")))

    assert consumed.skipped == ()
    assert consumed.items[0].kind == "not-yet-invented"


def test_each_malformed_shape_skips_only_itself_with_a_naming_reason() -> None:
    consumed = parse_envelope(
        envelope=_envelope(
            "not-an-object",
            _entry(summary=17),
            _entry(urgency="catastrophic"),
            _entry(source_ref={"repo": None}),
            _entry(source_ref="not-an-object"),
            _entry(handoff={"kind": "shell"}),
            _entry(id="plan:kept"),
        )
    )

    assert [item.id for item in consumed.items] == ["plan:kept"]
    assert [entry.position for entry in consumed.skipped] == [0, 1, 2, 3, 4, 5]
    reasons = [entry.reason for entry in consumed.skipped]
    assert reasons[0] == "entry is not a JSON object"
    assert "summary" in reasons[1]
    assert "urgency" in reasons[2]
    assert reasons[3] == reasons[4] == "missing or malformed `source_ref.repo`"
    assert "handoff" in reasons[5]


def test_an_unreadable_payload_surfaces_instead_of_failing_silently() -> None:
    for envelope in ("{not json", json.dumps(["a", "list"]), json.dumps({"attention": 3})):
        consumed = parse_envelope(envelope=envelope)

        assert consumed.items == ()
        assert [entry.position for entry in consumed.skipped] == [-1]


def test_the_two_unreadable_payload_shapes_report_distinct_reasons() -> None:
    assert parse_envelope(envelope="{not json").skipped[0].reason == "envelope is not valid JSON"
    assert (
        parse_envelope(envelope=json.dumps({"other": []})).skipped[0].reason
        == 'envelope carries no "attention" array'
    )


def test_an_empty_envelope_renders_the_empty_notice() -> None:
    assert render_envelope_markdown(envelope=_envelope()) == "No attention items.\n"


def test_rendering_annotates_only_the_unknown_kinds() -> None:
    rendered = render_envelope_markdown(
        envelope=_envelope(_entry(), _entry(id="plan:x", kind="from-the-future"))
    )

    assert "- `hygiene:capacity:repo` [high] Capacity reached." in rendered
    assert "- `plan:x` [high] (kind `from-the-future`) Capacity reached." in rendered
    assert "  - Handoff: `true`" in rendered
    assert "## Skipped malformed items" not in rendered


def test_rendering_surfaces_a_whole_envelope_failure_distinctly_from_an_item() -> None:
    whole = render_envelope_markdown(envelope="{not json")
    per_item = render_envelope_markdown(envelope=_envelope("not-an-object", _entry()))

    assert "- envelope: envelope is not valid JSON" in whole
    assert "- item 0: entry is not a JSON object" in per_item
    assert "- `hygiene:capacity:repo`" in per_item
