#!/bin/bash
# SessionStart hook for dilf — see INTEROP.md for the dilf↔draught-master
# contract this session is operating under.

set -euo pipefail

# Only run automatic setup in remote Claude Code on the web. Local
# sessions can opt-in by setting CLAUDE_CODE_REMOTE=true manually.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
    exit 0
fi

cd "$CLAUDE_PROJECT_DIR"

printf '\n'
printf '======================================================================\n'
printf ' dilf — pedagogy library consumed by jfrancoiscollin/draught-master\n'
printf '======================================================================\n'
printf ' Public API contract: INTEROP.md\n'
printf ' Snapshot test:       pedagogy/tests/test_public_api.py\n'
printf ' Breaking changes:    follow the two-step dance in INTEROP.md\n'
printf '======================================================================\n'

pip install -e ".[dev,extract,explanations]" --quiet --disable-pip-version-check

# One-line status of the public-API snapshot. Non-blocking — the
# session still starts even if the snapshot is red, so the dev can
# see and fix it.
if pytest pedagogy/tests/test_public_api.py -q --no-header --tb=no 2>/dev/null \
        | tail -1 | grep -qE "^[0-9]+ passed"; then
    printf ' [✓] public API snapshot test green\n'
else
    printf ' [✗] public API snapshot test FAILING — check INTEROP.md surface\n'
fi
printf '======================================================================\n\n'
