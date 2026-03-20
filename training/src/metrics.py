from __future__ import annotations

from typing import Dict

import torch


def hit_rate_at_k(scores: torch.Tensor, labels: torch.Tensor, k: int) -> float:
    topk = torch.topk(scores, k=k, dim=1).indices
    hits = labels.gather(1, topk).sum(dim=1).gt(0).float()
    return hits.mean().item()


def ndcg_at_k(scores: torch.Tensor, labels: torch.Tensor, k: int) -> float:
    topk = torch.topk(scores, k=k, dim=1).indices
    gains = labels.gather(1, topk).float()
    discounts = 1.0 / torch.log2(torch.arange(k, device=scores.device).float() + 2.0)
    return (gains * discounts).sum(dim=1).mean().item()


def mrr_at_k(scores: torch.Tensor, labels: torch.Tensor, k: int) -> float:
    topk = torch.topk(scores, k=k, dim=1).indices
    gains = labels.gather(1, topk).float()
    reciprocal = torch.zeros(scores.size(0), device=scores.device)
    for rank in range(k):
        reciprocal = torch.where(
            (reciprocal == 0) & (gains[:, rank] > 0),
            torch.tensor(1.0 / (rank + 1), device=scores.device),
            reciprocal,
        )
    return reciprocal.mean().item()


def summarize_metrics(scores: torch.Tensor, labels: torch.Tensor, k: int = 10) -> Dict[str, float]:
    return {
        f"hr@{k}": hit_rate_at_k(scores, labels, k),
        f"ndcg@{k}": ndcg_at_k(scores, labels, k),
        f"mrr@{k}": mrr_at_k(scores, labels, k),
    }
