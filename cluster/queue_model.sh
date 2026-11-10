#!/usr/bin/env bash
# Another agent model (generality check), fully on the cluster. Run on the LOGIN node:
#   nohup bash cluster/queue_model.sh <hold_job> <tag> >> logs/queue_<tag>.log 2>&1 &
# The holder must be a hold_node job started with the model as MODEL (see handoff.md 4.3).
# Same prompts, tools, eval set, decoding and LoRA detector as the qwen 7B runs;
# nothing is tuned. Seed 0, both phrasings, the same 5 conditions as the Llama run.
# Output: runs/llm_<tag>, analysis in runs/<tag>_analysis/, end marker logs/queue/<tag>.done.
# The holder is cancelled at the end.
set -uo pipefail
cd "$(dirname "$0")/.."
J=$1; TAG=$2
mkdir -p logs/queue "runs/${TAG}_analysis"
TPY=/ssd_scratch/gr/lma/venv-train/bin/python
LORA="lora:models/det-qwen2.5-1.5b-instruct-s{seed}"
EVAL="--scenarios data/eval/scenarios_v1.json --patients data/eval/patients_v1.json --policy data/policy/clinic_policy_v1.json"

step() {  # step <name> <command...>
  local name=$1; shift
  if [ -f "logs/queue/$name.done" ]; then echo "skip $name"; return 0; fi
  echo "=== $name start $(date)"
  if "$@" > "logs/queue/$name.log" 2>&1; then touch "logs/queue/$name.done"; echo "=== $name done $(date)"
  else echo "=== $name FAILED $(date) (see logs/queue/$name.log)"; return 1; fi
}

until grep -q READY "logs/lma-hold-$J.out" 2>/dev/null; do
  squeue -h -j "$J" | grep -q . || { echo "holder $J is gone"; exit 1; }
  sleep 60
done
source "logs/hold-$J.env"
NS=$(echo "$OLLAMA_URLS" | tr ',' '\n' | wc -l)

run() {  # run <conditions>
  srun --jobid="$J" --overlap -n 1 -c 6 --mem=12G --gres=none \
    env CUDA_VISIBLE_DEVICES= HF_HOME=/ssd_scratch/gr/lma/hf HF_HUB_OFFLINE=1 \
    $TPY scripts/run_llm.py --conditions "$1" --seeds 0 --phrasings direct,indirect \
    --detector "$LORA" $EVAL --base-urls "$OLLAMA_URLS" --model "$MODEL" --workers "$NS" --out "runs/llm_$TAG"
}
echo "queue_model start $(date) job=$J tag=$TAG model=$MODEL servers=$NS"
step "${TAG}_runs" run plain,safety,plain_label,recheck,recheck_v2 || exit 1

PY="srun --jobid=$J --overlap -n 1 -c 6 --mem=12G --gres=none .venv/bin/python"
R="runs/${TAG}_analysis"
step "${TAG}_regrade" $PY scripts/regrade_check.py --runs "runs/llm_$TAG"
step "${TAG}_summary" $PY scripts/summarize_runs.py --runs "runs/llm_$TAG" --out "$R/${TAG}_v1.md"
step "${TAG}_extra" $PY scripts/extra_facts.py --runs "runs/llm_$TAG" --out "$R/${TAG}_extra_facts.md"
step "${TAG}_failures" $PY scripts/failure_breakdown.py --runs "runs/llm_$TAG" --out "$R/${TAG}_failure_breakdown.md"
scancel "$J"
touch "logs/queue/$TAG.done"
echo "queue_model finished $(date)"
