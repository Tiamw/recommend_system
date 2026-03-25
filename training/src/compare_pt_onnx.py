from __future__ import annotations

import argparse
import json

import numpy as np
import onnxruntime as ort
import torch

from common import load_config, resolve_path
from model import SASRecLite, TemperatureScaledHead


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare PyTorch and ONNX top-k outputs.")
    parser.add_argument("--config", default="training/configs/default.yaml")
    parser.add_argument("--input-json", required=True)
    parser.add_argument("--top-k", type=int, default=None)
    return parser.parse_args()


def pad_left(sequence: list[int], max_len: int) -> tuple[np.ndarray, np.ndarray]:
    trimmed = sequence[-max_len:]
    seq_len = np.array([len(trimmed)], dtype=np.int64)
    padded = np.array([[0] * (max_len - len(trimmed)) + trimmed], dtype=np.int64)
    return padded, seq_len


def build_history(raw_history: list[int], raw_to_model: dict) -> list[int]:
    return [raw_to_model[str(item)] for item in raw_history if str(item) in raw_to_model]


def mask_seen(scores: np.ndarray, history: list[int]) -> None:
    scores[0] = -np.inf
    for seen_item_id in history:
        scores[seen_item_id] = -np.inf


def top_k_indices(scores: np.ndarray, k: int) -> list[int]:
    k = min(k, scores.shape[0])
    return np.argsort(scores)[::-1][:k].tolist()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)

    with open(args.input_json, "r", encoding="utf-8") as handle:
        request = json.load(handle)
    with (resolve_path(config, "mappings_dir") / "item_id_mapping.json").open("r", encoding="utf-8") as handle:
        raw_to_model = json.load(handle)

    history = build_history(request["raw_anime_history"], raw_to_model)
    if not history:
        raise ValueError("No valid anime ids were found in the request history.")

    checkpoint_path = resolve_path(config, "checkpoints_dir") / config["export"]["checkpoint_name"]
    checkpoint = torch.load(checkpoint_path, map_location="cpu")

    model = SASRecLite(
        item_vocab_size=checkpoint["item_vocab_size"],
        max_seq_len=config["data"]["max_seq_len"],
        embedding_dim=config["training"]["embedding_dim"],
        num_blocks=config["training"]["num_blocks"],
        num_heads=config["training"]["num_heads"],
        dropout=config["training"]["dropout"],
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    model.use_inf_mask = False

    temperature_head = None
    if checkpoint.get("temperature_head_state_dict") is not None:
        temperature_head = TemperatureScaledHead()
        temperature_head.load_state_dict(checkpoint["temperature_head_state_dict"])
        temperature_head.eval()

    item_seq, seq_len = pad_left(history, config["data"]["max_seq_len"])
    item_seq_t = torch.tensor(item_seq, dtype=torch.long)
    seq_len_t = torch.tensor(seq_len, dtype=torch.long)

    with torch.no_grad():
        logits = model(item_seq_t, seq_len_t)
        if temperature_head is not None:
            logits = temperature_head(logits)
        pt_scores = logits.numpy()[0]
    mask_seen(pt_scores, history)

    session = ort.InferenceSession(
        str(resolve_path(config, "onnx_dir") / config["export"]["onnx_name"]),
        providers=["CPUExecutionProvider"],
    )
    onnx_scores = session.run(["scores"], {"item_seq": item_seq, "seq_len": seq_len})[0][0]
    mask_seen(onnx_scores, history)

    top_k = args.top_k or int(request.get("top_k", config["export"]["top_k"]))
    pt_top = top_k_indices(pt_scores, top_k)
    onnx_top = top_k_indices(onnx_scores, top_k)

    result = {
        "top_k": top_k,
        "pytorch_top_k_model_item_ids": pt_top,
        "onnx_top_k_model_item_ids": onnx_top,
        "match": pt_top == onnx_top,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
