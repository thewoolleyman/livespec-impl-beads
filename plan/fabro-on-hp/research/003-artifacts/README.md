# Parameterized fabro-server provisioning — candidate artifacts

These are **draft artifacts for `bd-ib-l3nptz.14`**, held in the plan thread's
research store because `.14`'s destination repository has not been chosen yet.
They are not installed from here and nothing consumes them yet.

Once the maintainer picks a destination (a sibling per-host repo such as
`hp-xubuntu-info`, or a deliberately re-chartered multi-host `vps-info`), the
work is `git mv` of this directory into that repo's `services/fabro-server/`
plus a README pass — not re-derivation.

## What problem these solve

`vps-info/services/fabro-server/` hardcodes the vps host throughout. hp was
brought up by cloning it, editing the host-specific literals by hand, running
the installer, and discarding the edits. So hp's provisioning exists only as
live host state, and every fix landed in the versioned vps unit silently
misses hp. Two instances of that class are already filed: `bd-ib-l3nptz.15`
(the crash-loop mitigation) and `bd-ib-l3nptz.16` (scheduler concurrency).

One template plus a per-host values file replaces the hand-edit step.

## Files

| File | Role |
|---|---|
| `fabro-server.service.in` | The unit, with `@NAME@` placeholders for the axes hosts actually diverge on. |
| `hosts/<host>.env` | That host's values. Six lines. |
| `hosts/<host>.settings.expected` | That host's expected **resolved** fabro settings. |
| `render-unit.sh` | Renders the template for one host to stdout. No root needed. |
| `install.sh` | Renders, installs, enables, and verifies. Host-guarded. |
| `check-settings.sh` | Compares a host's live resolved settings against its expectations. |
| `install.test.sh` | Exercises the installer's pure guards without root or a live host. |
| `check-settings.test.sh` | Fixture tests for the settings.toml reader. |
| `fabro-server-verify-web` | Unmodified copy of vps-info's verifier — shared by all hosts. |
| `otel.conf` | The OTLP drop-in. Host-invariant. |

## The per-host axes, measured rather than assumed

The vps-era runbook predicted **two** per-host edits (`WorkingDirectory`, and
`install.sh`'s cwd assertion). Diffing the two live factories on 2026-08-19
found **five**, which is why a two-edit clone left hp incomplete:

1. **Service account** — `ubuntu` on vps, `cwoolley` on hp. The tailnet ACL
   rejects `ubuntu` on hp, so this is not cosmetic.
2. **HOME** — follows the account, and every `~/.fabro/...` path with it.
3. **Checkout root** — `/data/projects/...` on vps, `/home/cwoolley/repos/...`
   on hp. Appears twice: `WorkingDirectory` and the installer's cwd assertion.
4. **Canonical host** — the verifier's `Host:` header value.
5. **Verifier crash-loop budget** — `FABRO_WEB_VERIFY_ATTEMPTS`.

## Why the verifier is no longer forked

hp's installed verifier differs from vps's in exactly one line: the
`FABRO_CANONICAL_HOST` default. The script already honours that variable, so
the unit supplies it and a single shared copy serves both hosts.

Proven, with a negative control, on 2026-08-19: the **unmodified vps-info**
verifier (sha256 `06763080…`) run against hp exits **0** with
`FABRO_CANONICAL_HOST=hp-xubuntu.perch-rudd.ts.net:32276`, and exits **1**
without it. The variable is load-bearing; the fork is not.

## Why settings are checked by resolved value, not by file diff

A missing table in `settings.toml` does not read as missing — it reads as the
built-in default, and the server reports nothing. hp ran
`max_concurrent_runs=5` against vps's `10` for exactly that reason, invisibly,
because hp's `settings.toml` has no `[server.scheduler]` table at all
(`bd-ib-l3nptz.16`). `check-settings.sh` therefore reads
`GET /api/v1/settings` — resolved behavior — rather than diffing the file.

`cli.target.url` is checked separately, straight from `settings.toml`, because
the API exposes only `server.*`. It is not dropped: `auth.json` is keyed by
that URL, so pointing it at the tailnet name silently invalidates the stored
credential. It stays loopback on both hosts deliberately.

## Verification performed (2026-08-19)

Rendering reproduces each host's real unit exactly, with every difference
intentional and named:

| Rendered for | Compared against | Difference |
|---|---|---|
| hp | hp's **live** unit | `+FABRO_WEB_VERIFY_ATTEMPTS=300` (the `.15` fix), `+FABRO_CANONICAL_HOST` (de-forks the verifier). Nothing else. |
| vps | vps-info's **committed** unit | `+FABRO_CANONICAL_HOST` only. |
| vps | vps's **live** unit | The two above — live vps gets `ATTEMPTS` from a drop-in instead. |

Also run: `shellcheck` clean on all three scripts; `render-unit.sh` guard rails
exercised (missing file → 2, missing variable → 3, unsubstituted placeholder →
4); `check-settings.sh` passes on both hosts against their own expectations and
correctly flags the `.16` drift when hp is checked against vps's expectations.

## The installer's host guard is tested

`install.sh` is sourceable — `main` runs only when the file is executed
directly — so `install.test.sh` can source it and call individual guards
without root and without touching a host. `hostname` is stubbed through a PATH
shim, so the shipped code path is what runs.

`require_host_matches` is the guard worth covering first: installing hp's unit
on vps fails *silently* — the wrong unit installs and starts fine, pointed at
the wrong checkout and the wrong canonical host. Six checks pass: both hosts
accepted against their own canonical name, both cross-host installs refused,
and each `hosts/<name>.env` rendering a `WorkingDirectory` matching the
`FABRO_HOST_CHECKOUT` that same file declares.

Two things about the harness are worth knowing, because the obvious version
lies:

- Sourcing `install.sh` with **no** argument trips its `${1:?usage}` and exits
  before any function is defined. A naive harness then sees a non-zero status
  and scores every "refuses" case as a pass while never reaching the guard.
  The first draft did exactly that — 2 real failures beside 2 false passes. It
  is therefore sourced with a real `hosts/*.env`, and `FABRO_CANONICAL_HOST` is
  overridden *after* sourcing. **The positive cases are what prove the harness
  reaches the guard**; without them the negatives are worthless.
- The negatives were mutation-checked: replacing `require_host_matches` with
  `return 0` in a throwaway copy fails exactly the two cross-host cases and
  nothing else.

## The settings.toml reader is tested

`check-settings.sh` compares resolved values, with one exception: `cli.target`
is not exposed by the API, so it is parsed out of `settings.toml` by hand. That
parser is the only place in the artifact set that *reads* rather than
*compares*, and the file it reads carries a `url` key in several tables —
`[cli.target]`, `[server.api]`, `[server.web]`. Matching the wrong one would
compare the right key against the wrong value and print `ok`.

It is therefore extracted as `read_cli_target_url`, and `check-settings.sh`
returns early when sourced so `check-settings.test.sh` can call it against
fixtures. Eight checks cover the real layout, siblings before and after,
missing table, missing key, whitespace, a dotted subtable, and agreement with
whichever host's live `settings.toml` is readable from where the test runs.

**Mutation-checking corrected an assumption here.** Deleting the awk's
table-disarm rule fails exactly one case — "cli.target without a url". The case
that *reads* as though it guards the disarm, "sibling url after cli.target",
still passes against the mutant, because the parser `exit`s on the first match
and never reaches the sibling. That test documents behaviour; it does not guard
the rule. The labels in the test say which is which, because a test that cannot
fail is not a guard.

## Known gaps before this can be called done

- **Not installed anywhere.** `install.sh` has never been run end-to-end from
  this directory, so its supersede-the-old-drop-in step, and everything from
  `require_inputs` onward, remain unexercised. Landing this must include one
  real run on hp. (`require_host_matches` is now covered — see below.)
- **`hosts/hp-xubuntu.settings.expected` records `max_concurrent_runs=5`**,
  the observed value, not a chosen one. `.16` decides the number.
- **The tailscale serve mapping is not captured here.** Both hosts carry a
  tailnet-only `:32276` proxy; `tailscale-admin` documents only the vps one.
- **vps has no `otel.conf`.** Installing this on vps would newly add OTLP
  export there. Intended eventually, but it is a behavior change, not a
  transcription — do it deliberately.
