#!/bin/sh
set -eu

# Secret-leak guard for the attended O4 rehearsal's receipt bundle.
#
# TWO ARMS, because the name-shaped arm alone was structurally blind to the leak
# it exists to catch. Arm 1 matches a shell-style `BEADS_DOLT_PASSWORD=`
# assignment; it is RETAINED rather than replaced, because it still fires after
# the credential has been rotated, when arm 2's value no longer matches anything
# in the bundle. Arm 2 matches the VALUE itself, which is how a real leak looks:
# inside a DSN, a connection string, a JSON field, or an error message echoed by
# a client -- none of which carries the variable name.
#
# The value reaches this script through the ENVIRONMENT and reaches grep on
# STDIN. It is never an argv element (argv is visible in `ps` and in shell
# history) and it is never written to a file. `-F` keeps a secret containing
# regex metacharacters from being interpreted as a pattern.
#
# FAIL-CLOSED: every path that cannot ESTABLISH the no-leak property exits
# non-zero WITHOUT emitting the receipt. Publishing a clean secret_scan receipt
# for a scan that did not happen is worse than publishing none, because the
# operator's artifact bundle then carries positive evidence for a property
# nobody measured, and nothing downstream re-asks the question.

if [ "$#" -ne 2 ]; then
  printf '%s\n' "usage: $0 RECEIPT_ROOT SANITIZED_ENV_NAMES" >&2
  exit 64
fi

if [ -z "${BEADS_DOLT_PASSWORD:-}" ]; then
  printf '%s\n' "HALT: BEADS_DOLT_PASSWORD unset or empty; cannot scan for the secret value" >&2
  exit 70
fi

if grep -R "BEADS_DOLT_PASSWORD=.*" "$1" >/dev/null 2>&1; then
  printf '%s\n' "HALT: receipt root contains secret-looking value" >&2
  exit 70
fi

# grep's three exits are distinguished deliberately: 0 is a hit, 1 is a clean
# scan, anything else is a scan that did not happen. The original `if grep ...`
# form collapsed the last two, so an unreadable receipt root read as "clean".
scan_status=0
printf '%s\n' "$BEADS_DOLT_PASSWORD" | grep -R -F -f - "$1" >/dev/null 2>&1 || scan_status=$?
if [ "$scan_status" -eq 0 ]; then
  printf '%s\n' "HALT: receipt root contains the secret value itself" >&2
  exit 70
fi
if [ "$scan_status" -ne 1 ]; then
  printf '%s\n' "HALT: secret-value scan did not complete (grep exit $scan_status)" >&2
  exit 70
fi

printf '{"schema":"livespec.beads_v112_rehearsal.secret_scan_receipt.v1","sanitized_env_names":"%s"}\n' "$2"
