"""Contracts for the production orchestrator image Dockerfile."""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DOCKERFILE = _REPO_ROOT / "orchestrator-image" / "Dockerfile"
_BUILD_AND_VERIFY = _REPO_ROOT / "orchestrator-image" / "build-and-verify.sh"
_DOCKERIGNORE = _REPO_ROOT / "orchestrator-image" / ".dockerignore"


def _tier_one_embedded_bd_body(*, script: str) -> str:
    marker = 'log "T1.d.ii bd embedded-mode round-trip (init + create + list)"'
    section = script.split(marker, maxsplit=1)[1]
    before_completion = section.split('log "tier-1 verification complete"', maxsplit=1)[0]
    heredoc_start = 'docker exec "$CONTAINER" bash -lc "$(cat <<\'TIER1_BD\'\n'
    heredoc_end = '\nTIER1_BD\n)" 2>&1'

    assert before_completion.count(heredoc_start) == 1
    assert before_completion.count(heredoc_end) == 1
    return before_completion.split(heredoc_start, maxsplit=1)[1].split(heredoc_end, maxsplit=1)[0]


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


def test_beads_is_pinned_to_guarded_v1_2_2_layout() -> None:
    dockerfile = _DOCKERFILE.read_text(encoding="utf-8")

    assert "ENV BD_VERSION=1.2.2 \\" in dockerfile
    assert (
        "BD_TARBALL_SHA256=8140098a51d3b81d5548d1c5e6db1a2d9930e5d141efe2a4bff7d079c4d321e8 \\"
        in dockerfile
    )
    assert (
        "BD_BINARY_SHA256=54fc0e0581ce4c5487a5b242f0a4f34af1ef09cf056e164a1af63a6ec7aa1e0e"
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


def test_tier_one_embedded_bd_proves_enforcement_and_normalization() -> None:
    script = _BUILD_AND_VERIFY.read_text(encoding="utf-8")
    body = _tier_one_embedded_bd_body(script=script)

    expected_steps = (
        "BD=/usr/local/bin/bd",
        'test "$BD" = "$LIVESPEC_BD_PATH"',
        "export LIVESPEC_BD_GUARD_OTLP=off",
        'BD_NON_INTERACTIVE=1 "$BD" init --prefix ephemeral --skip-agents --skip-hooks '
        "--setup-exclude --role maintainer --quiet",
        '"$BD" config set status.custom "backlog,pending-approval,ready,active,acceptance"',
        "ITEM_ID=ephemeral-tier1",
        '"$BD" create --id "$ITEM_ID" --type task --title "ephemeral round-trip probe" '
        '--description "tier-1 verification" --json >create.json',
        '"$BD" show "$ITEM_ID" --json >after-create.json',
        'jq -e --arg id "$ITEM_ID" \'(if type == "array" then .[0] else . end) '
        '| .id == $id and .status == "backlog"\' after-create.json >/dev/null',
        "set +e",
        'LIVESPEC_BD_GUARD_MODE=fail "$BD" update "$ITEM_ID" --status in_progress '
        "--json >blocked.json 2>blocked.err",
        "blocked_rc=$?",
        'test "$blocked_rc" -eq 3',
        "test ! -s blocked.json",
        'grep -qF "bd update --status in_progress\' is non-lifecycle; use --status active" '
        "blocked.err",
        '"$BD" show "$ITEM_ID" --json >after-block.json',
        'jq -e --arg id "$ITEM_ID" \'(if type == "array" then .[0] else . end) '
        '| .id == $id and .status == "backlog"\' after-block.json >/dev/null',
    )

    missing_steps = tuple(step for step in expected_steps if step not in body)
    assert not missing_steps, missing_steps
    positions = tuple(body.index(step) for step in expected_steps)
    assert positions == tuple(sorted(positions))
    assert "|| true" not in body
    assert "\n  bd " not in body
