"""Paired coverage for groom draft data shapes."""

from __future__ import annotations

import pytest
from livespec_orchestrator_beads_fabro.commands import _dispatcher_groom_door, groom
from livespec_orchestrator_beads_fabro.commands.groom import CandidateSlice, CrossRepoSlice


def test_candidate_slice_defaults_to_factory_slice() -> None:
    candidate = CandidateSlice(
        title="slice",
        description="Do one thing.",
        acceptance="Factory can verify it.",
        autonomy_tier="T1",
        repo_target="local-repo",
    )

    assert candidate.depends_on == ()
    assert candidate.is_spec_change is False


def test_candidate_slice_rejects_priority_argument() -> None:
    with pytest.raises(TypeError):
        CandidateSlice(
            title="slice",
            description="Do one thing.",
            acceptance="Factory can verify it.",
            autonomy_tier="T1",
            repo_target="local-repo",
            priority=1,
        )


def test_cross_repo_slice_carries_minted_id() -> None:
    candidate = CandidateSlice(
        title="external",
        description="Do one external thing.",
        acceptance="Factory can verify it.",
        autonomy_tier="T1",
        repo_target="other-repo",
    )

    routed = CrossRepoSlice(candidate=candidate, minted_id="bd-x-123")

    assert routed.candidate is candidate
    assert routed.minted_id == "bd-x-123"


def test_the_front_end_surface_carries_the_groom_door() -> None:
    """The contract says the FRONT-END's operator performs the groom dispatch.

    The mechanism lives beside the Dispatcher's claim and pin seams, so what is
    asserted here is that the front-end module is where a caller finds it —
    identity, not merely a same-named attribute, because a second definition
    would satisfy the weaker check while diverging silently.
    """
    assert groom.groom_dispatch is _dispatcher_groom_door.groom_dispatch
    assert groom.GroomDispatch is _dispatcher_groom_door.GroomDispatch
    assert groom.GroomDoorRefusal is _dispatcher_groom_door.GroomDoorRefusal
    assert "groom_dispatch" in groom.__all__
