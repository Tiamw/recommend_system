import argparse
import json
import math
from pathlib import Path

from common import load_config, resolve_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate popularity baseline.")
    parser.add_argument("--config", default="training/configs/default.yaml")
    parser.add_argument("--mode", choices=["val", "test"], default="val")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    splits_path = resolve_path(config, "processed_dir") / "splits.json"
    popularity_path = resolve_path(config, "mappings_dir") / "popularity_baseline.json"

    with Path(splits_path).open("r", encoding="utf-8") as handle:
        splits = json.load(handle)
    with Path(popularity_path).open("r", encoding="utf-8") as handle:
        popularity = json.load(handle)

    candidates = popularity["popular_model_item_ids"]
    top_k = 10

    hit_sum = 0.0
    ndcg_sum = 0.0
    mrr_sum = 0.0
    total = 0

    for split in splits.values():
        target = split["val_target"] if args.mode == "val" else split["test_target"]
        total += 1
        if target in candidates[:top_k]:
            hit_sum += 1.0
            rank = candidates.index(target) + 1
            ndcg_sum += 1.0 / math.log2(rank + 1)
            mrr_sum += 1.0 / rank

    hr = hit_sum / total if total else 0.0
    ndcg = ndcg_sum / total if total else 0.0
    mrr = mrr_sum / total if total else 0.0

    print(json.dumps({
        "mode": args.mode,
        "users": total,
        "hr@10": hr,
        "ndcg@10": ndcg,
        "mrr@10": mrr,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
