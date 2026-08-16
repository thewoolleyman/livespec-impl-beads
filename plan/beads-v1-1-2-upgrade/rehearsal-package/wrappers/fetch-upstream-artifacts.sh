#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  printf '%s\n' "usage: $0 OUT_DIR" >&2
  exit 64
fi

out_dir=$1
mkdir -p "$out_dir"
cd "$out_dir"

curl -fsSLO https://github.com/gastownhall/beads/releases/download/v1.1.2/checksums.txt
curl -fsSLO https://github.com/gastownhall/beads/releases/download/v1.1.2/beads_1.1.2_linux_amd64.tar.gz
curl -fsSLO https://github.com/gastownhall/beads/releases/download/v1.1.2/beads-v1.1.2.spdx.json

printf '%s  %s\n' \
  a72d71ed374955dc9f83a0f90b54bd7b6a0016709dd1676ae2e368651ed401c2 \
  beads_1.1.2_linux_amd64.tar.gz | sha256sum -c -
printf '%s  %s\n' \
  b05ca7f525f05e50691a4329b13aa87f10bc93160fe8d4d1ca371867701b58e6 \
  beads-v1.1.2.spdx.json | sha256sum -c -

tar -xzf beads_1.1.2_linux_amd64.tar.gz bd
printf '%s  %s\n' \
  6d767629e90560506d0ea3de9823aef48386414f5425d8853e2ae3312cad9a82 \
  bd | sha256sum -c -

./bd version
