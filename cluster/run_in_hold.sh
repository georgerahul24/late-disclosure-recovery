#!/usr/bin/env bash
# Run a command inside a running hold_node job (shares its GPUs/servers).
#   cluster/run_in_hold.sh <jobid> scripts/run_llm.py --conditions plain --out runs/x
# The first argument after the job id is a python script; the Ollama URLs and
# model from logs/hold-<jobid>.env are passed as --base-urls / --model.
# Use CPUS=<n> to change the CPUs given to the step (default 4).
set -euo pipefail
cd "$(dirname "$0")/.."
JOB=$1; shift
ENV=logs/hold-$JOB.env
[ -f "$ENV" ] || { echo "no $ENV yet (holder not READY?)"; exit 1; }
source "$ENV"
SCRIPT=$1; shift
# URLS=<comma list> restricts the run to some servers (e.g. while a GPU trains)
URLS=${URLS:-$OLLAMA_URLS}
WORKERS=${WORKERS:-$(( $(echo "$URLS" | tr ',' '\n' | wc -l) * ${PARALLEL:-2} ))}
exec srun --jobid="$JOB" --overlap -n 1 -c "${CPUS:-4}" --mem=8G \
  .venv/bin/python "$SCRIPT" --base-urls "$URLS" --model "${RUN_MODEL:-$MODEL}" --workers "$WORKERS" "$@"
