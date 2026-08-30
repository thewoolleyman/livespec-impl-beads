"""Tests for the shared default-branch resolution every dispatch-path stage uses.

Covers the default-branch-resolution clause of `SPECIFICATION/contracts.md`:
the two-route rule, and the refusal that replaces a fallback to the `master`
literal when neither route can name a branch.
"""

from __future__ import annotations

import importlib
from pathlib import Path

from livespec_orchestrator_beads_fabro.commands._dispatcher_engine import CommandResult

_MODULE = "livespec_orchestrator_beads_fabro.commands._dispatcher_default_branch"
_ORIGIN_HEAD_ARGV = ["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"]
_REPO_VIEW_ARGV = [
    "gh",
    "repo",
    "view",
    "--json",
    "defaultBranchRef",
    "--jq",
    ".defaultBranchRef.name",
]


class RouteRunner:
    def __init__(self, *, origin_head: CommandResult, repo_view: CommandResult) -> None:
        self.origin_head = origin_head
        self.repo_view = repo_view
        self.calls: list[list[str]] = []

    def run(
        self,
        *,
        argv: list[str],
        cwd: Path,
        timeout_seconds: float,
        env: dict[str, str] | None = None,
        stdin: int | None = None,
    ) -> CommandResult:
        _ = (cwd, timeout_seconds, env, stdin)
        self.calls.append(argv)
        return self.origin_head if argv == _ORIGIN_HEAD_ARGV else self.repo_view


def _silent() -> CommandResult:
    return CommandResult(exit_code=1, stdout="", stderr="no answer")


def test_default_branch_module_exists_before_import() -> None:
    module_path = (
        Path(".claude-plugin/scripts/livespec_orchestrator_beads_fabro/commands")
        / "_dispatcher_default_branch.py"
    )
    assert module_path.is_file()


def test_git_route_answers_first_and_strips_the_remote_prefix(tmp_path: Path) -> None:
    module = importlib.import_module(_MODULE)
    runner = RouteRunner(
        origin_head=CommandResult(exit_code=0, stdout="origin/main\n", stderr=""),
        repo_view=CommandResult(exit_code=0, stdout="never-asked\n", stderr=""),
    )

    resolved = module.resolve_default_branch(repo=tmp_path, runner=runner)

    assert resolved == "main"
    # The forge is not consulted when git already answered.
    assert runner.calls == [_ORIGIN_HEAD_ARGV]


def test_forge_route_answers_when_git_fails(tmp_path: Path) -> None:
    module = importlib.import_module(_MODULE)
    runner = RouteRunner(
        origin_head=_silent(),
        repo_view=CommandResult(exit_code=0, stdout="trunk\n", stderr=""),
    )

    resolved = module.resolve_default_branch(repo=tmp_path, runner=runner)

    assert resolved == "trunk"
    assert runner.calls == [_ORIGIN_HEAD_ARGV, _REPO_VIEW_ARGV]


def test_forge_route_answers_when_git_exits_zero_with_nothing_to_say(tmp_path: Path) -> None:
    module = importlib.import_module(_MODULE)
    runner = RouteRunner(
        origin_head=CommandResult(exit_code=0, stdout="  \n", stderr=""),
        repo_view=CommandResult(exit_code=0, stdout="main\n", stderr=""),
    )

    resolved = module.resolve_default_branch(repo=tmp_path, runner=runner)

    # A zero exit is not an answer; an empty one leaves the branch unnamed.
    assert resolved == "main"
    assert runner.calls == [_ORIGIN_HEAD_ARGV, _REPO_VIEW_ARGV]


def test_both_routes_silent_resolves_to_none_rather_than_the_master_literal(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(_MODULE)
    runner = RouteRunner(origin_head=_silent(), repo_view=_silent())

    assert module.resolve_default_branch(repo=tmp_path, runner=runner) is None


def test_forge_route_answering_emptily_resolves_to_none(tmp_path: Path) -> None:
    module = importlib.import_module(_MODULE)
    runner = RouteRunner(
        origin_head=_silent(),
        repo_view=CommandResult(exit_code=0, stdout="\n", stderr=""),
    )

    assert module.resolve_default_branch(repo=tmp_path, runner=runner) is None
