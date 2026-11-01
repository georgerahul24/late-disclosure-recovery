#!/usr/bin/env bash
# Second agent model (generality check), fully on the cluster. Run on the LOGIN node:
#   nohup bash cluster/queue_llama.sh <job_a> <job_b> >> logs/queue_llama.log 2>&1 &
# Both jobs are hold_node jobs started with MODEL=llama3.1:8b-instruct-q8_0,
# CTX=8192, PARALLEL=1 (llama's KV cache is larger than qwen's; 2 parallel slots
# spill to CPU on an 11 GB card) and 2 GPUs each.
# Same prompts, tools, eval set, decoding and LoRA detector as the qwen runs;
# nothing was tuned for llama. Seed 0, both phrasings.
#   job_a: plain, safety, plain_label      job_b: recheck, recheck_v2
# Then the analysis (inside job_a) goes to runs/llama_analysis/ and both jobs are released.
set -uo pipefail
cd "$(dirname "$0")/.."
A=$1; B=$2
mkdir -p logs/queue runs/llama_analysis
TPY=/ssd_scratch/gr/lma/venv-train/bin/python
LLAMA=llama3.1:8b-instruct-q8_0
LORA="lora:models/det-qwen2.5-1.5b-instruct-s{seed}"
EVAL="--scenarios data/eval/scenarios_v1.json --patients data/eval/patients_v1.json --policy data/policy/clinic_policy_v1.json"

step() {  # step <name> <command...>
  local name=$1; shift
  if [ -f "logs/queue/$name.done" ]; then echo "skip $name"; return 0; fi
  echo "=== $name start $(date)"
  if "$@" > "logs/queue/$name.log" 2>&1; then touch "logs/queue/$name.done"; echo "=== $name done $(date)"
  else echo "=== $name FAILED $(date) (see logs/queue/$name.log)"; return 1; fi
}
setup_ok() { grep -q SETUP_OK "logs/setup-$1.log" 2>/dev/null; }

run() {  # run <job> <conditions>
  local j=$1 c=$2
  while ! setup_ok "$j"; do sleep 60; done
  source "logs/hold-$j.env"
  srun --jobid="$j" --overlap -n 1 -c 6 --mem=12G --gres=none \
    env CUDA_VISIBLE_DEVICES= HF_HOME=/ssd_scratch/gr/lma/hf HF_HUB_OFFLINE=1 \
    $TPY scripts/run_llm.py --conditions "$c" --seeds 0 --phrasings direct,indirect \
    --detector "$LORA" $EVAL --base-urls "$OLLAMA_URLS" --model "$LLAMA" --workers 3 --out runs/llm_llama
}

echo "queue_llama start $(date) a=$A b=$B"
( step llama_a run "$A" plain,safety,plain_label; echo "branch a exit $? $(date)" ) &
( step llama_b run "$B" recheck,recheck_v2; echo "branch b exit $? $(date)" ) &
wait

if [ -f logs/queue/llama_a.done ] && [ -f logs/queue/llama_b.done ]; then
  PY="srun --jobid=$A --overlap -n 1 -c 6 --mem=12G --gres=none .venv/bin/python"
  R=runs/llama_analysis
  step llama_regrade $PY scripts/regrade_check.py --runs runs/llm_llama
  step llama_summary $PY scripts/summarize_runs.py --runs runs/llm_llama --out $R/llama_v1.md
  step llama_extra $PY scripts/extra_facts.py --runs runs/llm_llama --out $R/llama_extra_facts.md
  step llama_failures $PY scripts/failure_breakdown.py --runs runs/llm_llama --out $R/llama_failure_breakdown.md
  scancel "$A" "$B"
  touch logs/queue/llama.done
fi
echo "queue_llama finished $(date)"
