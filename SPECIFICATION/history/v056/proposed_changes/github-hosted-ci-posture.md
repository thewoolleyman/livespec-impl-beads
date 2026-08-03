---
topic: github-hosted-ci-posture
author: codex-gpt-5
created_at: 2026-08-03T01:14:40Z
---

## Proposal: Hosted CI without weakening the factory boundary

### Target specification files

- constraints.md
- contracts.md
- scenarios.md

### Summary

Remove stale claims that fleet CI executes on the shared host, record the current GitHub-hosted-only posture, and preserve the workflow-edit refusal as a self-amending-gate boundary rather than a host-code-execution boundary.

### Motivation

The maintainer disabled both local CI supervisors and the self-hosted-only live golden-master workflow after the host became overloaded. The spec still says the check matrix runs on self-hosted runners and uses that fact as the rationale for withholding workflow-write capability. The capability boundary remains correct, but its stated reason is now false: an agent that can rewrite workflows can disable its own CI examiner even when GitHub executes the jobs off-host.

### Proposed Changes

In constraints.md section Factory sandbox credential constraints, the scope MUST refer to the factory execution substrate rather than a self-hosted CI substrate. The GitHub workflows read-write grant MUST remain rejected because it is self-amending authority over the implement to janitor to CI to merge chain; the updated rationale MUST state that ordinary fleet CI currently runs on GitHub-hosted runners, so the blast radius is the integrity of the pipeline and admitted repository output rather than arbitrary execution on the maintainer host. The live golden-master workflow MUST remain disabled while the local privileged gate runner is disabled, and its absence MUST NOT be replaced with a fail-open success. In contracts.md work-item mapping, factory_safety mutates-host-machinery MUST continue to route .github/workflows edits to the attended host session, but the text MUST explain that this is because workflow files mutate the factory's external merge-gate machinery, not because those jobs execute on the factory host. In scenarios.md Scenario 48, the workflow-edit refusal MUST be explicitly substrate-independent and remain in force when CI executes on GitHub-hosted runners.
