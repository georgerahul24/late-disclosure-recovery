#!/usr/bin/env bash
# Shared helpers: install Ollama on node-local scratch and start one server
# per allocated GPU. Sourced by llm_job.sbatch and hold_node.sbatch.
#
# After `start_ollama_servers`, these are set:
#   OLLAMA       path to the binary
#   OLLAMA_URLS  comma-separated OpenAI base URLs (http://127.0.0.1:<port>/v1)
#   OLLAMA_PIDS  array of server PIDs

MODEL=${MODEL:-qwen2.5:7b-instruct-q8_0}
OLLAMA_ARCHIVE=${OLLAMA_ARCHIVE:-$HOME/ollama}   # George's Ollama bundle (zstd tar, v0.21.2)
OLLAMA_VERSION=${OLLAMA_VERSION:-v0.9.6}          # download fallback only
PARALLEL=${PARALLEL:-2}   # concurrent requests per server
CTX=${CTX:-8192}
BASE_PORT=${BASE_PORT:-11434}
SCR=${SCR:-/ssd_scratch/gr/lma}

install_ollama() {
  mkdir -p "$SCR"
  df -h "$SCR" | tail -1
  if [ ! -x "$SCR/ollama/bin/ollama" ]; then
    mkdir -p "$SCR/ollama"
    # 1st choice: the bundle in home (fast copy over NFS). Needs zstd, which
    # compute nodes have and the login node does not.
    if [ -s "$OLLAMA_ARCHIVE" ] && zstd -dc "$OLLAMA_ARCHIVE" | tar -x -C "$SCR/ollama"; then
      OLLAMA="$SCR/ollama/bin/ollama"; "$OLLAMA" --version || true; return 0
    fi
    local base=https://github.com/ollama/ollama/releases/download/$OLLAMA_VERSION
    if curl -fsSL "$base/ollama-linux-amd64.tgz" -o "$SCR/ollama.tgz.part" && mv "$SCR/ollama.tgz.part" "$SCR/ollama.tgz"; then
      tar -xzf "$SCR/ollama.tgz" -C "$SCR/ollama"
    else
      curl -fsSL "$base/ollama-linux-amd64.tar.zst" -o "$SCR/ollama.tar.zst"
      zstd -dc "$SCR/ollama.tar.zst" | tar -x -C "$SCR/ollama"
    fi
    rm -f "$SCR"/ollama.tgz "$SCR"/ollama.tar.zst
  fi
  OLLAMA="$SCR/ollama/bin/ollama"
  "$OLLAMA" --version || true
}

start_ollama_servers() {
  export OLLAMA_MODELS="$SCR/models"
  # All servers share one models dir. Create it up front and disable startup
  # pruning, otherwise servers race on "remove .../manifests" and die.
  mkdir -p "$OLLAMA_MODELS/manifests" "$OLLAMA_MODELS/blobs" "$SCR/tmp"
  # /tmp can be full on some nodes (gnode082, 29 Oct): GPU discovery then fails
  # silently and Ollama runs on CPU. Keep its temp files on node scratch.
  export TMPDIR="$SCR/tmp"
  export OLLAMA_NOPRUNE=1
  export OLLAMA_CONTEXT_LENGTH=$CTX
  export OLLAMA_NUM_PARALLEL=$PARALLEL
  export OLLAMA_KEEP_ALIVE=-1
  local gpus
  IFS=',' read -ra gpus <<< "${CUDA_VISIBLE_DEVICES:-0}"
  local urls=()
  OLLAMA_PIDS=()
  for i in "${!gpus[@]}"; do
    local port=$((BASE_PORT + i))
    CUDA_VISIBLE_DEVICES=${gpus[$i]} OLLAMA_HOST=127.0.0.1:$port \
      "$OLLAMA" serve > "logs/ollama-${SLURM_JOB_ID:-x}-gpu$i.log" 2>&1 &
    OLLAMA_PIDS+=($!)
    urls+=("http://127.0.0.1:$port/v1")
  done
  OLLAMA_URLS=$(IFS=,; echo "${urls[*]}")
  for i in "${!gpus[@]}"; do
    for _ in $(seq 90); do curl -fs "http://127.0.0.1:$((BASE_PORT + i))/api/version" >/dev/null && break; sleep 2; done
  done
}

pull_and_warm() {  # $1 = model
  local m=${1:-$MODEL}
  # node DNS sometimes times out; retry
  for attempt in 1 2 3 4 5 6; do
    OLLAMA_HOST=127.0.0.1:$BASE_PORT "$OLLAMA" pull "$m" && break
    echo "pull failed (attempt $attempt), retrying"; sleep 20
  done
  local n
  n=$(echo "$OLLAMA_URLS" | tr ',' '\n' | wc -l)
  for i in $(seq 0 $((n - 1))); do
    curl -fs "http://127.0.0.1:$((BASE_PORT + i))/api/generate" \
      -d "{\"model\":\"$m\",\"prompt\":\"hi\",\"stream\":false,\"options\":{\"num_predict\":1}}" >/dev/null &
  done
  wait $(jobs -p | grep -vxF "$(printf '%s\n' "${OLLAMA_PIDS[@]}")") 2>/dev/null || true
  nvidia-smi --query-gpu=index,memory.used,memory.total --format=csv
}
