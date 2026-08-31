# livespec dark-factory orchestrator — Beads/Dolt + Fabro, Docker-in-Docker.
#
# Step 1 of the W7 orchestrator-convergence epic (livespec-impl-beads-8bc).
# Builds the PRODUCTION orchestrator image from the known-good DinD recipe the
# step-0 spike proved (archive/research/w7-orchestrator-convergence/dind-spike.md). The
# container runs an *inner* dockerd; Fabro spawns its sandboxes on that inner
# daemon, fully decoupled from the host daemon (DinD, not DooD — no host socket
# is ever mounted). An ephemeral in-container Dolt sql-server is available for a
# throwaway/scratch ledger; the production family-tenant ledger is EXTERNAL and
# injected as an endpoint at run time.
#
# The image is SECRET-FREE by construction. Every credential (model key, GitHub
# token, per-tenant Dolt password, Honeycomb ingest key, Claude Code OAuth
# token) is injected at `docker run` via env / mounts; NONE is baked in. See
# README.md for the run invocation and the injectable externals.

# --- Base: glibc >= 2.39 is a HARD FLOOR (fabro v0.254.0 links GLIBC_2.39). ---
# debian:12 (glibc 2.36) is TOO OLD; Alpine (musl) won't run the binary at all.
# ubuntu:24.04 (noble) ships glibc 2.39 — exactly the minimum. Proven by the
# step-0 spike's base-image table.
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

# --- Base system + inner Docker daemon. distro docker.io on noble == Docker
#     29.x (containerd image store / overlayfs snapshotter), proven to nest
#     cleanly. Plus the orchestrator's host-level runtime: git, ca-certs,
#     curl/jq for provisioning, python3 (3.12 on noble) plus the small stdlib
#     compatibility shim imported by the mounted dispatcher runtime, gh
#     (GitHub CLI), and iptables (dockerd networking inside the container). ---
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        docker.io \
        ca-certificates \
        curl \
        gpg \
        jq \
        git \
        libatomic1 \
        python3 \
        python3-typing-extensions \
        iptables \
        uidmap \
 && rm -rf /var/lib/apt/lists/*

# --- GitHub CLI (gh) — the dispatcher's PR/merge surface. Installed from the
#     official cli.github.com apt repo (keyring pinned) with an exact package
#     version so apt/Docker cache state cannot silently select a different gh. ---
ENV GH_VERSION=2.96.0
RUN mkdir -p -m 755 /etc/apt/keyrings \
 && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
        -o /etc/apt/keyrings/githubcli-archive-keyring.gpg \
 && chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
 && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
        > /etc/apt/sources.list.d/github-cli.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends gh="${GH_VERSION}" \
 && test "$(gh --version | awk 'NR == 1 {print $3}')" = "${GH_VERSION}" \
 && rm -rf /var/lib/apt/lists/*

# --- mise — needed by the dispatcher itself after a PR merge. Fabro sandboxes
#     provision their own toolchain, but the orchestrator container owns the
#     post-merge primary refresh and janitor checkout (`mise trust` +
#     `mise exec -- just check`), so mise must be present in the production
#     runtime too. ---
RUN mkdir -p -m 755 /etc/apt/keyrings \
 && curl -fsSL https://mise.jdx.dev/gpg-key.pub \
        | gpg --dearmor -o /etc/apt/keyrings/mise-archive-keyring.gpg \
 && chmod go+r /etc/apt/keyrings/mise-archive-keyring.gpg \
 && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/mise-archive-keyring.gpg] https://mise.jdx.dev/deb stable main" \
        > /etc/apt/sources.list.d/mise.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends mise \
 && rm -rf /var/lib/apt/lists/* \
 && mise --version

# --- uv (Astral) — the Python toolchain manager (family convention: uv pins
#     Python + Python packages; mise pins non-Python binaries). Pinned to the
#     family version (0.5.20) from the official installer, then verified. ---
ENV UV_VERSION=0.5.20
RUN curl -fsSL "https://astral.sh/uv/${UV_VERSION}/install.sh" \
        -o /tmp/uv-install.sh \
 && env UV_INSTALL_DIR=/usr/local/bin sh /tmp/uv-install.sh \
 && rm -f /tmp/uv-install.sh \
 && /usr/local/bin/uv --version

# --- bd (beads CLI), pinned v1.2.2 behind the lifecycle guard. The official
#     release TARBALL is content-pinned by sha256; the extracted binary is
#     re-verified and installed as the guard's private delegate at bd-real.
#
#     NEVER set BD_VERSION to 1.2.0 or 1.2.1. Upstream published both by
#     accident on 2026-08-11 without release testing. Running the v1.2.1
#     binary EVEN ONCE migrates the database schema from v53 to v65, after
#     which every v1.1.2 / v1.2.2 binary refuses with "schema version
#     mismatch: database is at v65, binary knows up to v53". We run a SHARED
#     multi-tenant Dolt server, so one invocation strands that tenant for
#     every client in the family. v1.2.1 is marked prerelease rather than
#     withdrawn, so it is still downloadable: this is a live hazard, not
#     history. The current stable is v1.2.2, a recovery release re-issuing
#     the tested 1.1 line. If a database is already at v65, recover per
#     docs/RECOVERY-1.2.1.md at tag v1.2.2 and upgrade EVERY clone first --
#     a leftover v1.2.1 binary silently re-migrates. See AGENTS.md
#     "Beads runtime prerequisites". ---
ENV BD_VERSION=1.2.2 \
    BD_TARBALL_SHA256=8140098a51d3b81d5548d1c5e6db1a2d9930e5d141efe2a4bff7d079c4d321e8 \
    BD_BINARY_SHA256=54fc0e0581ce4c5487a5b242f0a4f34af1ef09cf056e164a1af63a6ec7aa1e0e
RUN curl -fsSL -o /tmp/beads.tar.gz \
        "https://github.com/gastownhall/beads/releases/download/v${BD_VERSION}/beads_${BD_VERSION}_linux_amd64.tar.gz" \
 && echo "${BD_TARBALL_SHA256}  /tmp/beads.tar.gz" | sha256sum -c - \
 && tar -xzf /tmp/beads.tar.gz -C /tmp \
 && echo "${BD_BINARY_SHA256}  /tmp/bd" | sha256sum -c - \
 && install -m 0755 /tmp/bd /usr/local/bin/bd-real \
 && rm -rf /tmp/beads.tar.gz /tmp/bd /tmp/README.md /tmp/LICENSE /tmp/CHANGELOG.md \
 && /usr/local/bin/bd-real version

# --- bd lifecycle guard. The tracked wrapper is the public entry point at
#     /usr/local/bin/bd; normal callers and LIVESPEC_BD_PATH never point at the
#     private /usr/local/bin/bd-real delegate. The mode file is non-secret and
#     defaults the image to warn-mode observation. ---
COPY bd-guard /tmp/bd-guard
RUN install -m 0755 /tmp/bd-guard/bd-guard.sh /usr/local/bin/bd \
 && install -m 0755 /tmp/bd-guard/bd-guard-emit.py /usr/local/bin/bd-guard-emit.py \
 && mkdir -p /usr/local/etc \
 && printf 'warn\n' > /usr/local/etc/livespec-bd-guard.mode \
 && chmod 0644 /usr/local/etc/livespec-bd-guard.mode \
 && grep -q 'bd-guard-wrapper-sentinel' /usr/local/bin/bd \
 && echo "${BD_BINARY_SHA256}  /usr/local/bin/bd-real" | sha256sum -c - \
 && /usr/local/bin/bd-real version | grep -q "bd version ${BD_VERSION}" \
 && /usr/local/bin/bd version | grep -q "bd version ${BD_VERSION}" \
 && rm -rf /tmp/bd-guard

# --- dolt, pinned v2.1.4 (matches the host pin) at /usr/local/bin/dolt — for
#     the ephemeral in-container ledger substrate (the spike's Goal-5 pattern).
#     The production family-tenant ledger is EXTERNAL, not run here. ---
ENV DOLT_VERSION=2.1.4 \
    DOLT_TARBALL_SHA256=f3bd2329fc469d9d557af377dc36280da2c4ed13315cc2e4a82fe2b5ae682929
RUN curl -fsSL -o /tmp/dolt.tar.gz \
        "https://github.com/dolthub/dolt/releases/download/v${DOLT_VERSION}/dolt-linux-amd64.tar.gz" \
 && echo "${DOLT_TARBALL_SHA256}  /tmp/dolt.tar.gz" | sha256sum -c - \
 && tar -xzf /tmp/dolt.tar.gz -C /tmp \
 && install -m 0755 /tmp/dolt-linux-amd64/bin/dolt /usr/local/bin/dolt \
 && rm -rf /tmp/dolt.tar.gz /tmp/dolt-linux-amd64 \
 && /usr/local/bin/dolt version

# --- Fabro binary. Pin the version + the glibc floor together. The binary is
#     COPIED in (not apt-installed). It is fetched into the build context from
#     the host's ~/.fabro/bin/fabro (v0.254.0) by build-and-verify.sh and is
#     gitignored — NEVER committed (it is a 111MB blob, and pinning the floor
#     here documents the coupling). ---
ENV FABRO_VERSION=0.254.0
COPY fabro /usr/local/bin/fabro
RUN chmod +x /usr/local/bin/fabro \
 && /usr/local/bin/fabro version | head -1

# --- LIVESPEC_BD_PATH: the impl-beads wrappers shell out to $LIVESPEC_BD_PATH.
ENV LIVESPEC_BD_PATH=/usr/local/bin/bd

# --- Storage driver: overlay2/overlayfs, but /var/lib/docker MUST be on a
#     non-overlay filesystem or the inner daemon silently falls back to vfs.
#     The VOLUME declaration is load-bearing (mirrors the official docker:dind
#     image). At `docker run` time this is backed by an ext4 volume/bind. ---
VOLUME /var/lib/docker

# --- Fabro web-UI / control-plane port. The in-container fabro server listens
#     on 0.0.0.0:32276 (set by the entrypoint's templated settings.toml) so a
#     published port is reachable; the README documents binding it to the HOST
#     loopback only (-p 127.0.0.1:32276:32276) behind dev-token auth. ---
EXPOSE 32276

# --- Plugin payload (the .claude-plugin/scripts tree: bin/ wrappers, the
#     livespec_orchestrator_beads_fabro package, and the vendored runtime).
#     Staged into the build context as `plugin-scripts` by the build scripts
#     (the context is orchestrator-image/, not the repo root). Carries the
#     mint-app-token CLI the entrypoint's provision_github runs BEFORE any
#     in-container clone exists; LIVESPEC_MINT_APP_TOKEN_BIN pins the baked
#     location. Code only — the image stays secret-free. ---
COPY plugin-scripts /opt/livespec-orchestrator/scripts
ENV LIVESPEC_MINT_APP_TOKEN_BIN=/opt/livespec-orchestrator/scripts/bin/mint_app_token.py

# --- Entrypoint supervisor: starts dockerd -> waits for the socket ->
#     provisions ~/.fabro/settings.toml + the headless fabro server (LLM +
#     GitHub, non-interactive) -> execs the dispatcher (or a passed command). ---
COPY orchestrator-entrypoint.sh /usr/local/bin/orchestrator-entrypoint.sh
RUN chmod +x /usr/local/bin/orchestrator-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/orchestrator-entrypoint.sh"]
# Default command: the dispatcher loop is the orchestrator's reason for being,
# but it requires the injectable externals (ledger endpoint + creds) and a
# mounted impl-beads checkout, so the image defaults to an interactive shell;
# operators pass the real `dispatcher.py loop ...` command (see README).
CMD ["bash"]
