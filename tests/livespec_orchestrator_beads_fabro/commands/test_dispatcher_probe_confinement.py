"""Tests for the loop probe's `.livespec-probe/` confinement (v076).

Grouped as the contract splits the obligation: what counts as confined, the
PRE-MERGE refusal that must fire while nothing has merged, and the POST-MERGE
backstop that must name the commit and the revert obligation. The escape cases
lead with the fail-closed shapes -- absolute, traversing, and bare-directory --
because those are the ones a containment predicate written as a `startswith`
would wave through.
"""

from __future__ import annotations

import pytest
from livespec_orchestrator_beads_fabro.commands._dispatcher_probe_confinement import (
    PROBE_DIRECTORY,
    escaping_paths,
    merged_escape_failure,
    pre_merge_confinement_refusal,
)

_CONFINED = f"{PROBE_DIRECTORY}/latest.md"
_NESTED = f"{PROBE_DIRECTORY}/nested/artifact.txt"


def test_a_file_inside_the_probe_directory_is_confined() -> None:
    assert escaping_paths(paths=[_CONFINED, _NESTED]) == ()


def test_a_leading_dot_segment_does_not_defeat_confinement() -> None:
    assert escaping_paths(paths=[f"./{_CONFINED}"]) == ()


@pytest.mark.parametrize(
    "path",
    [
        "SPECIFICATION/contracts.md",
        f"/{_CONFINED}",
        f"{PROBE_DIRECTORY}/../escaped.md",
        PROBE_DIRECTORY,
        f"{PROBE_DIRECTORY}-sibling/artifact.md",
    ],
)
def test_every_unconfinable_path_reads_as_an_escape(path: str) -> None:
    assert escaping_paths(paths=[path]) == (path,)


def test_the_pre_merge_verification_passes_a_confined_change() -> None:
    assert pre_merge_confinement_refusal(paths=[_CONFINED]) is None


def test_the_pre_merge_verification_refuses_without_merging_and_names_the_path() -> None:
    refusal = pre_merge_confinement_refusal(paths=[_CONFINED, "justfile"])

    assert refusal is not None
    assert "failing without" in refusal
    assert "merging" in refusal
    assert "justfile" in refusal
    assert _CONFINED not in refusal


def test_the_post_merge_backstop_passes_a_confined_merged_diff() -> None:
    assert merged_escape_failure(paths=[_NESTED], merge_commit="abc1234") is None


def test_the_post_merge_backstop_names_the_commit_and_the_revert_obligation() -> None:
    failure = merged_escape_failure(paths=["justfile"], merge_commit="abc1234")

    assert failure is not None
    assert "abc1234" in failure
    assert "revert" in failure
    assert "justfile" in failure
