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

MODEL=${MODEL:-qwen2.5:7b-instruct-q8_0}
OLLAMA_VERSION=${OLLAMA_VERSION:-v0.9.6}
PARALLEL=${PARALLEL:-2}          # concurrent requests per server (KV cache per slot ~0.5 GB at 8k ctx)
CTX=${CTX:-8192}
SCR=/ssd_scratch/gr/lma
mkdir -p "$SCR"

echo "node=$(hostname) gpus=${CUDA_VISIBLE_DEVICES:-none} model=$MODEL"
nvidia-smi --query-gpu=index,name,memory.used,memory.total --format=csv

# 1. Ollama binary (node-local, cached across jobs on the same node)
if [ ! -x "$SCR/ollama/bin/ollama" ]; then
  mkdir -p "$SCR/ollama"
  base=https://github.com/ollama/ollama/releases/download/$OLLAMA_VERSION
  if curl -fsSL "$base/ollama-linux-amd64.tgz" -o "$SCR/ollama.tgz"; then
    tar -xzf "$SCR/ollama.tgz" -C "$SCR/ollama"
  else
    curl -fsSL "$base/ollama-linux-amd64.tar.zst" -o "$SCR/ollama.tar.zst"
    zstd -dc "$SCR/ollama.tar.zst" | tar -x -C "$SCR/ollama"
  fi
  rm -f "$SCR"/ollama.tgz "$SCR"/ollama.tar.zst
fi
OLLAMA="$SCR/ollama/bin/ollama"
"$OLLAMA" --version || true

# 2. One server per GPU
export OLLAMA_MODELS="$SCR/models"
export OLLAMA_CONTEXT_LENGTH=$CTX
export OLLAMA_NUM_PARALLEL=$PARALLEL
export OLLAMA_KEEP_ALIVE=-1
IFS=',' read -ra GPUS <<< "${CUDA_VISIBLE_DEVICES:-0}"
URLS=()
PIDS=()
for i in "${!GPUS[@]}"; do
  port=$((11434 + i))
  CUDA_VISIBLE_DEVICES=${GPUS[$i]} OLLAMA_HOST=127.0.0.1:$port \
    "$OLLAMA" serve > "logs/ollama-$SLURM_JOB_ID-gpu$i.log" 2>&1 &
  PIDS+=($!)
  URLS+=("http://127.0.0.1:$port/v1")
done
trap 'kill ${PIDS[*]} 2>/dev/null || true' EXIT
for i in "${!GPUS[@]}"; do
  for _ in $(seq 60); do curl -fs "http://127.0.0.1:$((11434 + i))/api/version" >/dev/null && break; sleep 2; done
done

# 3. Model (pulled once; all servers share OLLAMA_MODELS)
OLLAMA_HOST=127.0.0.1:11434 "$OLLAMA" pull "$MODEL"
# Warm every server so the first episodes do not time out on model load.
for i in "${!GPUS[@]}"; do
  curl -fs "http://127.0.0.1:$((11434 + i))/api/generate" -d "{\"model\":\"$MODEL\",\"prompt\":\"hi\",\"stream\":false}" >/dev/null &
done
wait_warm() { for p in $(jobs -p); do [[ " ${PIDS[*]} " == *" $p "* ]] || wait "$p"; done; }
wait_warm
nvidia-smi --query-gpu=index,memory.used --format=csv

# 4. Run
BASE_URLS=$(IFS=,; echo "${URLS[*]}")
WORKERS=${WORKERS:-$(( ${#GPUS[@]} * PARALLEL ))}
.venv/bin/python scripts/run_llm.py --model "$MODEL" --base-urls "$BASE_URLS" --workers "$WORKERS" "$@"
