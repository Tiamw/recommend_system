from __future__ import annotations

import argparse
import json

from common import load_config, resolve_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect the popularity baseline.")
    parser.add_argument("--config", default="training/configs/default.yaml")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    baseline_path = resolve_path(config, "mappings_dir") / "popularity_baseline.json"
    with baseline_path.open("r", encoding="utf-8") as handle:
        baseline = json.load(handle)
    print(json.dumps(baseline, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
