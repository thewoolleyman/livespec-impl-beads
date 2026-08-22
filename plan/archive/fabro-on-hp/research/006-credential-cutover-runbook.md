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

> **CORRECTED 2026-08-22, after executing `.11` step (5).** This section
> previously said BOTH servers are stopped by direct pid kill because "there is
> **no guard on that path**". That was **wrong for `:32286`**, and following it
> as written would have left the server running: `:32286` was managed by a
> systemd unit with `Restart=on-failure`, so a raw kill is simply **restarted**.
> The claim happens to hold for `:32278`. **It is a per-server property, not a
> property of "the dedicated servers" — check each one before acting.**

**Check for a unit first, every time.** The guard question is answered by
`systemctl`, not by assumption:

```bash
systemctl list-units --all | grep -i fabro
ls /etc/systemd/system/ | grep -i fabro
systemctl show <unit> -p MainPID -p Restart -p UnitFileState -p ActiveState
```

Measured 2026-08-22, after `.11` completed:

| server | pid | `FABRO_HOME` | systemd unit | correct stop | state |
|---|---|---|---|---|---|
| `:32278` (homelab) | `662038` | `~/.fabro-homelab` | **none** — confirmed absent | pid kill *is* correct here | still running; `.10` step (4) |
| `:32286` (dolt-server) | *was* `2521838` | `~/.fabro-dolt-server` | **`fabro-dolt-server.service`**, `Restart=on-failure` | `sudo systemctl stop fabro-dolt-server.service` | **STOPPED 2026-08-22**; `.11` complete |

For a unit-managed server, confirm `MainPID` matches the pid you verified, then
`systemctl stop`. Check `UnitFileState` too: `fabro-dolt-server.service` was
already `disabled`, so no separate `disable` was needed to keep it from
returning at boot. A unit that is `enabled` must also be disabled.

For an unmanaged server, re-confirm `/proc/<pid>/exe` and `FABRO_HOME`, then
kill **by PID** — never `pkill -f 'fabro server'`, which self-matches the
killing shell. `:32278` runs a deleted binary, so it cannot be restarted in
place once stopped.

**`.10` step (4)'s written instruction to remove `~/.fabro-homelab` needs the
same scrutiny `.11` step (5)'s did.** On `.11` that instruction was **wrong**:
the directory is the adopter's *client* home, which the v011 wrapper-path proof
asserts, and it had to survive the server's decommissioning. Verified after the
fact — the identity verifier still returns 23/0 with `:32286` stopped and the
home kept. homelab's arrangement may differ (its server has **zero runs ever**
and a deleted binary), but establish that its home is not load-bearing before
removing it, rather than inheriting `.11`'s answer or this runbook's original
wording.

## The homelab reset constraint — maintainer-directed, persisted here

**Recorded 2026-08-22 at the maintainer's direction**, communicated through the
`homelab-rewrite` session and persisted in this runbook so the constraint
survives the session that received it.

> **`.10` step (3) — "prove a real dispatch on hp" — MUST NOT run through the
> homelab repository.** Prove it on orchestrator, openbrain, resume, or
> dolt-server instead. Nothing may touch homelab.

**Why, measured rather than asserted.** homelab is mid-way through the
Talos/Omni repo reset (`docs/talos-omni-reset.md`). Its Phase 0 quiesce landed
on homelab `main` at 2026-08-22T02:44Z as PR #942, merge `0297e8f`, setting in
homelab's `.livespec.jsonc`:

| key | before | after |
|---|---|---|
| `dispatcher.wip_cap` | `10` | **`0`** |
| `spec_governance.spec_pr_merge` | `auto-on-green` | `manual` |

`wip_cap: 0` means homelab admits nothing. A homelab dispatch will not admit —
**and it presents as a factory or App failure when the real cause is the
quiesce.** That is the expensive part: you would be debugging App `3668528`'s
installation against a repo whose admission was capped minutes earlier. This
runbook's own `.10` line numbers (198, 173–174, 105) already reflect the
post-quiesce tree.

**Why another repo is sufficient, not a workaround.** What step (3) proves is
that identity `3668528` can open a pull request from the hp factory host. That
is a property of the App and the factory, not of homelab — any repo registered
with hp demonstrates it. homelab's own registration is re-established later by
the reset's Phase 8 against the **destination organisation**, so proving it
against homelab's current registration would prove something the reset is about
to invalidate.

### How this resolved in practice

`.10` step (3) was **waived**, not redirected — homelab's quiesce made a
dispatch impossible, and Gate 3 had already waived the same requirement for
`.12`. The credential is independently proven: homelab's own wrapper mints a
valid App JWT as `3668528` (it returned **401** before the switch, so step (1)
was a repair), and `.11` demonstrated the shared App publishing end to end from
hp — dolt-server PR #74, authored by `app/thewoolleyman-factory-bot`, merged.

**Note what that evidence does and does not cover.** The resume
`auto-enable-merge` re-run at 03:43:43Z proves resume's Actions secrets; it
exercises nothing in homelab, and must not be cited as homelab's dispatch
proof. Different population, same trap this thread hit repeatedly.

### Division of ownership, agreed by both threads

- **`.10` step (2) was dropped, not deferred.** The reset rewrites
  `.livespec.jsonc` wholesale in its purge commit and has recorded that the
  rewrite must not reintroduce `fabro_home` or the retired identifiers. The key
  is inert meanwhile — no plugin code reads `dispatcher.fabro_home` (zero
  non-test hits across `.claude-plugin/scripts/` and `commands/`). Editing it
  would have collided with another thread's in-flight rewrite of the same file.
- **`~/.fabro-homelab` and App `4331220` were `.10`'s**, per the reset's
  preserve-list reconciliation item 3, and its Phase 0 carves the legacy
  `127.0.0.1:32278` server out of the quiesce by name. **Both are now
  discharged**: `:32278` stopped 2026-08-22 (pid `662038`, no systemd unit, zero
  runs ever), `~/.fabro-homelab` removed, App `4331220` deleted.
- The shared per-host factory servers on hp and vps (`:32276`) are carved out by
  the reset and stay up.

### Load-bearing input supplied to the reset

The reset's Phase 6 step 2 needs to know which App identity the shared factories
publish with, so it can be installed on the destination org **before** Phase 8
restores dispatch. The answer, measured repeatedly on 2026-08-22 by App-JWT
`GET /app`:

- **App `3668528`** (`thewoolleyman-factory-bot`), **installation `131208965`**,
  `repository_selection=all`, permissions exactly `contents:write`,
  `metadata:read`, `pull_requests:write`, `statuses:write`, `workflows:write` —
  `administration` **absent**.

If that ever changes, the reset must be told: it is the input its reseeded
world's first dispatch depends on.
