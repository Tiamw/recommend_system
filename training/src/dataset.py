from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Dict, List, Sequence, Set, Tuple

import numpy as np
import torch
from torch.utils.data import Dataset


def pad_sequence(sequence: Sequence[int], max_len: int) -> Tuple[List[int], int]:
    trimmed = list(sequence[-max_len:])
    seq_len = len(trimmed)
    padded = [0] * (max_len - seq_len) + trimmed
    return padded, seq_len


class SequenceTrainDataset(Dataset):
    def __init__(self, splits_path: str | Path, max_seq_len: int, item_vocab_size: int, num_negative_samples: int = 1):
        with Path(splits_path).open("r", encoding="utf-8") as handle:
            self.splits: Dict[str, Dict[str, List[int] | int]] = json.load(handle)
        self.max_seq_len = max_seq_len
        self.item_vocab_size = item_vocab_size
        self.num_negative_samples = num_negative_samples
        self.user_seen_items: Dict[str, Set[int]] = {
            user_id: set(split["full_sequence"]) for user_id, split in self.splits.items()
        }
        self.samples: List[Tuple[str, List[int], int]] = []
        for user_id, split in self.splits.items():
            train_sequence: List[int] = split["train"]
            for end_idx in range(1, len(train_sequence)):
                history = train_sequence[:end_idx]
                target = train_sequence[end_idx]
                self.samples.append((user_id, history, target))

    def __len__(self) -> int:
        return len(self.samples)

    def _sample_negative(self, user_id: str) -> int:
        seen = self.user_seen_items[user_id]
        while True:
            candidate = random.randint(1, self.item_vocab_size - 1)
            if candidate not in seen:
                return candidate

    def __getitem__(self, index: int) -> Dict[str, torch.Tensor]:
        user_id, history, pos_target = self.samples[index]
        padded_history, seq_len = pad_sequence(history, self.max_seq_len)
        neg_target = self._sample_negative(user_id)
        return {
            "item_seq": torch.tensor(padded_history, dtype=torch.long),
            "seq_len": torch.tensor(seq_len, dtype=torch.long),
            "pos_item": torch.tensor(pos_target, dtype=torch.long),
            "neg_item": torch.tensor(neg_target, dtype=torch.long),
        }


class SequenceEvalDataset(Dataset):
    def __init__(self, splits_path: str | Path, max_seq_len: int, item_vocab_size: int, mode: str, sampled_candidates: int = 100):
        with Path(splits_path).open("r", encoding="utf-8") as handle:
            self.splits: Dict[str, Dict[str, List[int] | int]] = json.load(handle)
        self.max_seq_len = max_seq_len
        self.item_vocab_size = item_vocab_size
        self.mode = mode
        self.sampled_candidates = sampled_candidates
        self.samples: List[Tuple[List[int], int, Set[int]]] = []
        for split in self.splits.values():
            if mode == "val":
                history = split["train"]
                target = split["val_target"]
            else:
                history = split["train"] + [split["val_target"]]
                target = split["test_target"]
            seen = set(split["full_sequence"])
            self.samples.append((history, target, seen))

    def __len__(self) -> int:
        return len(self.samples)

    def _sample_candidates(self, target: int, seen: Set[int]) -> List[int]:
        candidates = {target}
        while len(candidates) < self.sampled_candidates:
            candidate = random.randint(1, self.item_vocab_size - 1)
            if candidate in seen and candidate != target:
                continue
            candidates.add(candidate)
        return list(candidates)

    def __getitem__(self, index: int) -> Dict[str, torch.Tensor]:
        history, target, seen = self.samples[index]
        padded_history, seq_len = pad_sequence(history, self.max_seq_len)
        candidates = self._sample_candidates(target, seen)
        candidate_labels = [1 if item_id == target else 0 for item_id in candidates]
        return {
            "item_seq": torch.tensor(padded_history, dtype=torch.long),
            "seq_len": torch.tensor(seq_len, dtype=torch.long),
            "candidates": torch.tensor(candidates, dtype=torch.long),
            "labels": torch.tensor(candidate_labels, dtype=torch.long),
            "target": torch.tensor(target, dtype=torch.long),
        }


def numpy_topk(scores: np.ndarray, k: int) -> np.ndarray:
    sorted_index = np.argsort(scores, axis=1)[:, ::-1]
    return sorted_index[:, :k]
