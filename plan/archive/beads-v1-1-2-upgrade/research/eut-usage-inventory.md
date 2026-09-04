# Enemy Unit Test usage inventory — the Beads surface livespec depends on

**Deliverable 1 of ledger item `bd-ib-3kolea.3`.** Read-only research; nothing
here mutates a tenant, a host binary, or an image.

**Measured:** 2026-08-19, against `master` at the time of writing.

**Scope searched:** this repository only — every tracked `*.py`, `*.sh`, and
`*.md`, via `git grep` over the whole worktree. Sibling family repositories
(`livespec`, `livespec-runtime`, `livespec-driver-*`, `livespec-console-*`,
`livespec-overseer`, `dolt-server`) were **NOT** searched; see
[Known scope gaps](#known-scope-gaps). Read every absence claim below as scoped
to this repository.

## Headline finding: the thin proxy already exists

`bd-ib-3kolea.3` is written as though the proxy must be built. It largely does
not: `livespec_orchestrator_beads_fabro/_beads_client.py` already defines a
`BeadsClient` Protocol with exactly **11 methods**, and `ShellBeadsClient` is
the single place this package turns those into `bd` subprocess calls. That is
the thin interface the Enemy Unit Test technique asks for.

Two properties make it directly usable as the EUT seam:

1. **It already accepts an arbitrary executable.** `_build_argv` composes
   `[self._config.bd_path, *verb_args]` and adds **no connection flags**, so
   pointing the whole surface at a different `bd` binary is a `StoreConfig`
   field, not a code change. The EUT requirement "must accommodate being
   pointed at an ARBITRARY `bd` executable" is already satisfied.
2. **It is genuinely thin.** Each method is one `bd` invocation plus a
   coercion. The one exception is `exists()`, noted below.

So deliverable 2 changes character: it is **verify-and-close-the-gaps**, not
build-from-scratch. The gaps are real and are listed in
[Prose surface](#prose-surface-commands-our-documentation-instructs) and
[Unrouted call sites](#unrouted-call-sites).

### One trap that must not be stepped in

`make_beads_client()` selects a **fake** backend when `config.fake` is set:

```python
def make_beads_client(*, config: StoreConfig) -> BeadsClient:
    if config.fake:
        return fake_singleton()
    return ShellBeadsClient(config=config)
```

Enemy Unit Tests **MUST** construct `ShellBeadsClient` directly, or assert
`config.fake` is false. Routing EUTs through `make_beads_client()` with a fake
config would test the fake's fidelity — which is the assumption under test —
and would pass against any binary, including one that does not exist. This is
the single most likely way for this harness to become a rubber stamp.

## Programmatic surface (authoritative)

Every `bd` invocation this package makes, with exact argv. This is the set the
proxy must expose and the EUTs must cover.

| Method | Exact verb argv | Output handling |
|---|---|---|
| `list_issues` | `list --status all --limit 0 --json` | `coerce_record_list` |
| `show_issue` | `show <id> --json` | `coerce_issue_record` |
| `list_comments` | `comments <id> --json` | `coerce_comment_list` |
| `children` | `children <id> --json` | `coerce_record_list` |
| `exists` | *(none — see below)* | derived from `list_issues` |
| `create_issue` | `create --id --type --title --description --priority [--assignee] [--spec-id] [--parent] [--label ...] --metadata` | **stdout NOT parsed** |
| `update_issue` | `update <id> [--status] [--assignee] [--parent] [--add-label ...] [--remove-label ...] [--metadata]` | **stdout NOT parsed** |
| `close_issue` | `close <id> [--reason <text>]` | **stdout NOT parsed** |
| `add_dependency` | `dep add <from> <to> --type <edge>` | **stdout NOT parsed** |
| `add_comment` | `comment <id> <body>` | **stdout NOT parsed** |
| `register_custom_statuses` | `config set status.custom <csv>` | **stdout NOT parsed** |

Notes that change what the EUTs must assert:

- **`exists()` issues no `bd` call of its own.** It scans `list_issues()` so a
  missing id is a clean boolean instead of a nonzero exit. An EUT asserting
  `exists()` is therefore really re-asserting `list --status all`.
- **`create` does not parse stdout.** The qualification note records that
  `bd create ... --json` emits a single JSON object, but this package does not
  consume it — `create_issue` returns `draft.issue_id`, the id it supplied. So
  a change to `create`'s output shape would **not** break this package
  directly. It would break the **guard**, which does parse it (see below).
- **`--metadata` is emitted as compact sorted JSON** (`separators=(",",":")`,
  `sort_keys=True`). Round-trip assertions should compare parsed structures,
  not strings.
- **Clearing an assignee is `--assignee ""`**, an empty-string argument, not a
  flag. Worth an explicit EUT: argument-parsing changes tend to break exactly
  this shape.
- `update_issue` **returns early** when the built argv is a no-op, so "no
  fields changed" never reaches `bd`.

The registered custom-status CSV is:

```
backlog,pending-approval,ready:active,active:wip,acceptance:wip
```

## The coercion contracts, and where they FAIL OPEN

These are the highest-value EUT targets, because three of them **degrade
silently** rather than raising. A shape change here does not crash — it
produces a plausible, empty, wrong answer.

| Function | Accepts | Silent-failure path |
|---|---|---|
| `parse_json_output` | any JSON | **empty stdout returns `[]`**, not an error |
| `coerce_issue_record` | non-empty array, `[0]` a dict | raises on all violations — *safe* |
| `coerce_comment_list` | array | **non-dict members are dropped** by a filter |
| `coerce_record_list` | bare array **or** `{"issues": [...]}` | **non-dict members are dropped** |

Three consequences the EUTs must pin down:

1. **A `bd` version that printed nothing would read as "no results."**
   `parse_json_output` maps empty stdout to `[]`. Every list-shaped read would
   then return empty and no exception would be raised. An EUT must assert a
   **non-empty** result against a **known-populated** fixture, never merely
   that the call did not raise.
2. **A comment-shape change would read as "no comments."** `coerce_comment_list`
   filters out non-dict members. *This exact failure mode was hit by a human
   reader during this plan's own work on 2026-08-19* — `bd show --json` does
   not carry comment bodies, the empty result was reported as "the epic has
   zero comments," and the claim was wrong. The machinery has the same blind
   spot the reader did.
3. **`coerce_record_list` accepts TWO envelopes.** A version that switched
   `list` from a bare array to `{"issues": [...]}` would pass unnoticed. That is
   deliberate tolerance, not a bug — but the EUT should **record which envelope
   each version actually returns**, so a silent switch is visible in the
   old-vs-new comparison rather than absorbed.

`coerce_issue_record` is the well-behaved one: it raises if `show` is not an
array, if the array is empty, or if `[0]` is not an object. The
one-element-array envelope is genuinely load-bearing and genuinely enforced.

## Prose surface (commands our documentation instructs)

Verbs appearing in tracked `*.md` that **`BeadsClient` never calls**. An agent
following these instructions exercises the API as surely as a call site does,
so they are in scope for the harness:

| Verb | Status in this package |
|---|---|
| `bd ready` | **not in the client** — instructed in prose |
| `bd init` | **not in the client**; `CLAUDE.md` forbids running it in a checkout |
| `bd version` | not in the client |
| `bd migrate` | not in the client; central to the upgrade itself |
| `bd doctor` | not in the client |
| `bd export` | not in the client |
| `bd bootstrap` | not in the client; upstream's prescribed upgrade path |
| `bd config get` | not in the client (only `config set` is) |
| `bd defer`, `bd reopen`, `bd create-prefix` | not in the client |

**A concrete divergence worth an assertion.** `CLAUDE.md` instructs operators
to survey the ledger with:

```
bd list --limit 0 --json
```

while the client emits `list --status all --limit 0 --json`. The prose form
**omits `--status all`**. If the two forms ever diverge in default filtering,
operators and code silently see different ledgers. The EUT should cover **both
literal forms** and assert they agree.

`CLAUDE.md` also documents that `bd list --status open` matches nothing here,
because `_NATIVE_STATUS_REMAP` in `commands/_dispatcher_ledger_close.py` maps
`open`→`backlog` and `in_progress`→`active`. A native-name filter returns an
empty set rather than erroring — another fail-open path, and a required EUT
assertion.

## Unrouted call sites

Files invoking `bd` outside `_beads_client_shell.py`. Deliverable 3 requires
each to be routed or explicitly justified; this is that list.

- **`bd-guard/bd-guard.sh`** — the lifecycle guard at `/usr/local/bin/bd`. It
  performs the **two-step create normalization** and therefore **does** parse
  `create` output, even though the Python client does not. It is the consumer
  that a `create`-output change would break, and it is *upstream* of every
  other call site. Highest-priority EUT coverage.
- `bd-guard/install.sh`, `bd-guard/rollback.sh` — install/rollback paths.
  `CLAUDE.md` warns `rollback.sh` must **not** be used for the version rollback
  because it removes the guard.
- `orchestrator-image/build-and-verify.sh` — image-side verification of the
  guarded layout.
- `plan/beads-v1-1-2-upgrade/rehearsal-package/wrappers/*.sh` — the rehearsal
  package's own real-call wrappers (`with-client.sh`, `capture-inventory.sh`,
  `survey-fixture-shape.sh`). These already implement an arbitrary-binary
  invocation pattern and are worth reusing rather than reinventing.
- `commands/_config.py`, `types.py` — resolve `bd_path` / `LIVESPEC_BD_PATH`;
  configuration, not invocation.
- `tests/**` — numerous dev-tooling and integration tests reference `bd_path`.
  These are *our* tests, not the enemy's surface, but they will need the same
  arbitrary-binary parameterization.

## Known scope gaps

Stated so a later reader does not mistake this for an exhaustive family sweep:

1. **Only this repository was searched.** Sibling repos consume Beads through
   their own adapters and may use verbs absent here.
2. **Prose was surveyed by verb frequency**, which over-counts English
   collocations (`create lands`, `update sets`) and could under-count a verb
   mentioned only once in an unusual phrasing.
3. **The guard's internal `bd` usage was identified but not disassembled.**
   Its exact parse of `create` output still needs reading before the EUTs can
   assert it.
4. Runtime-only surfaces — anything a dispatched factory agent invokes inside a
   sandbox image — were not enumerated.

## Recommended EUT coverage order

1. The four coercion contracts, with **non-empty** fixtures, against both
   binaries. Highest defect-detection value; three fail open.
2. The `show` one-element-array envelope, asserted explicitly.
3. The guard's two-step create normalization, including its parse of `create`
   output.
4. The custom-status CSV round-trip plus the `open`→`backlog` /
   `in_progress`→`active` remap.
5. `--assignee ""` clearing, and `--metadata` compact-sorted-JSON round-trip.
6. Both `list` literal forms (with and without `--status all`), asserted to
   agree.
7. The prose-only verbs, at least to the depth our documentation promises.
