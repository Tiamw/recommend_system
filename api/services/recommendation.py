from __future__ import annotations

import json

import numpy as np
import onnxruntime as ort

from api.config.settings import AppSettings


def pad_left(sequence: list[int], max_len: int) -> tuple[np.ndarray, np.ndarray]:
    """将用户观看序列左侧补零，保持与模型导出时的输入约定一致。"""
    trimmed = sequence[-max_len:]
    seq_len = np.array([len(trimmed)], dtype=np.int64)
    padded = np.array([[0] * (max_len - len(trimmed)) + trimmed], dtype=np.int64)
    return padded, seq_len


class RecommendationService:
    """封装模型与映射表，避免每次请求重复加载。"""

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings

        with (settings.mappings_dir / "item_id_mapping.json").open("r", encoding="utf-8") as handle:
            self.raw_to_model = json.load(handle)
        with (settings.mappings_dir / "reverse_item_id_mapping.json").open("r", encoding="utf-8") as handle:
            self.model_to_raw = json.load(handle)

        self.session = ort.InferenceSession(
            str(settings.onnx_path),
            providers=["CPUExecutionProvider"],
        )

    @property
    def is_ready(self) -> bool:
        return self.session is not None

    def recommend(self, raw_anime_history: list[int], top_k: int | None = None) -> list[int]:
        history = [
            self.raw_to_model[str(item)]
            for item in raw_anime_history
            if str(item) in self.raw_to_model
        ]
        if not history:
            raise ValueError("No valid anime ids were found in the request history.")

        item_seq, seq_len = pad_left(history, self.settings.max_seq_len)
        outputs = self.session.run(["scores"], {"item_seq": item_seq, "seq_len": seq_len})[0]
        scores = outputs[0]

        # 先屏蔽 padding 和用户已看过内容，避免推荐结果重复。
        scores[0] = -np.inf
        for seen_item_id in history:
            scores[seen_item_id] = -np.inf

        effective_top_k = top_k or self.settings.default_top_k
        effective_top_k = min(effective_top_k, scores.shape[0])
        top_indices = np.argsort(scores)[::-1][:effective_top_k]

        return [
            int(self.model_to_raw[str(index)])
            for index in top_indices
            if str(index) in self.model_to_raw
        ]
