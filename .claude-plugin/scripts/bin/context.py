#!/usr/bin/env python3
"""Shebang wrapper for context. No logic; see livespec_orchestrator_beads_fabro.commands.context."""

from _bootstrap import bootstrap

bootstrap()

from livespec_orchestrator_beads_fabro.commands.context import main

raise SystemExit(main())
