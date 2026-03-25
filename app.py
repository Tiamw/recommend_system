from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Optional

import numpy as np
import onnxruntime as ort
import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


def load_config(config_path: str | Path) -> dict:
    with Path(config_path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def resolve_path(config: dict, key: str) -> Path:
    return Path(config["paths"][key])


def pad_left(sequence: List[int], max_len: int) -> tuple[np.ndarray, np.ndarray]:
    trimmed = sequence[-max_len:]
    seq_len = np.array([len(trimmed)], dtype=np.int64)
    padded = np.array([[0] * (max_len - len(trimmed)) + trimmed], dtype=np.int64)
    return padded, seq_len


class RecommendRequest(BaseModel):
    raw_anime_history: List[int] = Field(..., description="List of raw anime IDs.")
    top_k: Optional[int] = Field(None, description="Number of recommendations to return.")


class RecommendResponse(BaseModel):
    top_k_raw_anime_ids: List[int]


app = FastAPI(title="Mini-Anime-Rec API", version="0.1.0")

CONFIG_PATH = os.getenv("CONFIG_PATH", "training/configs/default.yaml")
config = load_config(CONFIG_PATH)

with (resolve_path(config, "mappings_dir") / "item_id_mapping.json").open("r", encoding="utf-8") as handle:
    RAW_TO_MODEL = json.load(handle)
with (resolve_path(config, "mappings_dir") / "reverse_item_id_mapping.json").open("r", encoding="utf-8") as handle:
    MODEL_TO_RAW = json.load(handle)

MAX_SEQ_LEN = int(config["data"]["max_seq_len"])
DEFAULT_TOP_K = int(config["export"]["top_k"])

session = ort.InferenceSession(
    str(resolve_path(config, "onnx_dir") / config["export"]["onnx_name"]),
    providers=["CPUExecutionProvider"],
)


@app.post("/recommend", response_model=RecommendResponse)
def recommend(request: RecommendRequest) -> RecommendResponse:
    history = [RAW_TO_MODEL[str(item)] for item in request.raw_anime_history if str(item) in RAW_TO_MODEL]
    if not history:
        raise HTTPException(status_code=400, detail="No valid anime ids were found in the request history.")

    item_seq, seq_len = pad_left(history, MAX_SEQ_LEN)
    outputs = session.run(["scores"], {"item_seq": item_seq, "seq_len": seq_len})[0]
    scores = outputs[0]

    scores[0] = -np.inf
    for seen_item_id in history:
        scores[seen_item_id] = -np.inf

    top_k = request.top_k or DEFAULT_TOP_K
    top_k = min(top_k, scores.shape[0])
    top_indices = np.argsort(scores)[::-1][:top_k]

    top_raw_ids = [int(MODEL_TO_RAW[str(index)]) for index in top_indices if str(index) in MODEL_TO_RAW]
    return RecommendResponse(top_k_raw_anime_ids=top_raw_ids)
