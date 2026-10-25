#!/usr/bin/env bash
# Build the GPU training env on NODE-LOCAL scratch (home quota is too small
# for torch). Run inside the holder:
#   srun --jobid=<hold> --overlap -n 1 -c 8 --mem=16G bash cluster/setup_train_env.sh
# Then use:  /ssd_scratch/gr/lma/venv-train/bin/python scripts/train_detector.py ...
# with HF_HOME=/ssd_scratch/gr/lma/hf
set -euo pipefail
cd "$(dirname "$0")/.."
SCR=${SCR:-/ssd_scratch/gr/lma}
export PATH="$HOME/.local/bin:$PATH"
export UV_CACHE_DIR=$SCR/uv-cache
V=$SCR/venv-train
uv venv --python 3.12 "$V"
# torch cu121 wheels support sm_75 (RTX 2080 Ti)
uv pip install --python "$V/bin/python" --index-url https://download.pytorch.org/whl/cu121 "torch==2.4.1"
uv pip install --python "$V/bin/python" "transformers==4.44.2" "peft==0.12.0" "accelerate==0.33.0" \
  "numpy<2" scikit-learn
uv pip install --python "$V/bin/python" -e . --no-deps
"$V/bin/python" -c "import torch, transformers, peft; print('torch', torch.__version__, 'cuda', torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else '-'); print('transformers', transformers.__version__, 'peft', peft.__version__)"
