#!/usr/bin/env python3
"""Shebang wrapper for migrate-plan-records. No logic; see livespec_orchestrator_beads_fabro.commands.migrate_plan_records.

Private maintenance entry point for the one-shot plan-record migration.
"""

from _bootstrap import bootstrap

bootstrap()

from livespec_orchestrator_beads_fabro.commands.migrate_plan_records import main

raise SystemExit(main())
