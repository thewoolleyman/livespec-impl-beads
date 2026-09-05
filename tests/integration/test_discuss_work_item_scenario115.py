"""Scenario 115 — `discuss-work-item` stands by over the context envelope.

Binds `SPECIFICATION/scenarios.md` "Scenario 115 — `discuss-work-item` stands
by over the context envelope and resumes without chat history" and the
`discuss-work-item` operation contract it realizes, in
`SPECIFICATION/contracts.md`.

`discuss-work-item` is a HEAVYWEIGHT AUTHORED skill: its behavior lives in one
shared `.claude-plugin/prose/discuss-work-item.md` artifact plus thin
per-runtime bindings, so there is no single CLI wrapper to drive. That shapes
what an honest integration-tier binding can assert, and this module is built to
keep both halves real rather than letting the prose half swallow the whole
test:

- The two claims that are BEHAVIOR — that the subject's context is assembled by
  the `context` primitive, and that a plan resumes from that envelope with no
  chat history — are exercised as behavior, by running the shipped `context`
  CLI over a fixture tenant built through the client's public write verbs and
  reading the resume-bearing fields back out of the emitted envelope. Nothing
  is stood in.
- The claim that a maintainer ruling becomes a durable scope event is likewise
  exercised through the REAL Planning Lane primitive against the REAL
  store/client seam, and READ BACK through `read_timeline` — the same
  read-back the prose requires, because a ledger comment is not verified by the
  write call returning.
- Only the two claims that are genuinely about the SHIPPED ARTIFACT — the
  stand-by/explicit-instruction gate, and the registered name — are asserted
  against the prose and the three runtime bindings, because those are the
  things the operation actually is.

The registration case is the one with a silent failure mode worth naming. The
contract forbids the name `plan` because it collides with the Claude Code
built-in on autocomplete, and `plan` ALSO remains a live sibling operation of
this plugin. So "a skill named plan exists" is true and carries no information;
the discriminating assertion is that the discuss surface is registered under
its own name in all three runtimes AND that the sibling `plan` bindings still
point at their own prose, which is what proves the two were not conflated.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from livespec_orchestrator_beads_fabro._beads_client import (
    FakeBeadsClient,
    IssueDraft,
    make_beads_client,
    reset_fake_singleton,
)
from livespec_orchestrator_beads_fabro.commands.context import main
from livespec_orchestrator_beads_fabro.commands.plan import read_timeline, record_scope_event
from livespec_orchestrator_beads_fabro.types import StoreConfig

if TYPE_CHECKING:
    from collections.abc import Sequence

_OPERATION = "discuss-work-item"
_PLUGIN = "livespec-orchestrator-beads-fabro"
_REPO_ROOT = Path(__file__).resolve().parents[2]
_CLAUDE_DIR = _REPO_ROOT / ".claude-plugin"
_PROSE = _CLAUDE_DIR / "prose" / f"{_OPERATION}.md"
_CLAUDE_BINDING = _CLAUDE_DIR / "skills" / _OPERATION / "SKILL.md"
_CODEX_BINDING = _CLAUDE_DIR / ".codex-plugin" / "skills" / _OPERATION / "SKILL.md"
_PI_BINDING = _CLAUDE_DIR / ".pi-plugin" / "skills" / f"{_PLUGIN}-{_OPERATION}" / "SKILL.md"

_EPIC_ID = "bd-ib-s115"
_CHILD_ID = "bd-ib-s115.1"
_SLUG = "discuss-work-item-stand-by"
_NEXT_ACTION_TEXT = "Land the discuss-work-item stand-by slice."


@pytest.fixture(autouse=True)
def _hermetic_tenant(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("LIVESPEC_BEADS_FAKE", "1")
    reset_fake_singleton()
    yield
    reset_fake_singleton()


def _config() -> StoreConfig:
    return StoreConfig(
        tenant="livespec-impl-beads",
        prefix="bd-ib",
        server_user="livespec-impl-beads",
        database="livespec-impl-beads",
        bd_path="bd",
        fake=True,
    )


def _client() -> FakeBeadsClient:
    client = make_beads_client(config=_config())
    assert isinstance(client, FakeBeadsClient)
    return client


def _draft(
    *,
    issue_id: str,
    issue_type: str = "task",
    metadata: dict[str, Any] | None = None,
    spec_id: str | None = None,
) -> IssueDraft:
    return IssueDraft(
        issue_id=issue_id,
        issue_type=issue_type,
        title=f"{issue_id} title",
        description=f"{issue_id} description",
        assignee=None,
        created_at="2026-09-05T00:00:00Z",
        metadata={"rank": "a1", **(metadata or {})},
        labels=["origin:freeform"],
        spec_id=spec_id,
        parent_id=None,
    )


def _fixture_tenant(*, project_root: Path) -> None:
    """A live plan epic carrying everything a cold resume must recover."""
    client = _client()
    _ = client.create_issue(
        draft=_draft(
            issue_id=_EPIC_ID,
            issue_type="epic",
            metadata={
                "plan_slug": _SLUG,
                "next_action": {
                    "kind": "impl",
                    "ref": _CHILD_ID,
                    "text": _NEXT_ACTION_TEXT,
                },
            },
            spec_id=f"plan:{_SLUG}",
        )
    )
    _ = client.create_issue(
        draft=_draft(issue_id=_CHILD_ID, spec_id="obligation-discuss-work-item")
    )
    client.add_comment(issue_id=_EPIC_ID, body="Console decision D6 ratified this surface.")
    _ = (project_root / ".livespec.jsonc").write_text(
        '{"livespec-orchestrator-beads-fabro": {"connection": {"prefix": "bd-ib"}}}',
        encoding="utf-8",
    )
    plan_dir = project_root / "plan" / _SLUG
    _ = (plan_dir / "research").mkdir(parents=True)
    _ = (plan_dir / "associated_work_item_id").write_text(f"{_EPIC_ID}\n", encoding="utf-8")
    _ = (plan_dir / "research" / "001-charter.md").write_text("charter\n", encoding="utf-8")


def _envelope(*, project_root: Path, key: str, capsys: pytest.CaptureFixture[str]) -> Any:
    """Assemble one subject's context the way the operation is required to."""
    assert main(argv=[key, "--json", "--project-root", str(project_root)]) == 0
    return json.loads(capsys.readouterr().out)


def _prose() -> str:
    """The shipped prose with every whitespace run collapsed to one space.

    Prose is hard-wrapped, so a needle copied out of the rendered sentence
    matches while the same needle straddling a line break does not — a probe
    that can only fail silently. Normalizing BOTH sides removes the wrap as a
    variable, so a failing needle means the prose does not say the thing rather
    than that it says it across two lines.
    """
    return " ".join(_PROSE.read_text(encoding="utf-8").split())


def _frontmatter_name(*, path: Path) -> str:
    """The `name:` field of a binding's frontmatter block.

    Indexing rather than falling back to a sentinel: a binding with no `name:`
    is a structural defect, and returning `""` for it would compare unequal to
    the expected name and report as a WRONG name rather than a missing one.
    """
    declared = [
        line.removeprefix("name:").strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith("name:")
    ]
    return declared[0]


def _missing(*, haystack: str, needles: Sequence[str]) -> list[str]:
    return [needle for needle in needles if needle not in haystack]


def test_scenario115_the_skill_assembles_its_subject_through_the_context_primitive(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The subject's whole context comes from `context`, not a hand-rolled read.

    The behavior half runs the shipped primitive over the fixture tenant and
    asserts it returns a populated envelope for the epic. The artifact half
    asserts the prose routes the assembly there and names the not-found refusal
    it must surface, because a prose artifact that merely mentioned `context`
    while re-deriving the read would produce a second, divergent reading.
    """
    _fixture_tenant(project_root=tmp_path)

    envelope = _envelope(project_root=tmp_path, key=_EPIC_ID, capsys=capsys)

    assert envelope["epic"]["id"] == _EPIC_ID
    assert envelope["subject"]["plan_slug"] == _SLUG
    assert [child["id"] for child in envelope["children"]] == [_CHILD_ID]

    prose = _prose()
    assert (
        _missing(
            haystack=prose,
            needles=(
                "`context` primitive",
                "--json",
                "Do NOT hand-roll a per-item read",
                "exits 3 naming the missing key",
            ),
        )
        == []
    )


def test_scenario115_the_skill_resumes_a_plan_from_the_envelope_alone(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A cold session recovers the next action and current facts with no history.

    Every field a resume needs is read off ONE envelope: the typed next action
    (kind, ref and the human sentence), the epic's own facts, its children, its
    recorded comments, and the research the anchor resolves. The control is
    that the same envelope is produced from the `plan_slug` alone — a session
    resuming from a slug has nothing else to go on.
    """
    _fixture_tenant(project_root=tmp_path)

    by_slug = _envelope(project_root=tmp_path, key=_SLUG, capsys=capsys)
    by_id = _envelope(project_root=tmp_path, key=_EPIC_ID, capsys=capsys)

    assert by_slug == by_id
    assert by_slug["next_action"] == {
        "kind": "impl",
        "ref": _CHILD_ID,
        "text": _NEXT_ACTION_TEXT,
    }
    assert [comment["text"] for comment in by_slug["comments"]] == [
        "Console decision D6 ratified this surface."
    ]
    assert by_slug["research"]["files"] == [f"plan/{_SLUG}/research/001-charter.md"]

    prose = _prose()
    assert (
        _missing(
            haystack=prose,
            needles=(
                "no chat history and MUST NOT need any",
                "the typed field wins",
            ),
        )
        == []
    )


def test_scenario115_a_maintainer_ruling_is_recorded_as_a_plan_scope_event(
    tmp_path: Path,
) -> None:
    """The ruling becomes a durable scope event, read back through the timeline.

    A ruling left in the session is lost at the next resume, which is exactly
    the guarantee the envelope-alone case above depends on — so the write goes
    through the Planning Lane primitive and is verified by re-reading the
    ledger, never by the write call returning.
    """
    _fixture_tenant(project_root=tmp_path)

    record_scope_event(
        config=_config(),
        epic_id=_EPIC_ID,
        requirements=("The stand-by skill is registered as discuss-work-item.",),
        deferrals=("The console chat pane is deferred to the console track.",),
        author="maintainer",
        now="2026-09-05T06:00:00Z",
    )

    scope_entries = [
        entry
        for entry in read_timeline(config=_config(), epic_id=_EPIC_ID)
        if entry.kind == "scope"
    ]
    assert len(scope_entries) == 1
    assert "The stand-by skill is registered as discuss-work-item." in scope_entries[0].body
    assert "The console chat pane is deferred to the console track." in scope_entries[0].body
    assert scope_entries[0].author == "maintainer"

    prose = _prose()
    assert (
        _missing(
            haystack=prose,
            needles=(
                "record_scope_event(...)",
                "Do not leave a ruling in chat",
                "store-write consent discipline",
                "read_timeline(...)",
            ),
        )
        == []
    )


def test_scenario115_the_skill_drives_a_lifecycle_action_only_on_explicit_instruction() -> None:
    """Ambiguity resolves to standing by and asking, never to acting.

    This is an artifact-tier assertion by nature: the gate lives in the prose a
    conversational skill executes, and there is no CLI to drive. What makes it
    load-bearing rather than decorative is that it pins BOTH directions — the
    affirmative explicit-instruction rule and the negative that a recorded next
    action is a pointer rather than a mandate, which is the reading that would
    otherwise turn every resume into a dispatch.
    """
    prose = _prose()

    assert (
        _missing(
            haystack=prose,
            needles=(
                "ONLY on an explicit maintainer instruction",
                "An implicit or ambiguous request MUST NOT trigger a drive",
                "is a pointer rather than a mandate",
                "ask for explicit confirmation",
            ),
        )
        == []
    )


def test_scenario115_the_skill_is_registered_under_the_non_colliding_name() -> None:
    """Registered as `discuss-work-item` in all three runtimes; never as `plan`.

    `plan` is a live sibling operation here, so its mere existence proves
    nothing. The discriminator is that each runtime's discuss binding declares
    the discuss name and reads the discuss prose, while the sibling `plan`
    bindings still declare `plan` and read `plan.md` — which is what shows the
    two surfaces were added side by side rather than one being renamed onto the
    other.
    """
    assert _PROSE.is_file()
    for binding in (_CLAUDE_BINDING, _CODEX_BINDING, _PI_BINDING):
        assert binding.is_file(), f"missing runtime binding: {binding}"
        assert f"prose/{_OPERATION}.md" in binding.read_text(encoding="utf-8")

    assert _frontmatter_name(path=_CLAUDE_BINDING) == _OPERATION
    assert _frontmatter_name(path=_CODEX_BINDING) == _OPERATION
    assert _frontmatter_name(path=_PI_BINDING) == f"{_PLUGIN}-{_OPERATION}"

    # The sibling `plan` surface is untouched: not renamed, not absorbed.
    plan_binding = _CLAUDE_DIR / "skills" / "plan" / "SKILL.md"
    assert _frontmatter_name(path=plan_binding) == "plan"
    assert "prose/plan.md" in plan_binding.read_text(encoding="utf-8")

    # And the structural gate that enforces every runtime binding knows the op,
    # so a future binding deletion is a check failure rather than a silent gap.
    codex_check = (_REPO_ROOT / "dev-tooling" / "checks" / "codex_plugin_structure.py").read_text(
        encoding="utf-8"
    )
    assert f'"{_OPERATION}",' in codex_check

    assert "It is NOT named `plan`" in _prose()
