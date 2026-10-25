"""LoRA-tuned Qwen2.5 classifier (trained by scripts/train_detector.py).

Needs torch, transformers and peft (the `train` extra). Runs on GPU if one is
visible, else CPU (slow but fine for a few hundred messages).
"""

from __future__ import annotations

import json
from pathlib import Path


class LoraDetector:
    def __init__(self, adapter_dir: str, device: str | None = None):
        import torch
        from peft import PeftConfig, PeftModel
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        d = Path(adapter_dir)
        meta = json.loads((d / "metrics.json").read_text())
        self.labels = meta["labels"]
        self.name = f"lora[{Path(meta['base']).name}/s{meta['seed']}]"
        cfg = PeftConfig.from_pretrained(d)
        self.tok = AutoTokenizer.from_pretrained(d)
        base = AutoModelForSequenceClassification.from_pretrained(cfg.base_model_name_or_path,
                                                                  num_labels=len(self.labels))
        base.config.pad_token_id = self.tok.pad_token_id
        self.model = PeftModel.from_pretrained(base, d).eval()
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        if self.device == "cuda":
            self.model.half()
        self._torch = torch

    def predict(self, text: str) -> tuple[str, float]:
        return self.predict_batch([text])[0]

    def predict_batch(self, texts: list[str]) -> list[tuple[str, float]]:
        torch = self._torch
        enc = self.tok(texts, padding=True, truncation=True, max_length=128, return_tensors="pt").to(self.device)
        with torch.no_grad():
            probs = torch.softmax(self.model(**enc).logits.float(), -1)
        out = []
        for row in probs:
            i = int(row.argmax())
            out.append((self.labels[i], float(row[i])))
        return out
