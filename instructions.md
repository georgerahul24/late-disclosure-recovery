# Instructions (standing rules for anyone working on this repo)

These come from the project owner (George). Follow them unless George says otherwise.

## Working rules

1. **Commit by feature.** Do not commit everything at once. Make one commit per piece of functionality or per fix, with a clear message.
2. **Push after every commit.** `git push` right after each `git commit`. Repo: https://github.com/georgerahul24/late-disclosure-recovery (private).
3. **No AI attribution in commits.** No "Co-Authored-By: Claude" or similar trailer.
4. **Keep the docs current.** After any meaningful change, update `handoff.md` (current state) and `todo.md` (tasks). Every folder has a `README.md`; update it when you change what is inside.
5. **Plain writing.** Prose documents use short, simple sentences, with no em dashes and no fancy words.
6. **Report results honestly.** If a run fails or a number looks wrong, say so. Never invent results.

## The compute cluster (IIIT Hyderabad "ada")

- **Login:** `ssh gr@ada-gw1.iiit.ac.in`. Key-based SSH works from George's laptop with no password prompt.
- **Scheduler:** SLURM. Account `research`, partition `u22`, QoS `medium`. The QoS limit per user is **40 CPUs, 4 GPUs, 125 GB RAM, 4 days**. This limit is shared with George's other jobs (for example `kings_server`), so check `squeue -u gr` first. George's rule: use **up to 36 CPUs and 4 GPUs**.
- **Nodes:** use **gnode045 to gnode090**; they have the better GPUs. Every node has 40 CPUs, about 125 GB RAM and up to 4x **RTX 2080 Ti (11 GB, Turing, sm_75)**. Turing has **no bf16**, so use fp16 or quantised models.
- **Finding free GPUs: use `pestat`** (George's tip). `pestat -p u22 --no-color --gib | grep -E "gnode0(4[5-9]|[5-8][0-9]|90)"` lists CPUs used/total, free memory and GPUs used/total for each node. Pick a node with free GPUs *and* free CPUs. The older manual way is:
- **Finding free GPUs (manual):**
  ```bash
  for n in $(sinfo -p u22 -N -h -o "%N %t" | awk '$1>="gnode045" && $1<="gnode090" && ($2=="idle"||$2=="mix"){print $1}'); do
    echo "$n $(scontrol show node $n | grep -o 'AllocTRES=[^ ]*')"; done
  ```
  A node is good if its `gres/gpu` count is below the node's total and it has enough free CPUs and RAM.
- **Disk:**
  - Home `/home2/gr` is 50 GB and **nearly full** (about 4 GB free). Keep only code and small results there.
  - Each node has a local `/ssd_scratch`. Use `/ssd_scratch/gr/...` for models and the Ollama install. **Free space differs by node**: gnode079 was full, while gnode048/056/085/090 had hundreds of GB. Check with `df -h /ssd_scratch` inside a job.
  - `/data3/u22` is read-only.
- **Internet:** compute nodes can reach GitHub and the Ollama registry, so models can be pulled inside a job.
- **Python:** `~/.local/bin/uv` exists. Set `UV_CACHE_DIR=~/uv_cache` to reuse the existing cache and save home space.
- **There is no GitHub access from the cluster** for the private repo. Code moves by rsync (below).

## Serving the LLM: Ollama, not vLLM

- **Choice:** **Ollama**, one server per GPU.
- **Why not vLLM:** the GPUs are 2080 Ti. vLLM's current engine needs newer GPUs for its fast attention paths and bf16, and Qwen2.5-7B in fp16 (15 GB) would not fit on one 11 GB card. That would force tensor parallelism across 2 cards with PCIe only.
- **Why Ollama:** a quantised 7B fits on one card, and Ollama has an OpenAI-compatible endpoint with tool calling for Qwen2.5.
- **Model:** `qwen2.5:7b-instruct-q8_0` (about 8 GB). This is 8-bit, not the bf16 the proposal names. **Report this in the paper.**
- **Fallback:** the proposal allows `qwen2.5:14b` if the 7B cannot call tools reliably. A 14B Q4 (about 9 GB) fits on one card at a short context.
- **Settings in the job:**
  - `OLLAMA_CONTEXT_LENGTH=8192`. The Ollama default is too small for the tool schemas plus conversation.
  - `OLLAMA_NUM_PARALLEL=2` per server.
  - `OLLAMA_KEEP_ALIVE=-1`.
- **Ollama binary:** `~/ollama` is George's Ollama bundle (a zstd tar, version 0.21.2). The job unpacks it into `/ssd_scratch/gr/lma/ollama` on the node. Unpacking needs `zstd`, which the compute nodes have and the login node does not. A pinned GitHub download (`OLLAMA_VERSION`) is only a fallback, and it is slow (about 2 MB/s).

## How to run things

From the laptop, in the repo root:
```bash
cluster/sync.sh push                     # copy code + data to ~/lma on the cluster
ssh gr@ada-gw1.iiit.ac.in 'cd lma && bash cluster/setup_env.sh'   # first time only
```
On the cluster (`cd ~/lma`):
```bash
# scripted pilot (CPU only, seconds)
.venv/bin/python scripts/run_pilot.py

# LLM conditions: 4 GPUs on one node, args go to scripts/run_llm.py
sbatch -w gnode090 cluster/llm_job.sbatch --conditions plain,safety,plain_label,recheck,hybrid --seeds 0,1,2 --out runs/llm_dev
MODEL=qwen2.5:14b sbatch -w gnode048 cluster/llm_job.sbatch ...   # other model
squeue -u gr ; tail -f logs/lma-llm-<jobid>.out
```
Back on the laptop:
```bash
cluster/sync.sh pull        # brings runs/ and logs/ back
```
`runs/` is git-ignored. Copy the final `summary.md` files you want to keep into `results/` and commit them.

`scripts/run_llm.py` can be resumed. If a job dies, submit it again with the same `--out` and it skips finished episodes.
