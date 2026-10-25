"""Train the LoRA symptom detector (proposal section 5).

    python scripts/train_detector.py --base Qwen/Qwen2.5-1.5B-Instruct --seed 0 \
        --out models/detector-1.5b-s0

Data: seeds_v1 + paraphrases_v1, each placed in pre- and post-booking carrier
messages, plus benign carriers (recheck.detectors.augment_with_carriers).
Split: 85/15 train/dev grouped by seed_id (paraphrases never cross the split).
Model: <base> + 5-way classification head, LoRA r=16, alpha=32, dropout 0.05
on q/k/v/o attention projections; head trained in full. lr 2e-4, 3 epochs,
batch 16, fp16 (RTX 2080 Ti has no bf16). Model selection: best dev macro-F1
over epochs. Writes adapter + head + label map + metrics.json to --out.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from recheck.detectors.base import augment_with_carriers  # noqa: E402
from recheck.rules import FAMILIES  # noqa: E402


def grouped_split(rows: list[dict], dev_frac: float, seed: int):
    groups = sorted({r["seed_id"] for r in rows})
    rng = random.Random(seed)
    rng.shuffle(groups)
    # stratify by label so every class appears in dev
    by_label: dict[str, list[str]] = {}
    lab = {r["seed_id"]: r["label"] for r in rows}
    for g in groups:
        by_label.setdefault(lab[g], []).append(g)
    dev = set()
    for gs in by_label.values():
        dev |= set(gs[:max(1, round(len(gs) * dev_frac))])
    return [r for r in rows if r["seed_id"] not in dev], [r for r in rows if r["seed_id"] in dev]


def macro_f1(y, p, labels):
    f1s = []
    for c in labels:
        tp = sum(1 for a, b in zip(y, p) if a == c and b == c)
        fp = sum(1 for a, b in zip(y, p) if a != c and b == c)
        fn = sum(1 for a, b in zip(y, p) if a == c and b != c)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1s.append(2 * prec * rec / (prec + rec) if prec + rec else 0.0)
    return sum(f1s) / len(f1s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="Qwen/Qwen2.5-1.5B-Instruct")
    ap.add_argument("--seeds", default=str(ROOT / "data/detector/seeds_v1.json"))
    ap.add_argument("--paraphrases", default=str(ROOT / "data/detector/paraphrases_v1.json"))
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--bs", type=int, default=16)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--max-len", type=int, default=96)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    import numpy as np
    import torch
    from peft import LoraConfig, get_peft_model
    from torch.utils.data import DataLoader
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup

    torch.manual_seed(args.seed)
    random.seed(args.seed)
    np.random.seed(args.seed)
    seeds = json.loads(Path(args.seeds).read_text())
    paras = json.loads(Path(args.paraphrases).read_text()) if Path(args.paraphrases).exists() else []
    base_rows = seeds + [{"seed_id": p["seed_id"], "label": p["label"], "text": p["text"]} for p in paras]
    train_base, dev_base = grouped_split(base_rows, 0.15, seed=1234)  # same split for every run seed
    train = augment_with_carriers(train_base)
    dev = augment_with_carriers(dev_base)
    labels = list(FAMILIES)
    l2i = {l: i for i, l in enumerate(labels)}

    tok = AutoTokenizer.from_pretrained(args.base)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForSequenceClassification.from_pretrained(args.base, num_labels=len(labels),
                                                               torch_dtype=torch.float32)
    model.config.pad_token_id = tok.pad_token_id
    cfg = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
                     task_type="SEQ_CLS", modules_to_save=["score"])
    model = get_peft_model(model, cfg)
    model.print_trainable_parameters()
    dev_ = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(dev_)

    def collate(batch):
        enc = tok([b["text"] for b in batch], padding=True, truncation=True, max_length=args.max_len,
                  return_tensors="pt")
        enc["labels"] = torch.tensor([l2i[b["label"]] for b in batch])
        return enc

    tl = DataLoader(train, batch_size=args.bs, shuffle=True, collate_fn=collate,
                    generator=torch.Generator().manual_seed(args.seed))
    dl = DataLoader(dev, batch_size=64, shuffle=False, collate_fn=collate)
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=args.lr)
    sched = get_linear_schedule_with_warmup(opt, int(0.06 * len(tl) * args.epochs), len(tl) * args.epochs)
    scaler = torch.cuda.amp.GradScaler(enabled=dev_ == "cuda")

    def evaluate():
        model.eval()
        ys, ps = [], []
        with torch.no_grad():
            for b in dl:
                b = {k: v.to(dev_) for k, v in b.items()}
                with torch.autocast(dev_, dtype=torch.float16, enabled=dev_ == "cuda"):
                    logits = model(**{k: v for k, v in b.items() if k != "labels"}).logits
                ps += logits.argmax(-1).tolist()
                ys += b["labels"].tolist()
        model.train()
        y = [labels[i] for i in ys]
        p = [labels[i] for i in ps]
        return macro_f1(y, p, labels), sum(a == b for a, b in zip(y, p)) / len(y)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    best, hist = -1.0, []
    model.train()
    for ep in range(args.epochs):
        tot = 0.0
        for b in tl:
            b = {k: v.to(dev_) for k, v in b.items()}
            with torch.autocast(dev_, dtype=torch.float16, enabled=dev_ == "cuda"):
                loss = model(**b).loss
            scaler.scale(loss).backward()
            scaler.unscale_(opt)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(opt)
            scaler.update()
            opt.zero_grad()
            sched.step()
            tot += loss.item()
        f1, acc = evaluate()
        hist.append({"epoch": ep + 1, "train_loss": tot / len(tl), "dev_macro_f1": f1, "dev_acc": acc})
        print(hist[-1], flush=True)
        if f1 > best:
            best = f1
            model.save_pretrained(out)
            tok.save_pretrained(out)
    meta = {"base": args.base, "labels": labels, "seed": args.seed, "n_train": len(train), "n_dev": len(dev),
            "n_train_groups": len({r['seed_id'] for r in train_base}), "n_dev_groups": len({r['seed_id'] for r in dev_base}),
            "best_dev_macro_f1": best, "history": hist,
            "hparams": {"r": 16, "alpha": 32, "dropout": 0.05, "lr": args.lr, "epochs": args.epochs, "bs": args.bs,
                        "dtype": "fp16 autocast", "max_len": args.max_len}}
    (out / "metrics.json").write_text(json.dumps(meta, indent=1))
    print(json.dumps({k: meta[k] for k in ("best_dev_macro_f1", "n_train", "n_dev")}))


if __name__ == "__main__":
    main()
