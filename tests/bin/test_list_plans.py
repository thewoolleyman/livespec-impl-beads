"""Per-wrapper coverage test for bin/list_plans.py."""

from collections.abc import Callable


def test_list_plans_wrapper_threads_exit_code(
    wrapper_runner: Callable[[str, str, int], None],
) -> None:
    wrapper_runner(
        "list_plans.py",
        "livespec_orchestrator_beads_fabro.commands.list_plans",
        0,
    )
