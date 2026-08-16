#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  printf '%s\n' "usage: $0 OUT_DIR" >&2
  exit 64
fi

out_dir=$1
mkdir -p "$out_dir"

wrapper=/data/projects/1password-env-wrapper/with-livespec-env.sh
bd_path=/usr/local/bin/bd

survey_one() {
  name=$1
  repo_root=$2
  target_dir="$out_dir/$name"
  mkdir -p "$target_dir"
  (
    cd "$repo_root"
    "$wrapper" -- "$bd_path" list --status all --limit 0 --json > "$target_dir/all-issues.json"
  )
  python3 "$(dirname "$0")/../wrappers/identity-probe.py" \
    "$target_dir/all-issues.json" > "$target_dir/identity-probe.json"
}

survey_one dense-lifecycle-policy /data/projects/livespec
survey_one factory-policy /data/projects/livespec-orchestrator-beads-fabro
survey_one sparse-closed-only /data/projects/livespec-driver-codex
