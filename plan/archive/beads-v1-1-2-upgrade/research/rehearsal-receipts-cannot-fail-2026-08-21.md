# Five rehearsal receipts assert things they never measured

**Date:** 2026-08-21
**Subject:** `plan/beads-v1-1-2-upgrade/rehearsal-package/wrappers/`
**Finding:** **five** producer scripts publish **sixteen** assertion fields as a
hardcoded `True`, where the script is *structurally unable* to compute the
assertion — it holds one side of a comparison, or none.
**Corrected 2026-08-21, later the same day** — the first version of this note
said four scripts and eight fields. See "Correction" at the end: the undercount
came from a scope claim in this note that was itself overstated.
**The schemas are not at fault.** The package demonstrates the correct pattern
in one place; five other producers violate it.
**Bears on:** `bd-ib-ao3j` (which would RUN this package) and the epic's
acceptance criteria, which name these receipts as the evidence.

## Why this was checked at all

`rekey-silent-skip-hazard-2026-08-20.md` concluded "THE REHEARSAL WOULD NOT
CATCH IT EITHER", reasoning that no comparison in the package puts v49 data
beside v53 data. That claim had **already been revised once** in its own note —
the first version said the rewrite would be "visible, loudly" and was corrected
— and this thread's whole hazard framing rests on it. A claim revised once, and
load-bearing, is worth an independent look.

The boundary claim holds. What the earlier reading did not reach is that the
problem is one level deeper: several of the package's checks **cannot fail at
all**, whatever data they are pointed at.

## The package's own correct pattern

`compare-restored-baseline.sh` is the exemplar, and it is genuinely sound:

```sh
source_sha=$(sha256sum "$1/combined.sha256" | awk '{print $1}')
restored_sha=$(sha256sum "$2/combined.sha256" | awk '{print $1}')
…
    "all_artifacts_match": sys.argv[2] == sys.argv[3],
```

It is handed **both** sides, it **computes** the verdict, and its schema pins
the expected outcome:

```json
"all_artifacts_match": { "const": true }
```

So a mismatch writes `false` and **schema validation fails**. Measurement in the
producer, expected outcome in the schema, rejection on divergence. That is a
working gate, and it is the design the schemas were written for.

**This matters for reading the rest of this note: `"const": true` in a schema is
correct.** It declares the pass condition. The defect below is entirely in
producers that skip the measurement and write the pass condition directly.

## The five that cannot fail

### 1. `compare-golden-schema.sh` — one hash, not two

```python
migrated = Path(sys.argv[1])
payload = {
    "migrated_schema_sha256": hashlib.sha256(migrated.read_bytes()).hexdigest(),
    "golden_client_dir": sys.argv[2],          # <- recorded as a STRING
    "schema_hash_matches": True,               # <- hardcoded
}
```

`GOLDEN_CLIENT_DIR` is never opened. The script computes the migrated hash and
**no golden hash**, so it has nothing to compare against; `schema_hash_matches`
is a constant. Named a comparison, it is a transcription.

### 2. `prove-production-unchanged.sh` — no "after" parameter exists

```
usage: $0 PORT_BEFORE REGISTRY_SHA256_BEFORE BACKUP_CONFIG_SHA256_BEFORE RECEIPT_PATH
```

Every input is a **BEFORE** value. There is no *after* argument at all, so the
script is structurally incapable of detecting a change — and it publishes three:

```python
"production_port_3307_unchanged": True,
"production_registry_digest_unchanged": True,
"production_backup_config_digest_unchanged": True,
```

A script named *prove production unchanged* proves nothing about production.
This is the most serious single assertion in the set: it is the receipt that would be cited to
show a rehearsal did not touch the live server.

### 3. `preflight-backup-namespace.sh` — reads the manifest, discards it

```python
_ = json.loads(Path(sys.argv[1]).read_text())   # <- explicitly thrown away
run_id = sys.argv[2]
payload = {
    "bucket_prefix_contains_run_id": True,
    "manifest_namespace_contains_run_id": True,
    "production_values_refused": True,
}
```

The `_ =` is explicit: the topology manifest is parsed and dropped. `run_id` is
right there in scope, so `run_id in bucket_prefix` would be a one-line real
check. **`production_values_refused` is a safety assertion** — it is what stops
the rehearsal writing into production namespaces — and it is a literal.

### 4. `stop-manifest-pid.sh` — reads a path, verifies no scope

```python
"pid_file": manifest.get("isolated_server", {}).get("pid_file"),
"pid_scope_verified": True,
```

It extracts the pid-file path and asserts the scope was verified. Nothing checks
that the pid belongs to the isolated server rather than, say, the production
one — which is precisely what "scope verified" would need to mean.

### 5. `cleanup-run-scoped-resources.sh` — eight literals beside one real check

This is the largest offender and the most instructive, because it contains
**both patterns in the same payload**:

```python
clients = [row["client_dir"] for row in manifest.get("clients", [])]
payload = {
    "pid_absent": True,
    "port_13307_absent": True,
    "receipt_root_retained": True,
    "production_port_3307_unchanged": True,
    "production_registry_digest_unchanged": True,
    "production_backup_config_digest_unchanged": True,
    "sql_users_absent": True,
    "client_directories_absent": True,
    "run_root_absent": not run_root.exists(),      # <- a REAL check
    "removed_manifest_scoped_resources": clients,
}
```

`run_root_absent` is genuinely measured. Eight fields beside it are literals —
including `sql_users_absent`, which is the cleanup assertion that no leftover
SQL user remains on the **shared** server, and `client_directories_absent`,
which is hardcoded while `clients` (the very list of directories to check) sits
in scope one line above.

The juxtaposition matters for how this should be read. **An author who writes
`not run_root.exists()` knows how to write a real check**, so "unfinished draft"
is a far more plausible reading than "deliberate fabrication" — and the correct
idiom is demonstrated *inside the same dict* as the fabricated ones. That makes
the fix easier to specify and harder to argue with.

## What is NOT wrong, stated so this is fair

- **`assert-client-anchor.sh` is a good script.** It hash-checks its inputs and
  `halt()`s on mismatch, runs the identity probe, and compares database, user,
  port, TCP peer and server fingerprint against expected values, halting on each.
  Its `"read_only_transaction": True` is a *description of what the script
  itself did* — it issued one `SELECT` — not a claim about measured external
  state. That is legitimate.
- **The schemas are right**, as established above.
- **`compare-restored-baseline.sh` is right**, and is the pattern to copy.
- **`preflight-topology.sh` is right.** It performs genuine duplicate detection
  (`if len(realpaths) != len(set(realpaths))`, and the same for users) and fails
  on collision rather than asserting uniqueness.
- **`capture-inventory.sh`, `record-designated-migrator.sh`,
  `write-client-pointers.sh`, `anchor-probe.py` and `identity-probe.py`** write
  receipts but publish **no** hardcoded assertion fields — they record measured
  or supplied values.

## Why the receipts still validate

Because the schema pins the expected value and the producer writes exactly that
value, **validation passes by construction**. A reviewer asking the natural
question — "did every receipt validate against its schema?" — gets a clean
green, and that green carries no information about the sixteen assertions above.

This is the failure shape this repo already names: *a check that cannot fail is
not a check*, and worse, it **manufactures evidence** rather than merely
omitting it. The earlier hazard note found a rehearsal whose comparisons do not
cross the version boundary. This is sharper: five of its scripts would report
success against **any** input, including a rehearsal that had gone wrong.

## Disposition

Recorded as a finding, **not applied**. `bd-ib-ao3j` is `admission:auto` but sits
at `backlog`, and the `backlog -> ready` move is the `move:` human valve, so
hardening the package it will run is not this session's to start. The fix is
mechanical and small in each case — pass the second side in, compute the
comparison, let the schema reject a `false` — and `compare-restored-baseline.sh`
is a working template for all five.

This supersedes nothing in `rekey-silent-skip-hazard-2026-08-20.md`: its
boundary claim stands. It adds a layer underneath it that changes the priority —
widening the rehearsal's *scope* (the 2026-08-20 recommendation) is worth much
less while five of its existing scripts cannot fail.

## Correction — and how the undercount was found

The first version of this note claimed, under Scope, that it had "read every
producer under `rehearsal-package/wrappers/` that writes a receipt". **That was
overstated.** The actual method was a `grep` across all producers for
literal-boolean receipt fields, followed by reading the files that matched.
That is a sound method, but it is not "read every producer", and the difference
is not cosmetic: it is precisely the kind of scope claim this repo requires to
be stated accurately, because an absence claim is only as good as the search
behind it.

Re-checking that claim is what found the fifth script. **13 producers write
receipts; the first version classified 6.** Going back through the other seven
turned up `cleanup-run-scoped-resources.sh` with eight more hardcoded
assertions, doubling the count from 8 fields to 16.

So the correction is not incidental — the overstated scope sentence and the
undercount were the same defect. The note asserted broader coverage than it had,
and the gap it papered over contained the largest offender in the package.

## Scope, stated accurately

- **All 13 receipt-writing producers** under `rehearsal-package/wrappers/` were
  swept for literal-boolean receipt fields; every match was then read in full,
  as were `preflight-topology.sh` and `compare-restored-baseline.sh` as
  controls for the sound pattern. Every classification above quotes the code.
- All schemas under `rehearsal-package/schemas/` were checked for `const`
  pinning.
- **Not run.** This is a source reading of a package whose execution needs a
  privileged host, so "cannot fail" is a claim about the code, argued from the
  arguments each script receives — in every case above, the script is not given
  the second side of the comparison it publishes.
