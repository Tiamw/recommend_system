from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_default_config_exists() -> None:
    assert (ROOT / "training" / "configs" / "default.yaml").exists()


def test_processed_outputs_if_present_are_consistent() -> None:
    processed_dir = ROOT / "training" / "data" / "processed"
    mappings_dir = ROOT / "training" / "artifacts" / "mappings"
    splits_path = processed_dir / "splits.json"
    item_mapping_path = mappings_dir / "item_id_mapping.json"
    reverse_mapping_path = mappings_dir / "reverse_item_id_mapping.json"

    if not splits_path.exists():
        return

    with splits_path.open("r", encoding="utf-8") as handle:
        splits = json.load(handle)
    with item_mapping_path.open("r", encoding="utf-8") as handle:
        item_mapping = json.load(handle)
    with reverse_mapping_path.open("r", encoding="utf-8") as handle:
        reverse_mapping = json.load(handle)

    assert "0" not in reverse_mapping
    assert all(int(value) > 0 for value in item_mapping.values())
    for split in splits.values():
        assert len(split["full_sequence"]) >= 3
        assert split["val_target"] == split["full_sequence"][-2]
        assert split["test_target"] == split["full_sequence"][-1]


def test_interactions_csv_header_if_present() -> None:
    interactions_csv = ROOT / "training" / "data" / "processed" / "interactions_clean.csv"
    if not interactions_csv.exists():
        return

    with interactions_csv.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
    assert header == ["raw_user_id", "raw_anime_id", "model_user_id", "model_item_id", "rating", "order_index"]
