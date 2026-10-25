#!/usr/bin/env bash
# Long-running "node holder": takes GPUs for up to 4 days, starts one Ollama
# server per GPU, pulls the model, then idles. Experiments run INSIDE this
# allocation with `srun --jobid=<id> --overlap`, so we never lose the node
# between runs. See cluster/README.md.
#
#   sbatch -w gnode090 cluster/hold_node.sbatch            # 4 GPUs (default)
#   sbatch -w gnode048 --gres=gpu:3 cluster/hold_node.sbatch
#
# Writes logs/hold-<jobid>.env with NODE, JOBID, OLLAMA_URLS, MODEL.
#
#SBATCH -J lma-hold
#SBATCH -A research
#SBATCH -p u22
#SBATCH --qos=medium
#SBATCH --gres=gpu:4
#SBATCH -c 16
#SBATCH --mem=64G
#SBATCH -t 4-00:00:00
#SBATCH -o logs/%x-%j.out

set -uo pipefail
cd "$SLURM_SUBMIT_DIR"
mkdir -p logs runs
source cluster/ollama_lib.sh

echo "node=$(hostname) job=$SLURM_JOB_ID gpus=${CUDA_VISIBLE_DEVICES:-none} start=$(date)"
nvidia-smi --query-gpu=index,name,memory.used,memory.total --format=csv
install_ollama
start_ollama_servers
pull_and_warm "$MODEL"

cat > "logs/hold-$SLURM_JOB_ID.env" <<EOF
NODE=$(hostname)
JOBID=$SLURM_JOB_ID
OLLAMA_URLS=$OLLAMA_URLS
MODEL=$MODEL
OLLAMA=$OLLAMA
EOF
echo "READY $(date)"

# Restart any server that dies, forever (until the time limit).
while true; do
  sleep 60
  IFS=',' read -ra gpus <<< "${CUDA_VISIBLE_DEVICES:-0}"
  for i in "${!gpus[@]}"; do
    port=$((BASE_PORT + i))
    if ! curl -fs "http://127.0.0.1:$port/api/version" >/dev/null; then
      echo "restarting server on gpu $i ($(date))"
      CUDA_VISIBLE_DEVICES=${gpus[$i]} OLLAMA_HOST=127.0.0.1:$port OLLAMA_MODELS="$SCR/models" \
        "$OLLAMA" serve >> "logs/ollama-$SLURM_JOB_ID-gpu$i.log" 2>&1 &
    fi
  done
done
