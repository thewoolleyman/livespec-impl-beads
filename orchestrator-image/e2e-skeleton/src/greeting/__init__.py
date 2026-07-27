"""The greeting package — the hello-world deliverable lives here.

The Fabro agent adds `greet.py` exposing `greet(name: str) -> str` per the
repo SPECIFICATION; this package makes `from greeting.greet import greet`
importable once it does.
"""

# @generated — seed payload, not this repo's first-party code. This file is
# copied verbatim into a throwaway W7 golden-master clone and is governed by
# THAT project's rules, not by this repo's. The ruff `extend-exclude` in
# pyproject.toml already says so for the linter; this sentinel is what says the
# same thing to the git-derived first-party universe
# (`livespec_dev_tooling.config.is_generated`), which is the ONLY sanctioned way
# to say it — that module's design forbids per-repo path globs precisely because
# they recreate the fail-open allowlist the sentinel replaces.
__all__: list[str] = []
