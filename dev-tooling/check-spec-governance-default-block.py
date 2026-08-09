"""Verify this repo's commented spec_governance default block."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from livespec_runtime.spec_governance import verify_livespec_jsonc_default_block
from returns.result import Failure, Success

__all__: list[str] = ["main"]

_REPO_ROOT = Path(__file__).resolve().parent.parent
_LIVESPEC_JSONC = _REPO_ROOT / ".livespec.jsonc"
_LOGGER = logging.getLogger("spec_governance_default_block")


def main() -> int:
    """Run the shared default-block verifier against this checkout."""
    logging.basicConfig(format="%(message)s", level=logging.INFO)
    result = verify_livespec_jsonc_default_block(path=_LIVESPEC_JSONC)
    if isinstance(result, Success):
        payload: dict[str, Any] = result.unwrap()
        _LOGGER.info(json.dumps(payload, sort_keys=True))
        return 0
    if isinstance(result, Failure):
        _LOGGER.error(result.failure())
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
