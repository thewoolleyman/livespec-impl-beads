"""Seed sanity test — keeps `just check` (pytest) green on the seeded tree.

Exists so the skeleton's check suite is non-empty and green BEFORE the Fabro
agent implements `greet`. The agent adds `tests/test_greet.py` asserting the
greeting; both run under the same `just check`.
"""

# @generated — seed payload, not this repo's first-party code. See the matching
# sentinel in `src/greeting/__init__.py` for why this is the sanctioned way to
# keep the seed out of the git-derived first-party universe.
__all__: list[str] = ["test_skeleton_is_present"]


def test_skeleton_is_present() -> None:
    assert 1 + 1 == 2
