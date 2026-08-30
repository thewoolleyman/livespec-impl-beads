"""What COUNTS as a fleet-toolchain literal, separated from where the gate looks for one.

`no_fleet_toolchain_literals` owns the scope, the allow-lists and the positive
controls -- the policy question, "where do we look and what do we forgive". This
module owns the orthogonal one: given a string, is it a fleet premise? The two
change for different reasons (a new scanned tree, versus a newly-recognized
literal shape), which is why they are separate modules rather than one file.

WHAT COUNTS AS A LITERAL, IN THE PACKAGE. The package scan is AST-based, so
comments are invisible, and docstrings and `__all__` symbol lists are skipped: a
docstring naming the fleet's runner is the design record for why a wrapper is NOT
imposed, and `__all__` carries Python symbol names, one of which is legitimately
spelled the same as a default branch. Of the remaining string constants, two
shapes count and nothing else:

- the literal IS the token -- the argv-element and ref-constant shape;
- the literal carries the token in SHELL COMMAND POSITION (at its start, or right
  after `;`, `|`, `&&`, `||`, `-c ` or a newline) -- the same premise spelled as
  a shell command string.

A mention inside a sentence is NEITHER. An operator-facing refusal that names
this fleet's tools describes what happened; it does not impose anything on a
governed repository, and banning it would only buy a worse refusal message.

WHAT COUNTS AS A LITERAL, IN THE PAYLOAD. The payload and prompt files are not
Python, so there is no docstring structure to scan around and the match is a
whole-word one over each raw line. The fleet's recipe runner is matched in
command position only, because its name is also an ordinary English word and
every prompt file is English prose; the other tokens name nothing but the tool.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass

__all__: list[str] = [
    "TOOLCHAIN_TOKENS",
    "Finding",
    "literal_token",
    "source_findings",
    "text_findings",
    "text_token",
]

# The banned tool names, spelled exactly as the ratified clause spells them.
TOOLCHAIN_TOKENS: tuple[str, ...] = (
    "lefthook",
    "livespec-step-timer",
    "livespec_dev_tooling",
    "mise",
    "just",
)

# The ONE token that is also an ordinary English word, so the payload scan
# matches it in command position rather than whole-word. The package scan does
# not need the distinction: prose there lives in docstrings and comments, which
# it never reads.
_PROSE_AMBIGUOUS: tuple[str, ...] = ("just",)

# A bare default-branch name USED AS A REF: the branch name on its own, or the
# ref path naming it. A sentence mentioning the branch is not a ref.
_DEFAULT_BRANCH_REF = re.compile(r"\A(?:refs/heads/|refs/remotes/origin/|origin/)?(master|main)\Z")
_COMMAND_POSITION = {
    token: re.compile(r"(?:\A|[;|\n]|&&|\|\||-c )\s*" + re.escape(token) + r"(?![\w-])")
    for token in TOOLCHAIN_TOKENS
}
_WHOLE_WORD = {
    token: re.compile(r"(?<![\w-])" + re.escape(token) + r"(?![\w-])") for token in TOOLCHAIN_TOKENS
}


@dataclass(frozen=True, kw_only=True)
class Finding:
    """One fleet-toolchain literal outside the module allowed to carry it."""

    relpath: str
    lineno: int
    token: str
    literal: str


def literal_token(*, literal: str) -> str | None:
    """The fleet-toolchain token this Python string constant IS, or `None`."""
    stripped = literal.strip()
    for token in TOOLCHAIN_TOKENS:
        if stripped == token or _COMMAND_POSITION[token].search(literal) is not None:
            return token
    branch = _DEFAULT_BRANCH_REF.match(stripped)
    return branch.group(1) if branch is not None else None


def text_token(*, line: str) -> str | None:
    """The fleet-toolchain token this payload line carries, or `None`."""
    for token in TOOLCHAIN_TOKENS:
        matcher = _COMMAND_POSITION[token] if token in _PROSE_AMBIGUOUS else _WHOLE_WORD[token]
        if matcher.search(line) is not None:
            return token
    branch = _DEFAULT_BRANCH_REF.match(line.strip())
    return branch.group(1) if branch is not None else None


def _all_assignment_value(*, node: ast.AST) -> ast.expr | None:
    match node:
        case ast.Assign(targets=[ast.Name(id="__all__")], value=value):
            return value
        case ast.AnnAssign(target=ast.Name(id="__all__"), value=value):
            return value
        case _:
            return None


def _skipped_node_ids(*, tree: ast.AST) -> set[int]:
    """Constants the package scan does not read: docstrings and `__all__` entries."""
    ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                ids.update(id(inner) for inner in ast.walk(body[0]))
        value = _all_assignment_value(node=node)
        if value is not None:
            ids.update(id(inner) for inner in ast.walk(value))
    return ids


def source_findings(*, source: str, relpath: str) -> list[Finding]:
    """Every fleet-toolchain literal in one module's source."""
    tree = ast.parse(source, filename=relpath)
    skipped = _skipped_node_ids(tree=tree)
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        if id(node) in skipped:
            continue
        token = literal_token(literal=node.value)
        if token is not None:
            findings.append(
                Finding(
                    relpath=relpath, lineno=node.lineno, token=token, literal=node.value.strip()
                )
            )
    return sorted(findings, key=lambda finding: (finding.lineno, finding.token, finding.literal))


def text_findings(*, text: str, relpath: str) -> list[Finding]:
    """Every fleet-toolchain literal in one non-Python payload file."""
    findings: list[Finding] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        token = text_token(line=line)
        if token is not None:
            findings.append(
                Finding(relpath=relpath, lineno=lineno, token=token, literal=line.strip())
            )
    return findings
