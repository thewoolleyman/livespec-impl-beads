#!/usr/bin/env bash
#
# preflight-probe.sh — the attended-window pre-flight check for the
# beads v1.0.5 -> v1.2.2 upgrade.
#
# WHY THIS EXISTS
# ---------------
# Two findings from 2026-08-21 make a pre-flight check the cheapest control
# available for this upgrade:
#
#   1. rekey-drift-fleet-probe-2026-08-21.md — the v1.2.2 upgrade runs
#      rekeyAuxRowIDs, which rewrites the primary keys of four tables. On
#      dolthub/dolt#11131 storage drift it SKIPS a table, logs three lines, and
#      lets MigrateUp exit 0. Our client discards that stderr on a zero exit,
#      so a partial re-key would pass silently. No tenant carried the drift on
#      2026-08-21, but the tenants are LIVE, so that reading is point-in-time
#      and must be retaken immediately before the migration.
#
#   2. remote-migrate-gate-does-not-fire-2026-08-21.md — the remote-migrate
#      gate keys on `SELECT COUNT(*) FROM dolt_remotes > 0`, which is 0 on every
#      tenant, and the explicit ApplySchemaMigrations route passes no gate at
#      all. So nothing mechanically prevents an accidental migration; the
#      "one designated migrator" rule is a human convention only.
#
# WHAT IT CHECKS, per tenant
#   A. schema version   — MAX(version) in schema_migrations. Anything other than
#                         the expected baseline means a newer binary has already
#                         touched this tenant; at or above 65 is the v1.2.1
#                         landmine (AGENTS.md "Beads runtime prerequisites").
#   B. re-key drift     — forces a decode of exactly the columns auxRekeyTables
#                         reads. Any "invalid hash length" is the silent-skip
#                         trigger. LENGTH(CONCAT_WS(...)) is what forces every
#                         selected cell to materialise rather than be optimised
#                         away, so an undecodable cell raises instead of hiding.
#   C. row counts       — what the re-key would rewrite, one UPDATE each.
#   D. remotes          — recorded for context: 0 means the remote-migrate gate
#                         cannot fire, which is finding 2 above.
#
# READ-ONLY. Every statement is a SELECT. This installs nothing and runs no
# v1.2.x binary. One query per tenant, so it is fast enough to run inside the
# window rather than being skipped for time.
#
# USAGE
#   ./preflight-probe.sh              # check every server-mode tenant
#   ./preflight-probe.sh <repo-path>  # check one
#
# EXIT CODES
#   0  every probed tenant is clean and at the expected baseline
#   1  at least one tenant FAILED a check — treat as a STOP, do not migrate
#   2  at least one tenant was UNREADABLE (no verdict) — also a stop, because a
#      missing answer is not a pass. A directory that declares server mode but
#      holds no database is SKIPPED rather than counted unreadable; that arm is
#      matched narrowly so an auth or connection failure still stops the run.
#
# MAINTENANCE
#   The column lists below are copied verbatim from auxRekeyTables in
#   internal/storage/schema/aux_row_id_backfill.go. If upstream changes that
#   table, THESE MUST CHANGE WITH IT or the probe silently checks the wrong
#   cells. Verified against v1.2.2 @ 6c124203e771.

set -uo pipefail

EXPECTED_SCHEMA_VERSION="${EXPECTED_SCHEMA_VERSION:-49}"
LANDMINE_VERSION=65
WRAPPER_DIR=/data/projects/1password-env-wrapper

EVENTS_COLS="issue_id, event_type, actor, old_value, new_value, comment, CAST(created_at AS CHAR)"
COMMENTS_COLS="issue_id, author, text, CAST(created_at AS CHAR)"
ISNAP_COLS="issue_id, CAST(snapshot_time AS CHAR), compaction_level, original_size, compressed_size, original_content, archived_events"
CSNAP_COLS="issue_id, compaction_level, snapshot_json, CAST(created_at AS CHAR)"

failed=0
unreadable=0
total_rows=0

wrapper_for() {
    case "$1" in
        homelab)   echo "$WRAPPER_DIR/with-homelab-env.sh" ;;
        openbrain) echo "$WRAPPER_DIR/with-openbrain-env.sh" ;;
        resume)    echo "$WRAPPER_DIR/with-resume-env.sh" ;;
        *)         echo "$WRAPPER_DIR/with-livespec-env.sh" ;;
    esac
}

# One statement per tenant. Each decode_* subquery forces every cell the re-key
# reads to materialise, so a dolt#11131 cell raises rather than being skipped.
build_sql() {
    cat <<SQL
SELECT
  (SELECT MAX(version) FROM schema_migrations)                                            AS schema_version,
  (SELECT COUNT(*) FROM dolt_remotes)                                                     AS remotes,
  (SELECT COUNT(*) FROM events)                                                           AS n_events,
  (SELECT COUNT(*) FROM comments)                                                         AS n_comments,
  (SELECT COUNT(*) FROM issue_snapshots)                                                  AS n_isnap,
  (SELECT COUNT(*) FROM compaction_snapshots)                                             AS n_csnap,
  (SELECT COALESCE(SUM(LENGTH(CONCAT_WS('|', $EVENTS_COLS))),0)   FROM events)            AS d_events,
  (SELECT COALESCE(SUM(LENGTH(CONCAT_WS('|', $COMMENTS_COLS))),0) FROM comments)          AS d_comments,
  (SELECT COALESCE(SUM(LENGTH(CONCAT_WS('|', $ISNAP_COLS))),0)    FROM issue_snapshots)   AS d_isnap,
  (SELECT COALESCE(SUM(LENGTH(CONCAT_WS('|', $CSNAP_COLS))),0)    FROM compaction_snapshots) AS d_csnap
SQL
}

check_tenant() {   # $1=repo path
    local repo="$1" name wrap out row
    name=$(basename "$repo")
    wrap=$(wrapper_for "$name")
    cd "$repo" || { echo "== $name"; echo "   ????  cannot cd"; unreadable=1; return; }
    echo "== $name"

    out=$("$wrap" -- bd sql "$(build_sql)" 2>&1)

    if grep -qi "invalid hash length" <<<"$out"; then
        echo "   FAIL  dolt#11131 drift present — the re-key WILL silently skip a table"
        failed=1
        return
    fi
    row=$(grep -E '^[0-9]+ *\|' <<<"$out" | head -1)
    if [[ -z "$row" ]]; then
        # A directory whose .beads/config.yaml declares server mode but which
        # resolves to NO DATABASE is not a tenant at all — skip it. This is
        # deliberately narrow: it matches only bd's own "no beads database
        # found", never an auth or connection failure. Widening it would turn
        # the fail-closed arm below into a fail-open one, and a probe that
        # always returns INCOMPLETE trains its operator to ignore the verdict,
        # which is the same outcome as having no probe.
        if grep -qi "no beads database found" <<<"$out"; then
            echo "   skip  no beads database here — not a tenant"
            return
        fi
        echo "   ????  unreadable — $(tr '\n' ' ' <<<"$out" | cut -c1-110)"
        unreadable=1
        return
    fi

    local f
    IFS='|' read -r -a f <<< "$(tr -d ' ' <<<"$row")"
    local ver="${f[0]}" remotes="${f[1]}"
    local ne="${f[2]}" nc="${f[3]}" ni="${f[4]}" ns="${f[5]}"

    if [[ "$ver" -ge "$LANDMINE_VERSION" ]] 2>/dev/null; then
        echo "   FAIL  schema v$ver — AT OR PAST THE v1.2.1 LANDMINE (v65). See AGENTS.md; do NOT migrate."
        failed=1
    elif [[ "$ver" != "$EXPECTED_SCHEMA_VERSION" ]]; then
        echo "   FAIL  schema v$ver, expected v$EXPECTED_SCHEMA_VERSION — a newer binary has already touched this tenant"
        failed=1
    else
        echo "   ok    schema v$ver (expected)"
    fi

    echo "   ok    all four re-key tables decode cleanly"
    echo "   info  rows to rewrite: events=$ne comments=$nc issue_snapshots=$ni compaction_snapshots=$ns"
    if [[ "$remotes" == "0" ]]; then
        echo "   note  dolt_remotes=0 — the remote-migrate gate CANNOT fire on this tenant"
    else
        echo "   note  dolt_remotes=$remotes — the remote-migrate gate may fire on the store-open path"
    fi
    for n in "$ne" "$nc" "$ni" "$ns"; do
        [[ "$n" =~ ^[0-9]+$ ]] && total_rows=$((total_rows + n))
    done
}

if [[ $# -ge 1 ]]; then
    check_tenant "$1"
else
    for cfg in /data/projects/*/.beads/config.yaml; do
        repo=$(dirname "$(dirname "$cfg")")
        grep -q "mode: *server" "$cfg" 2>/dev/null || continue
        check_tenant "$repo"
    done
fi

echo
echo "rows the re-key would rewrite across probed tenants: $total_rows"
if [[ "$failed" -ne 0 ]]; then
    echo "VERDICT: FAILED — do not migrate."
    exit 1
fi
if [[ "$unreadable" -ne 0 ]]; then
    echo "VERDICT: INCOMPLETE — at least one tenant gave no verdict. A missing answer is not a pass."
    exit 2
fi
echo "VERDICT: PASSED — all probed tenants at v$EXPECTED_SCHEMA_VERSION and free of re-key drift."
