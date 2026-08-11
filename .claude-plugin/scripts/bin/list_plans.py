#!/usr/bin/env python3
"""Shebang wrapper for list-plans. No logic; see livespec_orchestrator_beads_fabro.commands.list_plans."""

from _bootstrap import bootstrap

bootstrap()

from livespec_orchestrator_beads_fabro.commands.list_plans import main

raise SystemExit(main())
