#!/usr/bin/env bash
# Starts one Ollama server per GPU on the node, pulls the model once into
# node-local scratch, then runs scripts/run_llm.py against all servers.
#
# Submit from ~/lma on the login node, e.g.:
#   sbatch -w gnode090 cluster/llm_job.sbatch --conditions plain,recheck --seeds 0
# Any arguments are passed straight to scripts/run_llm.py.
# Override the model with:  MODEL=qwen2.5:14b sbatch ...
#
#SBATCH -J lma-llm
#SBATCH -A research
#SBATCH -p u22
#SBATCH --qos=medium
#SBATCH --gres=gpu:4
#SBATCH -c 8
#SBATCH --mem=32G
#SBATCH -t 1-00:00:00
#SBATCH -o logs/%x-%j.out

set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
mkdir -p logs runs

source cluster/ollama_lib.sh
echo "node=$(hostname) gpus=${CUDA_VISIBLE_DEVICES:-none} model=$MODEL"
install_ollama
start_ollama_servers
trap 'kill ${OLLAMA_PIDS[*]} 2>/dev/null || true' EXIT
pull_and_warm "$MODEL"

# 4. Run
WORKERS=${WORKERS:-$(( $(echo "$OLLAMA_URLS" | tr ',' '\n' | wc -l) * PARALLEL ))}
.venv/bin/python scripts/run_llm.py --model "$MODEL" --base-urls "$OLLAMA_URLS" --workers "$WORKERS" "$@"
