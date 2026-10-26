#!/usr/bin/env bash
# The experiment queue for eval set v1. Run on the LOGIN node with nohup:
#   nohup bash cluster/queue_main.sh <hold_jobid> >> logs/queue.log 2>&1 &
# Each step writes logs/queue/<step>.done when it finishes; re-running the
# queue skips finished steps and run_llm.py resumes half-finished ones.
#
# Layout (env overrides):
#   URLS     Ollama servers to use (default: all servers of the holder)
#   DET_GPU  GPU index for the LoRA detector; empty (default) = run it on CPU.
#            A 1.5B fp16 detector does not fit next to an Ollama q8 7B model
#            on one 11 GB card, so either give it its own GPU or use CPU.
#   C, M     CPUs / memory per step (default 16 / 48G)
# If the holder job disappears, the queue stops instead of failing every step.
set -uo pipefail
cd "$(dirname "$0")/.."
JOB=$1
source "logs/hold-$JOB.env"
mkdir -p logs/queue
URLS=${URLS:-$OLLAMA_URLS}
NSRV=$(echo "$URLS" | tr ',' '\n' | wc -l)
W=${WORKERS:-$(( NSRV * 2 ))}
TPY=/ssd_scratch/gr/lma/venv-train/bin/python
LORA="lora:models/det-qwen2.5-1.5b-instruct-s{seed}"
EVAL="--scenarios data/eval/scenarios_v1.json --patients data/eval/patients_v1.json --policy data/policy/clinic_policy_v1.json"
COMMON="$EVAL --base-urls $URLS --model $MODEL --workers $W"
if [ -n "${DET_GPU:-}" ]; then
  DEV="--gres=gpu:4"; DETENV="env CUDA_VISIBLE_DEVICES=$DET_GPU HF_HOME=/ssd_scratch/gr/lma/hf"
else
  DEV="--gres=none"; DETENV="env CUDA_VISIBLE_DEVICES= HF_HOME=/ssd_scratch/gr/lma/hf"
fi

step() {  # step <name> <command...>
  local name=$1; shift
  if [ -f "logs/queue/$name.done" ]; then echo "skip $name"; return 0; fi
  if ! squeue -j "$JOB" -h -t R | grep -q .; then echo "holder $JOB is not running; stopping $(date)"; exit 1; fi
  echo "=== $name start $(date)"
  if "$@" > "logs/queue/$name.log" 2>&1; then
    touch "logs/queue/$name.done"; echo "=== $name done $(date)"
  else
    echo "=== $name FAILED $(date) (see logs/queue/$name.log)"
  fi
}

ov() {  # run a command inside the holder (detector on DET_GPU or CPU)
  srun --jobid="$JOB" --overlap -n 1 -c "${C:-16}" --mem="${M:-48G}" $DEV $DETENV "$@"
}

# A. detector comparison on eval text
DETS="keyword,tfidf"
for d in models/det-*; do DETS="$DETS,lora:$d"; done
step detectors ov $TPY scripts/eval_detectors.py --detectors "$DETS,prompted" --base-urls "$URLS" --model "$MODEL" --out runs/detector_eval

# B. scripted baselines with the same LoRA detector seeds as RECHECK
step scripted ov $TPY scripts/run_scripted.py --detector "$LORA" --seeds 0,1,2 --out runs/scripted_main
step scripted_faults ov $TPY scripts/run_scripted.py --detector "$LORA" --seeds 0 --phrasings direct \
  --faults cancel_fails_once,book_lost_response,slot_taken --controllers dsc --out runs/scripted_faults

# C. main LLM conditions (3 seeds, both phrasings). Ordered by priority for the
#    confirmatory tests: RECHECK and Hybrid first, then the rest (resume fills
#    any episodes dropped earlier).
step llm_main_recheck ov $TPY scripts/run_llm.py --conditions recheck,hybrid --seeds 0,1,2 \
  --phrasings direct,indirect --detector "$LORA" $COMMON --out runs/llm_main
step llm_main_rest ov $TPY scripts/run_llm.py --conditions safety,plain_label,plain --seeds 0,1,2 \
  --phrasings direct,indirect --detector "$LORA" $COMMON --out runs/llm_main

# D. ablations: seed 0, direct phrasing (proposal: one seed for ablations).
#    no_ledger and single_pass are confirmatory (H2c), so they go first.
step llm_ablate_conf ov $TPY scripts/run_llm.py --conditions recheck_no_ledger,recheck_single_pass \
  --seeds 0 --phrasings direct --detector "$LORA" $COMMON --out runs/llm_ablate
step llm_ablate ov $TPY scripts/run_llm.py --conditions recheck_no_detector,recheck_detector_tool,recheck_no_retrieval,recheck_full_record,recheck_no_readback \
  --seeds 0 --phrasings direct --detector "$LORA" $COMMON --out runs/llm_ablate

# E. tool faults (seed 0, direct)
step llm_faults ov $TPY scripts/run_llm.py --conditions plain,recheck,hybrid,recheck_no_readback --seeds 0 --phrasings direct \
  --faults cancel_fails_once,book_lost_response,slot_taken --detector "$LORA" $COMMON --out runs/llm_faults

echo "queue finished $(date)"
