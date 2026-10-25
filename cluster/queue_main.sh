#!/usr/bin/env bash
# The experiment queue for eval set v1. Run on the LOGIN node with nohup:
#   nohup bash cluster/queue_main.sh 39713 > logs/queue.log 2>&1 &
# Each step writes logs/queue/<step>.done when it finishes; re-running the
# queue skips finished steps and run_llm.py resumes half-finished ones.
# Layout while it runs: Ollama servers on GPUs 0-2 serve the LLM; GPU 3 runs
# the LoRA detectors (its Ollama model is unloaded).
set -uo pipefail
cd "$(dirname "$0")/.."
JOB=$1
source "logs/hold-$JOB.env"
mkdir -p logs/queue
U3="http://127.0.0.1:11434/v1,http://127.0.0.1:11435/v1,http://127.0.0.1:11436/v1"
TPY=/ssd_scratch/gr/lma/venv-train/bin/python
LORA="lora:models/det-qwen2.5-1.5b-instruct-s{seed}"
EVAL="--scenarios data/eval/scenarios_v1.json --patients data/eval/patients_v1.json --policy data/policy/clinic_policy_v1.json"
GPU3="env CUDA_VISIBLE_DEVICES=3 HF_HOME=/ssd_scratch/gr/lma/hf"

step() {  # step <name> <command...>
  local name=$1; shift
  if [ -f "logs/queue/$name.done" ]; then echo "skip $name"; return 0; fi
  echo "=== $name start $(date)"
  if "$@" > "logs/queue/$name.log" 2>&1; then
    touch "logs/queue/$name.done"; echo "=== $name done $(date)"
  else
    echo "=== $name FAILED $(date) (see logs/queue/$name.log)"
  fi
}

ov() {  # run a command inside the holder with GPU 3 visible
  srun --jobid="$JOB" --overlap -n 1 -c "${C:-6}" --mem="${M:-24G}" --gres=gpu:4 $GPU3 "$@"
}

# A. detector comparison on eval text (LoRA x6 on GPU 3, prompted 7B on servers 0-2)
DETS="keyword,tfidf"
for d in models/det-*; do DETS="$DETS,lora:$d"; done
step detectors ov $TPY scripts/eval_detectors.py --detectors "$DETS,prompted" --base-urls "$U3" --model "$MODEL" --out runs/detector_eval

# B. scripted baselines with the same LoRA detector seeds as RECHECK
step scripted ov $TPY scripts/run_scripted.py --detector "$LORA" --seeds 0,1,2 --out runs/scripted_main
step scripted_faults ov $TPY scripts/run_scripted.py --detector "$LORA" --seeds 0 --phrasings direct \
  --faults cancel_fails_once,book_lost_response,slot_taken --controllers dsc --out runs/scripted_faults

# C. LLM main conditions that need the detector (plain/safety run separately)
step llm_main_det ov $TPY scripts/run_llm.py --conditions plain_label,recheck,hybrid --seeds 0,1,2 \
  --phrasings direct,indirect --detector "$LORA" $EVAL --base-urls "$U3" --model "$MODEL" --workers 6 --out runs/llm_main

# D. ablations: seed 0, direct phrasing (proposal: one seed for ablations)
step llm_ablate ov $TPY scripts/run_llm.py --conditions recheck_no_detector,recheck_detector_tool,recheck_no_retrieval,recheck_full_record,recheck_no_ledger,recheck_no_readback,recheck_single_pass \
  --seeds 0 --phrasings direct --detector "$LORA" $EVAL --base-urls "$U3" --model "$MODEL" --workers 6 --out runs/llm_ablate

# E. tool faults (seed 0, direct)
step llm_faults ov $TPY scripts/run_llm.py --conditions plain,recheck,hybrid,recheck_no_readback --seeds 0 --phrasings direct \
  --faults cancel_fails_once,book_lost_response,slot_taken --detector "$LORA" $EVAL --base-urls "$U3" --model "$MODEL" \
  --workers 6 --out runs/llm_faults

echo "queue finished $(date)"
