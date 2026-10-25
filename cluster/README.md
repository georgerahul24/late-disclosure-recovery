# cluster/ (running on the ada SLURM cluster)

The full how-to is in `../instructions.md`. This is the short version.

| File | Run where | What |
|---|---|---|
| `sync.sh push` / `sync.sh pull` | laptop, repo root | rsync code to `~/lma` on the cluster, or pull back `runs/` and `logs/`. The cluster cannot clone the private repo. |
| `setup_env.sh` | cluster login node, once | Makes `~/lma/.venv` (Python 3.12, scikit-learn, pytest) with uv, reusing `~/uv_cache`, then runs the tests. |
| `llm_job.sbatch` | `sbatch` from `~/lma` | Starts one Ollama server per allocated GPU on node-local `/ssd_scratch/gr/lma`, pulls the model once, warms the servers, then runs `scripts/run_llm.py` with any arguments you pass. Env overrides: `MODEL`, `OLLAMA_VERSION`, `PARALLEL`, `CTX`, `WORKERS`. |

Example:
```bash
sbatch -w gnode090 cluster/llm_job.sbatch --conditions plain,recheck --seeds 0 --out runs/llm_dev
sbatch -w gnode048 --gres=gpu:3 -c 12 --mem=48G cluster/llm_job.sbatch ...   # override resources
```

## Lessons learned

- **`sbatch --test-only` lies here.** It reported a start time 40 hours away for every request, while real jobs started within seconds to minutes. Submit for real and watch `squeue`.
- **Check `/ssd_scratch` space** on the node first. Some nodes are full; for example gnode079 had 3 GB free.
- **`~/ollama` is the Ollama bundle** (a zstd tar). The login node has no `zstd`, so unpack it on a compute node. The scripts do this.
- **The GPUs are 2080 Ti.** That means no bf16, and 7B fp16 does not fit on one card. Use q8_0 or Q4 via Ollama.
