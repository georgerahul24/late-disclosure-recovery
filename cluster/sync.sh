#!/usr/bin/env bash
# Run on YOUR LAPTOP from the repo root.
#   cluster/sync.sh push   copy code + data to the cluster (~/lma)
#   cluster/sync.sh pull   copy results (runs/, logs/) back into this repo
# The cluster has no GitHub credentials for the private repo, so we rsync.
set -euo pipefail
HOST=${LMA_HOST:-gr@ada-gw1.iiit.ac.in}
REMOTE=${LMA_REMOTE:-lma}
case "${1:-push}" in
  push)
    rsync -az --delete \
      --exclude .venv --exclude .git --exclude runs --exclude logs --exclude models \
      --exclude __pycache__ --exclude .pytest_cache --exclude '*.egg-info' \
      --exclude /data/synthea/ \
      ./ "$HOST:$REMOTE/"
    # data/synthea/ is GENERATED ON THE CLUSTER (scripts/synthea_to_records.py)
    # and only flows back with `pull`; never let --delete wipe it.
    echo "pushed to $HOST:$REMOTE" ;;
  pull)
    mkdir -p runs logs
    rsync -az "$HOST:$REMOTE/runs/" runs/
    rsync -az "$HOST:$REMOTE/logs/" logs/ || true
    mkdir -p data/synthea
    rsync -az "$HOST:$REMOTE/data/synthea/" data/synthea/ || true
    echo "pulled runs/, logs/ and data/synthea/" ;;
  *) echo "usage: $0 push|pull"; exit 1 ;;
esac
