"""PreToolUse beads-access guard — deny un-wrapped tenant tooling.

Shipped in the impl-plugin template's `.claude/hooks/` and registered as a
`PreToolUse` hook on the `Bash` tool in `.claude/settings.json`. It blocks a
bare `bd` / `dolt` / direct-tenant `mysql` invocation unless the command runs
under a recognized per-project credential-injection env wrapper
(`with-<id>-env.sh`) — turning the silent "ran outside the wrapper -> tenant
auth failure" footgun into an actionable deny that names the wrapper.

The matching `should_block` predicate is pure so it can be unit-tested by
import (no subprocess). Fail-open: any malformed input or unexpected shape is a
silent pass-through — the hook only ever blocks on a POSITIVE match.
"""

from __future__ import annotations

import json
import re
import shlex
import sys

__all__: list[str] = ["main", "should_block"]

_WRAPPER_RE = re.compile(r"with-[a-z0-9-]+-env\.sh")
_COMMAND_SEPARATORS = {";", "&", "&&", "|", "||", "(", ")"}
_COMMAND_SUBSTITUTION_PREFIX = "$"
_ENV_COMMAND = "env"
_COMMAND_PREFIXES = {"command", "sudo"}
_HEREDOC_OPERATORS = {"<<", "<<-"}
_TENANT_COMMANDS = {"bd", "dolt"}
_TENANT_HINTS = ("3307", "127.0.0.1")
_ASSIGNMENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=.*")

_REASON = (
    "Blocked: direct beads/Dolt tenant access must run under your project's "
    "configured credential-injection env wrapper (e.g. "
    "`with-<project>-env.sh -- <command>`). An 'Access denied' / 'no beads "
    "database found' failure means you are OUTSIDE the wrapper (the bare "
    "BEADS_DOLT_PASSWORD is absent) — never hand-hunt the secret or reach "
    "around the seam with raw mysql/dolt/sudo."
)


def should_block(*, command: str) -> bool:
    """Return True iff `command` is an un-wrapped tenant-tooling invocation.

    A command already running under any recognized per-project env wrapper
    (`with-<id>-env.sh`) is never blocked. Otherwise a bare `bd` or `dolt`
    word, or a `mysql` invocation aimed at the tenant endpoint (`127.0.0.1` /
    port `3307`), is blocked.
    """
    if _WRAPPER_RE.search(command):
        return False
    command_tokens = _command_position_tokens(command=command)
    if any(token in _TENANT_COMMANDS for token in command_tokens):
        return True
    return "mysql" in command_tokens and any(hint in command for hint in _TENANT_HINTS)


def _command_position_tokens(*, command: str) -> list[str]:
    """Return shell words that occupy command position in `command`."""
    try:
        tokens = _shell_tokens(command=_without_heredoc_bodies(command=command))
    except ValueError:
        return []

    command_position_tokens: list[str] = []
    expect_command = True
    token_index = 0
    while token_index < len(tokens):
        token = tokens[token_index]
        if token == _COMMAND_SUBSTITUTION_PREFIX:
            token_index += 1
            continue
        if token in _COMMAND_SEPARATORS:
            expect_command = True
            token_index += 1
            continue
        if not expect_command:
            token_index += 1
            continue
        token_index = _effective_command_index(tokens=tokens, start=token_index)
        if token_index >= len(tokens):
            break
        token = tokens[token_index]
        if token in _COMMAND_SEPARATORS:
            continue
        command_position_tokens.append(token)
        expect_command = False
        token_index += 1
    return command_position_tokens


def _effective_command_index(*, tokens: list[str], start: int) -> int:
    """Skip shell prefixes that still leave a later word in command position."""
    token_index = start
    while token_index < len(tokens):
        token = tokens[token_index]
        if token in _COMMAND_SEPARATORS:
            return token_index
        if _ASSIGNMENT_RE.fullmatch(token):
            token_index += 1
            continue
        if token in _COMMAND_PREFIXES:
            token_index += 1
            continue
        if token == _ENV_COMMAND:
            token_index += 1
            while token_index < len(tokens) and _ASSIGNMENT_RE.fullmatch(tokens[token_index]):
                token_index += 1
            continue
        return token_index
    return token_index


def _shell_tokens(*, command: str) -> list[str]:
    """Split `command` into shell-like words and control operators."""
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    return list(lexer)


def _without_heredoc_bodies(*, command: str) -> str:
    """Return `command` with here-document body lines removed."""
    stripped_lines: list[str] = []
    pending_delimiters: list[str] = []
    for line in command.splitlines():
        if pending_delimiters:
            if line == pending_delimiters[0]:
                pending_delimiters.pop(0)
            continue
        stripped_lines.append(line)
        pending_delimiters.extend(_heredoc_delimiters(line=line))
    return "\n".join(stripped_lines)


def _heredoc_delimiters(*, line: str) -> list[str]:
    """Return here-document delimiters introduced on a command line."""
    try:
        tokens = _shell_tokens(command=line)
    except ValueError:
        return []

    delimiters: list[str] = []
    iterator = iter(tokens)
    for token in iterator:
        if token in _HEREDOC_OPERATORS:
            delimiter = next(iterator, "")
            delimiters.append(delimiter)
            continue
    return delimiters


def main() -> int:
    """Read the PreToolUse hook input on stdin; deny on a positive match.

    Always exits 0 (fail-open): a malformed payload, a non-Bash tool, or any
    unexpected shape is a silent pass-through.
    """
    try:
        payload = json.loads(sys.stdin.read())
    except (ValueError, TypeError):
        return 0
    command = _command_of(payload=payload)
    if not command or not should_block(command=command):
        return 0
    json.dump(
        {
            "decision": "block",
            "reason": _REASON,
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": _REASON,
            },
        },
        sys.stdout,
    )
    return 0


def _command_of(*, payload: object) -> str:
    """Extract `tool_input.command` from the hook payload, or empty string."""
    if not isinstance(payload, dict):
        return ""
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


if __name__ == "__main__":
    raise SystemExit(main())
