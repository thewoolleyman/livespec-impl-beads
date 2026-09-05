"""Per-wrapper coverage test for bin/context.py."""

from collections.abc import Callable


def test_context_wrapper_threads_exit_code(
    wrapper_runner: Callable[[str, str, int], None],
) -> None:
    wrapper_runner(
        "context.py",
        "livespec_orchestrator_beads_fabro.commands.context",
        0,
    )
