from __future__ import annotations

import argparse
import csv
import json
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from common import ensure_dir, load_config, resolve_path, save_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preprocess the anime recommendation dataset.")
    parser.add_argument("--config", default="training/configs/default.yaml")
    return parser.parse_args()


def extract_raw_files(archive_zip: Path, raw_dir: Path) -> None:
    ensure_dir(raw_dir)
    with zipfile.ZipFile(archive_zip) as archive:
        for name in ("anime.csv", "rating.csv"):
            target = raw_dir / name
            if target.exists():
                continue
            archive.extract(name, path=raw_dir)


def read_anime_rows(anime_csv: Path) -> Tuple[List[Dict[str, str]], Dict[int, Dict[str, str]]]:
    rows: List[Dict[str, str]] = []
    anime_by_id: Dict[int, Dict[str, str]] = {}
    with anime_csv.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(row)
            anime_by_id[int(row["anime_id"])] = row
    return rows, anime_by_id


def iter_positive_interactions(ratings_csv: Path, positive_threshold: int) -> Iterable[Tuple[int, int, int, int]]:
    with ratings_csv.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for order_index, row in enumerate(reader):
            rating = int(row["rating"])
            if rating == -1 or rating < positive_threshold:
                continue
            yield int(row["user_id"]), int(row["anime_id"]), rating, order_index


def build_clean_interactions(
    ratings_csv: Path,
    positive_threshold: int,
    min_user_interactions: int,
    min_item_interactions: int,
) -> List[Dict[str, int]]:
    latest_pairs: Dict[Tuple[int, int], Tuple[int, int]] = {}
    user_counts = Counter()
    item_counts = Counter()

    for user_id, anime_id, rating, order_index in iter_positive_interactions(ratings_csv, positive_threshold):
        latest_pairs[(user_id, anime_id)] = (rating, order_index)

    for (user_id, anime_id), _ in latest_pairs.items():
        user_counts[user_id] += 1
        item_counts[anime_id] += 1

    filtered: List[Dict[str, int]] = []
    for (user_id, anime_id), (rating, order_index) in latest_pairs.items():
        if user_counts[user_id] < min_user_interactions:
            continue
        if item_counts[anime_id] < min_item_interactions:
            continue
        filtered.append(
            {
                "user_id": user_id,
                "anime_id": anime_id,
                "rating": rating,
                "order_index": order_index,
            }
        )

    filtered.sort(key=lambda row: (row["user_id"], row["order_index"]))
    return filtered


def write_csv(path: Path, fieldnames: List[str], rows: Iterable[Dict[str, object]]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def build_sequences(
    interactions: List[Dict[str, int]],
) -> Tuple[Dict[int, List[int]], Dict[int, int], Dict[int, int], Dict[int, int]]:
    user_sequences_raw: Dict[int, List[int]] = defaultdict(list)
    unique_items = set()
    for row in interactions:
        user_sequences_raw[row["user_id"]].append(row["anime_id"])
        unique_items.add(row["anime_id"])

    user_id_mapping = {raw_user_id: idx + 1 for idx, raw_user_id in enumerate(sorted(user_sequences_raw))}
    item_id_mapping = {raw_item_id: idx + 1 for idx, raw_item_id in enumerate(sorted(unique_items))}
    reverse_item_id_mapping = {model_id: raw_id for raw_id, model_id in item_id_mapping.items()}
    user_sequences = {
        user_id_mapping[raw_user_id]: [item_id_mapping[item_id] for item_id in sequence]
        for raw_user_id, sequence in user_sequences_raw.items()
    }
    return user_sequences, user_id_mapping, item_id_mapping, reverse_item_id_mapping


def split_sequences(user_sequences: Dict[int, List[int]]) -> Dict[str, Dict[str, object]]:
    splits: Dict[str, Dict[str, object]] = {}
    for model_user_id, sequence in user_sequences.items():
        if len(sequence) < 3:
            continue
        splits[str(model_user_id)] = {
            "train": sequence[:-2],
            "val_target": sequence[-2],
            "test_target": sequence[-1],
            "full_sequence": sequence,
        }
    return splits


def compute_popularity(interactions: List[Dict[str, int]], item_id_mapping: Dict[int, int], top_k: int) -> Dict[str, object]:
    counts = Counter()
    for row in interactions:
        counts[item_id_mapping[row["anime_id"]]] += 1
    most_common = counts.most_common(top_k)
    return {
        "top_k": top_k,
        "popular_model_item_ids": [item_id for item_id, _ in most_common],
        "popular_counts": {str(item_id): count for item_id, count in most_common},
    }


def write_jsonl(path: Path, rows: Iterable[Dict[str, object]]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    args = parse_args()
    config = load_config(args.config)

    archive_zip = resolve_path(config, "archive_zip")
    raw_dir = resolve_path(config, "raw_dir")
    processed_dir = resolve_path(config, "processed_dir")
    mappings_dir = resolve_path(config, "mappings_dir")
    metrics_dir = resolve_path(config, "metrics_dir")

    extract_raw_files(archive_zip, raw_dir)

    anime_rows, anime_by_id = read_anime_rows(raw_dir / "anime.csv")
    interactions = build_clean_interactions(
        ratings_csv=raw_dir / "rating.csv",
        positive_threshold=config["data"]["positive_rating_threshold"],
        min_user_interactions=config["data"]["min_user_interactions"],
        min_item_interactions=config["data"]["min_item_interactions"],
    )
    user_sequences, user_id_mapping, item_id_mapping, reverse_item_id_mapping = build_sequences(interactions)
    splits = split_sequences(user_sequences)
    popularity = compute_popularity(interactions, item_id_mapping, config["data"]["popularity_top_k"])

    cleaned_anime_rows = [row for row in anime_rows if int(row["anime_id"]) in item_id_mapping]
    interaction_rows_for_csv = [
        {
            "raw_user_id": row["user_id"],
            "raw_anime_id": row["anime_id"],
            "model_user_id": user_id_mapping[row["user_id"]],
            "model_item_id": item_id_mapping[row["anime_id"]],
            "rating": row["rating"],
            "order_index": row["order_index"],
        }
        for row in interactions
    ]

    write_csv(processed_dir / "anime_clean.csv", ["anime_id", "name", "genre", "type", "episodes", "rating", "members"], cleaned_anime_rows)
    write_csv(
        processed_dir / "interactions_clean.csv",
        ["raw_user_id", "raw_anime_id", "model_user_id", "model_item_id", "rating", "order_index"],
        interaction_rows_for_csv,
    )
    write_jsonl(
        processed_dir / "user_sequences.jsonl",
        (
            {
                "model_user_id": model_user_id,
                "sequence": split_info["full_sequence"],
                "val_target": split_info["val_target"],
                "test_target": split_info["test_target"],
            }
            for model_user_id, split_info in splits.items()
        ),
    )
    save_json(splits, processed_dir / "splits.json")
    save_json({str(k): v for k, v in user_id_mapping.items()}, mappings_dir / "user_id_mapping.json")
    save_json({str(k): v for k, v in item_id_mapping.items()}, mappings_dir / "item_id_mapping.json")
    save_json({str(k): v for k, v in reverse_item_id_mapping.items()}, mappings_dir / "reverse_item_id_mapping.json")
    save_json(popularity, mappings_dir / "popularity_baseline.json")

    stats = {
        "num_raw_anime": len(anime_rows),
        "num_filtered_anime": len(cleaned_anime_rows),
        "num_interactions": len(interactions),
        "num_users": len(user_sequences),
        "num_items": len(item_id_mapping),
        "num_sequences_with_split": len(splits),
        "positive_rating_threshold": config["data"]["positive_rating_threshold"],
        "min_user_interactions": config["data"]["min_user_interactions"],
        "min_item_interactions": config["data"]["min_item_interactions"],
    }
    save_json(stats, metrics_dir / "preprocess_stats.json")

    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f"Extracted anime metadata rows available for inference: {len(anime_by_id)}")


if __name__ == "__main__":
    main()
