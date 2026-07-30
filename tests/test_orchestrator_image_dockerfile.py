"""Contracts for the production orchestrator image Dockerfile."""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DOCKERFILE = _REPO_ROOT / "orchestrator-image" / "Dockerfile"
_BUILD_AND_VERIFY = _REPO_ROOT / "orchestrator-image" / "build-and-verify.sh"


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
