#!/usr/bin/env bash
# Extra Ollama server for the advice judge (llama3.1:8b q8_0 fits fully on one
# 11 GB card with this context and parallelism; larger settings spill to CPU
# and run ~10x slower).
#   srun --jobid=<job> --overlap -n 1 -c 8 --mem=8G --gres=gpu:<n> cluster/judge_server.sh <gpu_index> <port>
export OLLAMA_MODELS=/ssd_scratch/gr/lma/models OLLAMA_NOPRUNE=1 OLLAMA_CONTEXT_LENGTH=1536 OLLAMA_NUM_PARALLEL=6
export OLLAMA_KEEP_ALIVE=-1 CUDA_VISIBLE_DEVICES=$1 OLLAMA_HOST=127.0.0.1:$2
mkdir -p /ssd_scratch/gr/lma/tmp && export TMPDIR=/ssd_scratch/gr/lma/tmp  # /tmp can be full
exec /ssd_scratch/gr/lma/ollama/bin/ollama serve
