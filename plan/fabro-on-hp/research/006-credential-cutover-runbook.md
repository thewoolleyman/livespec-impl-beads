# fabro-on-hp — the three remaining children, as one runbook

**Written 2026-08-21.** Every remaining child of `bd-ib-l3nptz` — `.10`, `.11`,
`.12` — is blocked on a credential action only the maintainer can perform. The
instructions are spread across six comments in three items, which is why they
have been re-read rather than executed several times. This note collects them
into one ordered pass.

Every pin below was **re-measured on 2026-08-21**, not copied from the items.
Where an item's own text is wrong, this note says so and gives the corrected form.

## Do this first, once

- **Record the App ids before deleting anything.** `4331220` (homelab-pr-bot),
  `4483441` (dolt-server-pr-bot), `4204166` (openbrain-pr-bot), `4243167`
  (resume-pr-bot). The `*_OLD` 1Password values restore a *credential*; nothing
  restores a *deleted App*. Delete only after the replacement is proven.
- **The replacement identity is the same everywhere:** App `3668528`
  (`thewoolleyman-factory-bot`), sole installation `131208965`,
  `repository_selection=all`, 281 repos. Its permission set was measured by
  App-JWT `GET /app`: `contents:write`, `metadata:read`, `pull_requests:write`,
  `statuses:write`, `workflows:write`. **`administration` is absent entirely** —
  that is what eliminated the blast-radius concern, and it is also why homelab
  loses unattended deploy-key registration (accepted 2026-08-21 as the cost).

## `.11` — dolt-server (start here; it is the closest to done)

**Its repo side is already merged**: `c1e1bc9` (PR #70) adopted the shared App
and replaced the repository-cardinality security proof with a wrapper-path
proof. Nothing further is needed in that repo.

**Its step (1) as written is wrong** and this is the correction that matters:
the item says "maintainer switches dolt-server's 1Password Environment". That
wrapper does **not** read a 1Password Environment. It reads root-owned,
`systemd-creds`-encrypted files under `/var/lib/dolt-server/credentials/`. No
desktop-app edit can change them, so a maintainer told "do the 1Password
switches" would reasonably believe this one was done when it was not.

The real procedure, as root on the host:

```bash
sudo ./scripts/provision-dolt-server-credentials.sh --name dolt-server-github-app-id              # stdin: 3668528
sudo ./scripts/provision-dolt-server-credentials.sh --name dolt-server-github-private-key         # stdin: the shared PEM
sudo ./scripts/provision-dolt-server-credentials.sh --name dolt-server-github-app-installation-id # stdin: 131208965
```

`just provision-credential name=<n>` wraps it. **No atomic cutover is required**
— the identity verifier is not on the dispatch path (no `ExecStartPre`, not in
`just check`), so the only casualty of a mid-flight state is the manual
`just verify-dispatch-identity`.

Then: verify one dispatch; stop the dedicated server; delete App `4483441`.

## `.10` — homelab

1. Switch `with-homelab-env.sh`'s `GITHUB_APP_ID` / `GITHUB_PRIVATE_KEY` to the
   shared App (1Password desktop app). **This item's stored credential is dead
   (401)** — step 1 is a *repair*, not cleanup.
2. Land the pre-computed `.livespec.jsonc` edits **in the same commit as the
   switch** (they rewrite prose that stays true until then): delete the
   `dispatcher.fabro_home` key and its 3-line comment; update the identifier
   comment from `4331220` / `147392283` to `3668528` / `131208965`. Leave
   `ci/test-hetzner-prod-deploy-key.py:208` alone — its `4331220` is a synthetic
   fixture asserting the key's *absence*, resolved and out of scope.
3. Verify one real homelab dispatch lands on hp.
4. Stop the dedicated server, then delete App `4331220`.

**Blocked on another thread, not on this one:** homelab has ratified spec text
naming the old identity, and its `proposed_changes/` still holds **8** in-flight
proposals from other threads (re-counted 2026-08-21). A revise pass decides all
eight, so it belongs to whoever drives homelab's spec cadence. Contrast `.12`'s
openbrain half, whose tree was empty — which is the whole reason that one moved
and this one did not.

## `.12` — openbrain + resume

**Two of its steps are already done.** Its openbrain spec prerequisite is
ratified — `SPECIFICATION/history/v105`, commit `74fc938` — and its step (5)
cleanup target `~/.fabro-openbrain` no longer exists (searched `/home` and
`/root` at depth 3; the same search finds `.fabro-restore`,
`.fabro-dolt-server` and `.fabro-homelab`, so it could have returned a hit).

What remains is maintainer-only:

1. Switch openbrain's 1Password Environment to the shared App.
2. Switch resume's wrapper **and**, in the same window, resume's `APP_ID` /
   `APP_PRIVATE_KEY` **GitHub Actions secrets**. Both surfaces must move
   together; switching only the wrapper leaves `auto-enable-merge.yml`
   authenticating as an App that is about to be deleted.
3. Delete Apps `4204166` and `4243167`.

**No dispatch verification is required** — that was ruled on 2026-08-21, on the
grounds that "one dispatch per repo" is impossible in both repos for reasons
unrelated to the credential switch.

**resume's repo side is already transition-tolerant**: `e842fb6` allowlists both
`thewoolleyman-factory-bot[bot]` and `resume-pr-bot[bot]` in
`auto-enable-merge.yml`, so the switch has no window in which auto-merge stops.
Remove the stale `resume-pr-bot[bot]` entry only *after* a bump pull request is
observed landing as the new App.

## Stopping the two dedicated servers

Both `.10` step (4) and `.11` step (5) stop a server by **direct pid-verified
kill**, not through `install.sh`. There is **no guard on that path** — see `005`
§"The dedicated servers have no guard at all". Measured 2026-08-21:

| server | pid | `FABRO_HOME` | binary | live runs | total runs |
|---|---|---|---|---|---|
| `:32278` (homelab) | `662038` | `~/.fabro-homelab` | **deleted** since 2026-07-18 | 0 | **0 ever** |
| `:32286` (dolt-server) | `2521838` | `~/.fabro-dolt-server` | live | 0 | 17 historical |

Re-confirm `/proc/<pid>/exe` and `FABRO_HOME` before killing, and kill **by
PID** — never `pkill -f 'fabro server'`, which self-matches the killing shell.
`:32278` runs a deleted binary, so it cannot be restarted in place once stopped.
Keep `:32286` running until dolt-server's shared-server dispatch is verified
green; that is its rollback path.
