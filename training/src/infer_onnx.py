from __future__ import annotations

import argparse
import json

import numpy as np
import onnxruntime as ort

from common import load_config, resolve_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run ONNX inference for a sample request.")
    parser.add_argument("--config", default="training/configs/default.yaml")
    parser.add_argument("--input-json", required=True)
    return parser.parse_args()


def pad_left(sequence, max_len):
    trimmed = sequence[-max_len:]
    seq_len = np.array([len(trimmed)], dtype=np.int64)
    padded = np.array([[0] * (max_len - len(trimmed)) + trimmed], dtype=np.int64)
    return padded, seq_len


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    with open(args.input_json, "r", encoding="utf-8") as handle:
        request = json.load(handle)
    with (resolve_path(config, "mappings_dir") / "item_id_mapping.json").open("r", encoding="utf-8") as handle:
        raw_to_model = json.load(handle)
    with (resolve_path(config, "mappings_dir") / "reverse_item_id_mapping.json").open("r", encoding="utf-8") as handle:
        model_to_raw = json.load(handle)

    history = [raw_to_model[str(item)] for item in request["raw_anime_history"] if str(item) in raw_to_model]
    if not history:
        raise ValueError("No valid anime ids were found in the request history.")

    item_seq, seq_len = pad_left(history, config["data"]["max_seq_len"])
    session = ort.InferenceSession(str(resolve_path(config, "onnx_dir") / config["export"]["onnx_name"]), providers=["CPUExecutionProvider"])
    outputs = session.run(["scores"], {"item_seq": item_seq, "seq_len": seq_len})[0]

    scores = outputs[0]
    scores[0] = -np.inf
    for seen_item_id in history:
        scores[seen_item_id] = -np.inf
    top_k = request.get("top_k", config["export"]["top_k"])
    top_indices = np.argsort(scores)[::-1][:top_k]
    response = {
        "raw_anime_history": request["raw_anime_history"],
        "model_item_history": history,
        "top_k_model_item_ids": top_indices.tolist(),
        "top_k_raw_anime_ids": [int(model_to_raw[str(index)]) for index in top_indices],
        "top_k_scores": [float(scores[index]) for index in top_indices],
    }
    print(json.dumps(response, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
