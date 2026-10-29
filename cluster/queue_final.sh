#!/usr/bin/env bash
# Final stage, fully on the cluster (no laptop needed). Run on the LOGIN node:
#   nohup bash cluster/queue_final.sh <hold_job> <judge_job> >> logs/queue_final.log 2>&1 &
# hold_job  : the qwen holder (2 GPUs). Runs RECHECK v2 on eval v1 (3 seeds),
#             then turns its GPUs into judge servers and judges llm_faults + llm_v2.
# judge_job : a hold_node job started with MODEL=llama3.1:8b-instruct-q8_0,
#             PARALLEL=6, CTX=1536. Judges llm_main + llm_ablate.
# Then runs every analysis into runs/final_analysis/ (pulled by cluster/sync.sh pull).
# Steps leave logs/queue/<name>.done; re-running skips finished steps and every
# run/judge resumes.
set -uo pipefail
cd "$(dirname "$0")/.."
HOLD=$1; JUDGE=$2
mkdir -p logs/queue runs/final_analysis
TPY=/ssd_scratch/gr/lma/venv-train/bin/python
QWEN=qwen2.5:7b-instruct-q8_0
LLAMA=llama3.1:8b-instruct-q8_0
LORA="lora:models/det-qwen2.5-1.5b-instruct-s{seed}"
EVAL="--scenarios data/eval/scenarios_v1.json --patients data/eval/patients_v1.json --policy data/policy/clinic_policy_v1.json"

alive() { squeue -j "$1" -h -t R | grep -q .; }
step() {  # step <name> <command...>
  local name=$1; shift
  if [ -f "logs/queue/$name.done" ]; then echo "skip $name"; return 0; fi
  echo "=== $name start $(date)"
  if "$@" > "logs/queue/$name.log" 2>&1; then touch "logs/queue/$name.done"; echo "=== $name done $(date)"
  else echo "=== $name FAILED $(date) (see logs/queue/$name.log)"; return 1; fi
}
on() {  # on <job> <cmd...>: run a command inside a job (no GPU)
  local j=$1; shift
  srun --jobid="$j" --overlap -n 1 -c "${C:-4}" --mem="${M:-8G}" --gres=none "$@"
}
curl_in() { on "$1" curl -s -m 600 "${@:2}"; }

judge() {  # judge <job> <urls> <runs_dir> <label_sample>
  local j=$1 urls=$2 d=$3 n=$4
  C=2 M=6G on "$j" .venv/bin/python scripts/judge_runs.py --runs "$d" --base-urls "$urls" \
    --judge-model "$LLAMA" --workers 12 --label-sample "$n"
}

branch_hold() {
  # free GPU 0 from the earlier judge server, reload qwen on both holder servers
  for s in $(squeue -s -j "$HOLD" -h -o "%i %j" | awk '$2=="judge_server.sh"{print $1}'); do scancel "$s"; done
  sleep 10
  source "logs/hold-$HOLD.env"
  for p in 11434 11435; do
    curl_in "$HOLD" "http://127.0.0.1:$p/api/generate" -d "{\"model\":\"$QWEN\",\"prompt\":\"hi\",\"stream\":false,\"options\":{\"num_predict\":1}}" > /dev/null
  done
  step v2_eval srun --jobid="$HOLD" --overlap -n 1 -c 16 --mem=48G --gres=none \
    env CUDA_VISIBLE_DEVICES= HF_HOME=/ssd_scratch/gr/lma/hf HF_HUB_OFFLINE=1 \
    $TPY scripts/run_llm.py --conditions recheck_v2 --seeds 0,1,2 --phrasings direct,indirect \
    --detector "$LORA" $EVAL --base-urls "$OLLAMA_URLS" --model "$QWEN" --workers 4 --out runs/llm_v2 || return 1
  # turn both holder GPUs into judge servers
  for p in 11434 11435; do
    curl_in "$HOLD" "http://127.0.0.1:$p/api/generate" -d "{\"model\":\"$QWEN\",\"keep_alive\":0}" > /dev/null
  done
  sleep 10
  nohup srun --jobid="$HOLD" --overlap -n 1 -c 6 --mem=8G --gres=gpu:2 cluster/judge_server.sh 0 11436 > logs/ollama-judge-h0.log 2>&1 &
  nohup srun --jobid="$HOLD" --overlap -n 1 -c 6 --mem=8G --gres=gpu:2 cluster/judge_server.sh 1 11437 > logs/ollama-judge-h1.log 2>&1 &
  sleep 30
  local U=http://127.0.0.1:11436/v1,http://127.0.0.1:11437/v1
  step judge_faults judge "$HOLD" "$U" runs/llm_faults 0 || return 1
  step judge_v2 judge "$HOLD" "$U" runs/llm_v2 0 || return 1
}

branch_judge() {
  until [ -f "logs/hold-$JUDGE.env" ]; do alive "$JUDGE" || { echo "judge job gone"; return 1; }; sleep 60; done
  source "logs/hold-$JUDGE.env"
  step judge_main judge "$JUDGE" "$OLLAMA_URLS" runs/llm_main 60 || return 1
  step judge_ablate judge "$JUDGE" "$OLLAMA_URLS" runs/llm_ablate 0 || return 1
}

echo "queue_final start $(date) hold=$HOLD judge=$JUDGE"
branch_hold > logs/queue_final_hold.log 2>&1 &
PH=$!
branch_judge > logs/queue_final_judge.log 2>&1 &
PJ=$!
wait $PH; echo "hold branch exit $? $(date)"
wait $PJ; echo "judge branch exit $? $(date)"

# If one branch finished early, the other job's servers can help: judge any dir still incomplete.
for d in llm_main llm_ablate llm_faults llm_v2; do
  [ -f "logs/queue/judge_${d#llm_}.done" ] && continue
  for j in "$JUDGE" "$HOLD"; do
    if alive "$j"; then
      source "logs/hold-$j.env"; U=$OLLAMA_URLS
      [ "$j" = "$HOLD" ] && U=http://127.0.0.1:11436/v1,http://127.0.0.1:11437/v1
      n=0; [ "$d" = llm_main ] && n=60
      step "judge_${d#llm_}" judge "$j" "$U" "runs/$d" "$n" && break
    fi
  done
done

# Analysis (CPU only). Everything goes to runs/final_analysis/.
A=runs/final_analysis
J=$HOLD; alive "$J" || J=$JUDGE
RUNS="runs/llm_main runs/llm_v2 runs/llm_ablate runs/llm_faults runs/scripted_main runs/scripted_faults"
PY=.venv/bin/python
an() { if alive "$J"; then C=8 M=16G on "$J" "$@"; else "$@"; fi; }
step an_regrade an $PY scripts/regrade_check.py --runs $RUNS
step an_summary an $PY scripts/summarize_runs.py --runs $RUNS --out $A/final_v1.md
step an_gee an $PY scripts/timing_model.py --runs runs/llm_main --scenarios data/eval/scenarios_v1.json \
  --conditions plain,plain_label,safety,recheck,hybrid --metric unsafe_policy --out $A/final_timing_policy.md
step an_extra an $PY scripts/extra_facts.py --runs $RUNS --out $A/extra_facts_v1.md
step an_failures an $PY scripts/failure_breakdown.py --runs runs/llm_main runs/llm_v2 runs/scripted_main --out $A/failure_breakdown_v1.md
step an_advice an $PY scripts/summarize_advice.py --runs runs/llm_main runs/llm_v2 runs/llm_ablate runs/llm_faults \
  --out $A/advice_v1.md --label-sample runs/llm_main/advice_label_sample.jsonl --label-out $A/labelling
step an_tables an $PY scripts/make_report_tables.py --runs $RUNS --detectors results/detectors_eval_v1.json \
  --gee $A/final_timing_policy.md --out $A/tables
echo "queue_final finished $(date)"
touch logs/queue/final.done
