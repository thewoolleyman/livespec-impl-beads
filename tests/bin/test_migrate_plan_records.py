"""Per-wrapper coverage test for bin/migrate_plan_records.py."""

from collections.abc import Callable


def test_migrate_plan_records_wrapper_threads_exit_code(
    wrapper_runner: Callable[[str, str, int], None],
) -> None:
    wrapper_runner(
        "migrate_plan_records.py",
        "livespec_orchestrator_beads_fabro.commands.migrate_plan_records",
        0,
    )
