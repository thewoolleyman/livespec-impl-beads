"""Contracts for the production orchestrator image Dockerfile."""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DOCKERFILE = _REPO_ROOT / "orchestrator-image" / "Dockerfile"
_BUILD_AND_VERIFY = _REPO_ROOT / "orchestrator-image" / "build-and-verify.sh"
_DOCKERIGNORE = _REPO_ROOT / "orchestrator-image" / ".dockerignore"


def test_github_cli_apt_install_is_exactly_pinned_and_verified() -> None:
    dockerfile = _DOCKERFILE.read_text(encoding="utf-8")

    assert "ENV GH_VERSION=2.96.0\n" in dockerfile
    assert 'apt-get install -y --no-install-recommends gh="${GH_VERSION}"' in dockerfile
    assert 'test "$(gh --version | awk \'NR == 1 {print $3}\')" = "${GH_VERSION}"' in dockerfile


def test_build_and_verify_asserts_the_container_github_cli_version() -> None:
    script = _BUILD_AND_VERIFY.read_text(encoding="utf-8")

    assert 'log "T1.0 gh version"' in script
    assert 'version="$(gh --version | awk "NR == 1 {print \\$3}")"' in script
    assert 'test "$version" = "$GH_VERSION"' in script


def test_beads_is_pinned_to_guarded_v1_1_2_layout() -> None:
    dockerfile = _DOCKERFILE.read_text(encoding="utf-8")

    assert "ENV BD_VERSION=1.1.2 \\" in dockerfile
    assert (
        "BD_TARBALL_SHA256=a72d71ed374955dc9f83a0f90b54bd7b6a0016709dd1676ae2e368651ed401c2 \\"
        in dockerfile
    )
    assert (
        "BD_BINARY_SHA256=6d767629e90560506d0ea3de9823aef48386414f5425d8853e2ae3312cad9a82"
        in dockerfile
    )
    assert "install -m 0755 /tmp/bd /usr/local/bin/bd-real" in dockerfile
    assert "COPY bd-guard /tmp/bd-guard" in dockerfile
    assert "install -m 0755 /tmp/bd-guard/bd-guard.sh /usr/local/bin/bd" in dockerfile
    assert (
        "install -m 0755 /tmp/bd-guard/bd-guard-emit.py /usr/local/bin/bd-guard-emit.py"
        in dockerfile
    )
    assert "bd-guard-wrapper-sentinel" in dockerfile
    assert "ENV LIVESPEC_BD_PATH=/usr/local/bin/bd" in dockerfile


def test_orchestrator_image_context_allows_and_cleans_bd_guard_payload() -> None:
    dockerignore = _DOCKERIGNORE.read_text(encoding="utf-8")
    script = _BUILD_AND_VERIFY.read_text(encoding="utf-8")

    assert "!bd-guard" in dockerignore
    assert "!bd-guard/**" in dockerignore
    assert 'rm -rf "$HERE/bd-guard" || true' in script
    assert 'cp -R "$HERE/../bd-guard" "$HERE/bd-guard"' in script
    assert 'find "$HERE/bd-guard" -type d -name __pycache__ -prune -exec rm -rf {} +' in script


def test_tier_one_verifies_guarded_beads_contract_without_host_mutation() -> None:
    script = _BUILD_AND_VERIFY.read_text(encoding="utf-8")

    assert 'log "T1.1 guarded bd layout"' in script
    assert 'test "$LIVESPEC_BD_PATH" = /usr/local/bin/bd' in script
    assert "grep -q" in script
    assert "bd-guard-wrapper-sentinel" in script
    assert "/usr/local/bin/bd" in script
    assert 'echo "$BD_BINARY_SHA256  /usr/local/bin/bd-real" | sha256sum -c -' in script
    assert '/usr/local/bin/bd-real version | grep -q "bd version $BD_VERSION"' in script
    assert '/usr/local/bin/bd version | grep -q "bd version $BD_VERSION"' in script
