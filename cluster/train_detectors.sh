#!/usr/bin/env bash
# Train the LoRA detectors on ONE GPU inside the holder job.
#   1. free a GPU: unload the Ollama model from that GPU's server, e.g. GPU 3:
#        curl 127.0.0.1:11437/api/generate -d '{"model":"<m>","keep_alive":0}'
#      (and keep that server out of --base-urls for LLM runs while training)
#   2. srun --jobid=<hold> --overlap -n 1 -c 8 --mem=32G --gres=gpu:4 \
#        env GPU=3 bash cluster/train_detectors.sh
# Trains Qwen2.5-1.5B-Instruct (main) and Qwen2.5-0.5B (small) x seeds 0,1,2
# (proposal section 5). Adapters go to node scratch and are copied to
# ~/lma/models/ (small, git-ignored); metrics.json to runs/detector/.
set -euo pipefail
cd "$(dirname "$0")/.."
SCR=${SCR:-/ssd_scratch/gr/lma}
export HF_HOME=$SCR/hf
export CUDA_VISIBLE_DEVICES=${GPU:-3}
PY=$SCR/venv-train/bin/python
SEEDS=${SEEDS:-"0 1 2"}
BASES=${BASES:-"Qwen/Qwen2.5-1.5B-Instruct Qwen/Qwen2.5-0.5B"}
mkdir -p runs/detector models
nvidia-smi --query-gpu=index,memory.used,memory.total --format=csv
for base in $BASES; do
  short=$(basename "$base" | tr 'A-Z' 'a-z')
  for s in $SEEDS; do
    out=$SCR/models/det-$short-s$s
    if [ -f "$out/metrics.json" ]; then echo "skip $out"; continue; fi
    echo "=== $base seed $s $(date)"
    $PY scripts/train_detector.py --base "$base" --seed "$s" --out "$out" \
      --seeds data/detector/seeds_v1_decon.json --paraphrases data/detector/paraphrases_v1_decon.json
    mkdir -p "models/det-$short-s$s" && cp -r "$out"/. "models/det-$short-s$s/"
    cp "$out/metrics.json" "runs/detector/det-$short-s$s.metrics.json"
  done
done
echo "all done $(date)"
