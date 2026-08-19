# Guard and provisioning findings (2026-08-19 working session)

Facts established by direct measurement while working F1/F3 to closure. Each
entry states how it was verified, because several corrected an earlier belief
that had already been written down as if settled.

## The per-dispatch `run_turn` guard was false-positiving on every green dispatch

Observed: the `run-turn-telemetry-absent` critical reflection finding fired on
every dispatch this session made, reaching a cumulative count of 9, while live
Honeycomb queries showed the corresponding `run_turn` spans landing in the
`fabro` dataset inside the exact dispatch windows.

**First hypothesis, WRONG and now superseded.** The guard keys on
`work.item.id` / `livespec.dispatch.id`; no sampled `run_turn` span carries
either, and neither is even a column in the `fabro` dataset (`run_query`
rejects `work.item.id` as unknown). That looked sufficient, and it was filed
that way. Reading `_dispatcher_run_turn_sink.py` refuted it: the sink already
records a global fallback key `fabro.run_turn` precisely because Fabro spans
carry no correlation ids, and `has_export()` passes on that key alone.

**Verified cause.** The OTLP receiver binds the host-global sandbox endpoint
`172.17.0.1:4318` (`DEFAULT_SANDBOX_OTEL_ENDPOINT`), and
`ensure_receiver_started()` is deliberately fail-open, but the export marker
path was repo-scoped (`<repo>/tmp/<journal-stem>-run-turn-exports.json`). When
another repo's dispatcher already holds the port, this repo's dispatch silently
gets no receiver, the spans still reach Honeycomb through that other process,
and this repo's guard reads a marker file that was never written. Confirmed by
`ss`: port 4318 was held by a `dispatcher.py loop --repo
/data/projects/livespec-overseer` process, and no `*-run-turn-exports.json`
existed under any repo on the host.

Fixed in two steps: PR #1551 bounded the marker lookup to the dispatch window
(so stale markers cannot satisfy the guard), and PR #1553 moved the marker to a
host-global, dataset-keyed XDG state path so whichever process owns the port
writes the signal every repo's guard reads.

**Still unverified live, and why.** Only the process that binds 4318 writes the
marker. That process must itself be running a build that carries PR #1553
(v0.58.12+). Do not kill another track's dispatcher loop to force this; wait for
its natural restart, then confirm a green dispatch emits no finding while
Honeycomb shows its spans landed.

## The dead-man trigger's provisioning script could not have worked

`bd-ib-ehrdid` shipped a provisioning script and auto-closed on merge, but the
trigger itself was never created — `get_triggers` on the livespec environment
still returned exactly 3 triggers, none on `fabro`. Provisioning needs a
livespec-scoped Honeycomb **Configuration** key that does not exist on this host
(tracked by `bd-ib-jb7rzr.3`).

A pre-flight review of the script found it would have failed on its first run
even once that key existed, for two independent reasons:

- Its default recipient selector `operator-alert` named a recipient that does
  not exist. `GET /1/recipients` for team `thewoolleyweb` returns exactly two
  recipients, both `type=email`. The premise carried in `bd-ib-ehrdid` and the
  README — that there is an existing "operator-alert path used by the adopter
  dead-man triggers" — is unfounded for this team; those triggers route to bare
  email recipients.
- Its matcher could not match an email recipient at all. The candidate set was
  `{id, target, details.name, details.webhook_name, details.slack_channel}`,
  while an email recipient's only populated field is `details.email_address`.
  Overriding the selector with the operator's own address would also have
  failed; only a raw recipient id worked, which was undocumented.

Both fixed in PR #1555, along with the README wording.

## Honeycomb key and recipient scoping (reusable)

- **Recipients are team-scoped, not per-environment.** Proven, not assumed: the
  list returned through an `agent-activity`-scoped key contains exactly the
  recipient ids the `livespec` environment's own triggers use. Only the trigger
  write needs an environment-scoped key.
- **Configuration keys ARE environment-scoped.** The fleet's one Configuration
  key (`HONEYCOMB_TRIGGER_RECIPIENT_AUDIT_CONFIG_API_KEY`, 1Password `homelab`
  Environment) probes via `/1/auth` as environment `agent-activity`, so it
  cannot touch `livespec` regardless of its scopes.
- The `livespec` wrapper carries only ingest keys plus a **management**-type MCP
  key. The v1 API rejects management keys at `/1/auth` before scopes are
  consulted, so no scope grant bridges them — consistent with the finding
  recorded in `vps-info/services/honeycomb-trigger-recipients-check`.

## A merge that closes an item is not evidence the item's goal was reached

Two separate instances in one session. `bd-ib-ehrdid` closed green with a
merged PR while the trigger it existed to create did not exist, and its PR also
rewrote the README to assert the trigger *was* live — the same stale-doc failure
mode PR #1522 had corrected in that same section weeks earlier (re-corrected in
PR #1548). `bd-ib-jb7rzr.2` closed green having fixed only part of its defect.
Both were caught by checking the live system rather than the ledger status.
