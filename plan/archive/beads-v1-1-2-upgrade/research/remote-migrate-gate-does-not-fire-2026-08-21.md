# The remote-migrate gate does not fire on our tenants

**Date:** 2026-08-21
**Verifies:** the mitigation `rekey-silent-skip-hazard-2026-08-20.md` recorded
as "the design's evident intent … NOT verified semantics"
**Result:** the mitigation **does not hold**. The gate is correctly
inapplicable to our topology, and therefore protects us from nothing.
**Read-only.** Every statement below is a `SELECT`.

## The claim being verified

The 2026-08-20 hazard note, having established that our own client discards the
re-key's stderr warning on a zero exit, offered a mitigation and was careful to
label it unverified:

> MITIGATING, and stated as such: our tenants are server-mode and beads has a
> remote-migrate gate whose refusal arm the rehearsal already exercises
> (`migration-gate-receipt`'s `gate_decision` enum), so an incidental read
> should refuse rather than quietly migrate — that is the design's evident
> intent from the gate's existence and the receipt shape, **NOT verified
> semantics**. The residual exposure is the deliberate one-designated-migrator
> run.

That labelling was right, and the caution was warranted: the semantics do not
hold for us.

## What the gate actually keys on

`internal/storage/schema/remote_migrate_gate.go` @ v1.2.2. After establishing
that the database is not fresh (`current != 0`) and that migrations are pending,
the gate reaches its one decisive condition:

```go
hasRemote, err := anyDoltRemoteConfigured(ctx, db)
…
if !hasRemote && extraHasRemote != nil {
	hasRemote = extraHasRemote()
}
if !hasRemote {
	return nil // no remote — no cross-clone fork risk
}
```

and the probe itself is:

```go
func anyDoltRemoteConfigured(ctx context.Context, db DBConn) (bool, error) {
	var count int
	if err := db.QueryRowContext(ctx, "SELECT COUNT(*) FROM dolt_remotes").Scan(&count); err != nil {
		…
	}
	return count > 0, nil
}
```

The gate fires **only when a Dolt remote is configured**. It is not a
"migrations are pending" guard; it is a *cross-clone fork* guard.

## The measurement

The check is one `SELECT`, so this is not an approximation of the gate's
condition — **it is the gate's condition, run verbatim**:

```sql
SELECT COUNT(*) FROM dolt_remotes;
```

**Every one of the 14 live server tenants returns 0.**

| Tenant | remotes |
|---|---:|
| dolt-server | 0 |
| homelab | 0 |
| livespec | 0 |
| livespec-console-beads-fabro | 0 |
| livespec-dev-tooling | 0 |
| livespec-driver-claude | 0 |
| livespec-driver-codex | 0 |
| livespec-driver-pi | 0 |
| livespec-orchestrator-beads-fabro | 0 |
| livespec-orchestrator-git-jsonl | 0 |
| livespec-overseer | 0 |
| livespec-runtime | 0 |
| openbrain | 0 |
| resume | 0 |

Scope: every `.beads/config.yaml` under `/data/projects` declaring
`mode: server`; the three independent tenants probed through their own
credential wrappers. So `hasRemote` is false, and the gate returns `nil` —
**it does not fire, on any tenant.**

## Why this is correct behaviour, and why it is still bad for us

The gate is not broken and this is not an upstream defect. Its documented
purpose (gastownhall/beads#4259) is to stop two clones that sync through a
shared remote from each migrating in place and forking the schema. **We do not
have that topology.** We have ONE shared Dolt server that every client reaches
over TCP; there are no clones to fork, so there is nothing for the gate to
prevent, and it correctly stands down.

The problem is that the hazard note was relying on it as an *accidental safety
net* against a different failure — a stray newer binary migrating a tenant. On
our topology that net is absent, and our topology also makes that failure
**worse**, not better:

- In the upstream scenario the gate defends, an accidental migration forks one
  clone's schema, and the operator can adopt the remote.
- In ours, an accidental migration mutates **the one shared database**, so every
  client of that tenant is affected at once — which is exactly the fleet-wide
  stranding AGENTS.md records for the v1.2.1 landmine.

So the two properties compose badly: the topology that removes the gate's
trigger is the same topology that raises the blast radius.

## What this changes

**The hazard note's residual-exposure sentence is too narrow.** It reads: "The
residual exposure is the deliberate one-designated-migrator run." That is no
longer the whole of it. With the gate inert, the exposure is **any invocation of
any newer binary against any tenant** — the migration is auto-applied on open,
with no refusal and, per the earlier finding, with its warnings captured and
discarded by our own client on a zero exit.

**The "one designated migrator" rule is a convention, not an enforced control,
on our configuration.** The epic's own plan language ("one-designated-migrator
handling for the shared Dolt tenants") should be read as a human protocol that
nothing mechanically backstops.

**What DOES still bound the exposure** — stated so this is not read as alarm.
The exposure remains *human, not mechanical*, exactly as `bd-ib-3kolea.4`'s
analysis established: no dynamic version resolution exists in any of the twelve
repositories, nothing installs beads through mise, `/usr/local/bin/bd` is the
tracked lifecycle guard and `/usr/local/bin/bd-real` is pinned at v1.0.5
(re-measured 2026-08-19), and `go.mod` at v1.2.2 retracts the bad versions. Two
independent probes on 2026-08-20 confirmed no v1.2.x binary exists on this host
and all fourteen clones still record schema-line 1.0.5. Someone must
deliberately install a newer binary for any of this to matter.

What has changed is the **consequence** of that human error, not its
probability: there is no second line of defence behind it.

## Recommendations, recorded as findings with dispositions

1. **Do not cite the remote-migrate gate as a mitigation** in the rehearsal, the
   cutover runbook, or the final gate. It does not fire here. Superseding the
   hazard note's sentence in place is the honest fix, as that note itself did
   with its own earlier claim.
2. **If a mechanical backstop is wanted, `BD_ALLOW_REMOTE_MIGRATE` is the wrong
   lever** — it is an *unlock*, consulted only once the gate would already fire.
   A gate that never fires cannot be tightened by its own escape hatch.
   Registering a dummy remote purely to arm the gate would be defeating the
   design rather than using it, and is not recommended.
3. **The cheap control we do have is the pre-flight probe** from
   `rekey-drift-fleet-probe-2026-08-21.md` plus a version assertion: before the
   attended window, assert every tenant's schema version and every reachable
   binary's version, and treat any drift as a stop.
4. **Note the smart gate for completeness.** #4516's smart gate is on by default
   (`BD_SMART_GATE=0` opts out) and can decide `smartAutoMigrate` — i.e. *allow*
   a migration the blunt gate would have blocked. It is reached only after
   `hasRemote` is true, so it is moot for us today; it matters only if a remote
   is ever configured on these tenants.

Nothing was applied to `bd-ib-ao3j` or `bd-ib-3kolea.2`: both are
`admission:manual`, and this session held an admission only on
`bd-ib-3kolea.4`.

## Follow-on, same session: the other migrate path is UNGATED BY CONSTRUCTION

The limit originally recorded here — "establishing whether any other guard
exists in that path is separate work" — was then done, and it sharpens the
finding rather than softening it.

Call sites of `CheckRemoteMigrateGate*` are seven, of which the two
non-test store implementations are `internal/storage/dolt/store.go`
(server mode — **ours**) and `internal/storage/embeddeddolt/store.go`.
In the server-mode store there are exactly **two** routes into
`initSchemaOnDBWithRetryAndGate`, and they differ in their last argument:

```go
// 1. the store-OPEN path — gated
func (s *DoltStore) initSchema(ctx context.Context) error {
	…
	gate := func(ctx context.Context, db *sql.DB) error {
		return schema.CheckRemoteMigrateGateForRemoteWithRemoteCheck(ctx, db, s.remote, s.hasPersistedCLIRemote)
	}
	_, err = initSchemaOnDBWithRetryAndGate(ctx, migDB, gate)
```

```go
// 2. the explicit APPLY path — gate is nil
func (s *DoltStore) ApplySchemaMigrations(ctx context.Context) (int, error) {
	…
	return initSchemaOnDBWithRetry(ctx, migDB)
}

func initSchemaOnDBWithRetry(ctx context.Context, db *sql.DB) (int, error) {
	return initSchemaOnDBWithRetryAndGate(ctx, db, nil)   // <- no gate
}
```

`ApplySchemaMigrations` implements `storage.SchemaMigrator` — the explicit
"apply the migrations" entry point — and passes **`nil`** for the gate. That is
a deliberate design choice, not a bug: an operator who explicitly asks to
migrate should not be refused by a guard whose purpose is to catch *silent*
migration. But it means the gate is not a backstop even in principle.

So the two routes compose to: **on our tenants, neither path refuses.**

| Path | Gate passed? | Fires on our tenants? |
|---|---|---|
| store open (`initSchema`) | yes | **no** — `dolt_remotes` is 0, so the gate returns `nil` |
| explicit apply (`ApplySchemaMigrations`) | **no — `nil`** | n/a — there is no gate to fire |

This also means the gate's protection is narrower than it looks *for anyone*,
not only for us: even a tenant that DID have a remote configured would be
migrated without refusal through the explicit-apply path.

## The "somewhere else might catch it" hedge, now closed

The first version of this note hedged that it did "not claim that no check
anywhere else in the process would intervene". That hedge was honest but it
left a successor to redo the work, so it was chased down.

The explicit-apply route was traced to its **CLI entry point**:
`handleSchemaMigrate()` in `cmd/bd/migrate.go` calls
`migrator.ApplySchemaMigrations(rootCtx)` directly. Two discriminating symbol
searches over the whole repository:

| Symbol | Occurrences | Any under `cmd/bd/`? |
|---|---:|---|
| `CheckRemoteMigrateGate*` | 7 | **no** — 2 in `internal/storage/schema`, 2 in the two store implementations, 3 tests |
| `IsRemoteMigrateGateError` | 6 | **no** — storage layers and tests only |

**The gate is purely a store-layer guard; the CLI never calls it and never
handles its error.** So on the explicit `bd migrate` schema path there is no
gate at *any* layer — not in the store (it passes `nil`), and not above it.

That confirms the finding rather than qualifying it, and it is now traced end to
end rather than at the store method alone.

## Limits of this finding

This traces the two migrate routes in the **server-mode** store, which is the
one our tenants use, and the CLI path that reaches the ungated one. It does not
audit `embeddeddolt`. The two symbol searches above are the stated scope for the
"no CLI-layer gate" claim — a repository-wide search for the two symbols that
would have to appear for such a check to exist. Both legs are read from v1.2.2
source at commit `6c124203e771…`, the same commit the attestation binds.
