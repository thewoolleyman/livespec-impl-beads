"""PR-stage prompt freshness and bounded publish retry contract."""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PR_PROMPT = (
    _REPO_ROOT
    / ".claude-plugin"
    / ".fabro"
    / "workflows"
    / "implement-work-item"
    / "prompts"
    / "pr.md"
)
# The default branch is the resolved integration-contract field, rendered by
# fabro from `inputs.default_branch`; the prompt never spells a branch name.
_FETCH = "git fetch origin {{ inputs.default_branch }} --quiet"
_REBASE = "git rebase origin/{{ inputs.default_branch }}"
_PUSH = "git push -u origin HEAD:refs/heads/feat/<work-item-id>"
_LEASE_PUSH = (
    "git push --force-with-lease="
    "refs/heads/feat/<work-item-id>:<observed-remote-tip> "
    "origin HEAD:refs/heads/feat/<work-item-id>"
)
_WORKFLOWS_PERMISSION_REJECTION = (
    "refusing to allow a GitHub App to create or update workflow "
    ".github/workflows/ci.yml without workflows permission"
)
_NON_FAST_FORWARD_REJECTION = "non-fast-forward"


def _prompt_text() -> str:
    return _PR_PROMPT.read_text(encoding="utf-8")


def test_pr_stage_rebases_current_master_immediately_before_first_push() -> None:
    """A stale-base sandbox is refreshed before the publish branch is created."""
    prompt = _prompt_text()

    fetch_index = prompt.index(_FETCH)
    rebase_index = prompt.index(_REBASE)
    push_index = prompt.index(_PUSH)

    assert fetch_index < rebase_index < push_index
    assert "After a" in prompt
    assert "successful rebase, re-check committed work" in prompt


def test_pr_stage_retries_once_only_for_exact_workflows_permission_rejection() -> None:
    """The stale-base App-token failure is recovered once, without overmatching."""
    prompt = _prompt_text()

    assert _WORKFLOWS_PERMISSION_REJECTION in prompt
    assert prompt.count(_FETCH) == 2
    assert prompt.count(_REBASE) == 2
    assert prompt.count(_PUSH) == 2
    assert "retry EXACTLY ONCE" in prompt
    assert "If that retry gets the same rejection" in prompt
    assert "Do NOT loop and do NOT retry on any" in prompt
    assert "different error signature" in prompt


def test_pr_stage_retries_own_feature_branch_non_fast_forward_with_lease() -> None:
    """A rewritten own feature branch is reconciled with an explicit lease."""
    prompt = _prompt_text()
    normalized_prompt = " ".join(prompt.split())

    assert _NON_FAST_FORWARD_REJECTION in normalized_prompt
    assert _LEASE_PUSH in prompt
    assert "--force-with-lease" in prompt
    assert "bare `--force` push remains forbidden" in normalized_prompt
    assert "the lease is what makes this overwrite safe" in normalized_prompt.lower()
    assert "refs/heads/feat/<work-item-id>:<observed-remote-tip>" in normalized_prompt
    assert "never the current run branch" in normalized_prompt
    assert "cannot prove the remote branch tip is this run's own prior push" in normalized_prompt
    assert "report the output verbatim and end with the needs-human protocol" in normalized_prompt
    assert "lease mismatch" in normalized_prompt


def test_pr_stage_never_instructs_bare_force_push() -> None:
    """The publish recipe allows only the leased force form."""
    prompt = _prompt_text()

    assert "--force-with-lease" in prompt
    assert " --force " not in prompt
    assert " --force\n" not in prompt


def test_pr_stage_arms_auto_merge_with_the_declared_merge_mode() -> None:
    """The merge-method flag is a projection of `dispatcher.merge_mode`, not a literal."""
    prompt = _prompt_text()

    assert "gh pr merge --{{ inputs.merge_mode }} --auto --delete-branch" in prompt
    assert "--rebase" not in prompt
    assert "--squash" not in prompt


def test_pr_stage_does_not_authorize_workflow_file_edits() -> None:
    """The workflow path appears only as the remote rejection signature."""
    prompt = _prompt_text()

    assert "this stage must not edit files under `.github/workflows/`" in prompt
