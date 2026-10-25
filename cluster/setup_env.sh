#!/usr/bin/env bash
# Run ONCE on the cluster login node, inside ~/lma, after cluster/sync.sh push.
# Creates ~/lma/.venv with the small CPU deps (no torch). Home quota is tight
# (50G, nearly full), so we reuse the existing uv cache.
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/.local/bin:$PATH"
export UV_CACHE_DIR=${UV_CACHE_DIR:-$HOME/uv_cache}
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e ".[ml,dev]"
.venv/bin/python -m pytest -q
echo "env ok"
