#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  printf '%s\n' "usage: $0 OUT_DIR" >&2
  exit 64
fi

case "$(go version)" in
  *go1.26.2*) ;;
  *)
    printf '%s\n' "HALT: fixture producer requires go1.26.2" >&2
    exit 70
    ;;
esac

out_dir=$1
mkdir -p "$out_dir"
cd "$out_dir"

archive=beads-v1.0.5-6a3f515c.tar.gz
curl -fsSL \
  https://github.com/gastownhall/beads/archive/6a3f515ced18406c189c55fff789a4925bfaa35c.tar.gz \
  -o "$archive"
sha256sum "$archive"
tar -xzf "$archive"
cd beads-6a3f515ced18406c189c55fff789a4925bfaa35c
go build -trimpath -ldflags=-buildid= -o ../bd ./cmd/bd
cd ..
sha256sum bd
./bd version
