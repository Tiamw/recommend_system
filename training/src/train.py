from __future__ import annotations

import argparse
import json

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

from common import ensure_dir, load_config, resolve_path, save_json, set_seed
from dataset import SequenceEvalDataset, SequenceTrainDataset
from metrics import summarize_metrics
from model import SASRecLite, TemperatureScaledHead


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a SASRec-lite model.")
    parser.add_argument("--config", default="training/configs/default.yaml")
    parser.add_argument("--no-temperature-head", action="store_true")
    return parser.parse_args()


def detect_device(requested: str) -> torch.device:
    if requested == "cpu":
        return torch.device("cpu")
    if requested == "cuda":
        return torch.device("cuda")
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def evaluate_model(model: torch.nn.Module, temperature_head: torch.nn.Module | None, dataloader: DataLoader, device: torch.device):
    model.eval()
    all_scores = []
    all_labels = []
    with torch.no_grad():
        for batch in dataloader:
            logits = model(batch["item_seq"].to(device), batch["seq_len"].to(device))
            if temperature_head is not None:
                logits = temperature_head(logits)
            candidate_scores = logits.gather(1, batch["candidates"].to(device))
            all_scores.append(candidate_scores.cpu())
            all_labels.append(batch["labels"].cpu())
    return summarize_metrics(torch.cat(all_scores, dim=0), torch.cat(all_labels, dim=0), k=10)


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    set_seed(config["project"]["seed"])
    device = detect_device(config["training"]["device"])

    with (resolve_path(config, "mappings_dir") / "reverse_item_id_mapping.json").open("r", encoding="utf-8") as handle:
        reverse_mapping = json.load(handle)
    item_vocab_size = max(int(key) for key in reverse_mapping.keys()) + 1
    splits_path = resolve_path(config, "processed_dir") / "splits.json"

    train_dataset = SequenceTrainDataset(
        splits_path=splits_path,
        max_seq_len=config["data"]["max_seq_len"],
        item_vocab_size=item_vocab_size,
        num_negative_samples=config["training"]["num_negative_samples"],
    )
    val_dataset = SequenceEvalDataset(
        splits_path=splits_path,
        max_seq_len=config["data"]["max_seq_len"],
        item_vocab_size=item_vocab_size,
        mode="val",
        sampled_candidates=config["data"]["sampled_eval_candidates"],
    )
    train_loader = DataLoader(train_dataset, batch_size=config["training"]["batch_size"], shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=config["training"]["eval_batch_size"], shuffle=False)

    model = SASRecLite(
        item_vocab_size=item_vocab_size,
        max_seq_len=config["data"]["max_seq_len"],
        embedding_dim=config["training"]["embedding_dim"],
        num_blocks=config["training"]["num_blocks"],
        num_heads=config["training"]["num_heads"],
        dropout=config["training"]["dropout"],
    ).to(device)
    temperature_head = None if args.no_temperature_head else TemperatureScaledHead().to(device)
    parameters = list(model.parameters()) + ([] if temperature_head is None else list(temperature_head.parameters()))
    optimizer = torch.optim.Adam(parameters, lr=config["training"]["lr"], weight_decay=config["training"]["weight_decay"])

    checkpoints_dir = ensure_dir(resolve_path(config, "checkpoints_dir"))
    metrics_dir = ensure_dir(resolve_path(config, "metrics_dir"))
    best_checkpoint_path = checkpoints_dir / config["export"]["checkpoint_name"]

    best_hr = -1.0
    patience_counter = 0
    history = []

    for epoch in range(1, config["training"]["epochs"] + 1):
        model.train()
        total_loss = 0.0
        for batch in train_loader:
            logits = model(batch["item_seq"].to(device), batch["seq_len"].to(device))
            if temperature_head is not None:
                logits = temperature_head(logits)
            pos_scores = logits.gather(1, batch["pos_item"].to(device).unsqueeze(1)).squeeze(1)
            neg_scores = logits.gather(1, batch["neg_item"].to(device).unsqueeze(1)).squeeze(1)
            loss = F.softplus(-(pos_scores - neg_scores)).mean()
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(parameters, max_norm=5.0)
            optimizer.step()
            total_loss += loss.item()

        val_metrics = evaluate_model(model, temperature_head, val_loader, device)
        epoch_metrics = {"epoch": epoch, "train_loss": total_loss / max(len(train_loader), 1), **val_metrics}
        history.append(epoch_metrics)
        print(json.dumps(epoch_metrics, ensure_ascii=False))

        if val_metrics["hr@10"] > best_hr:
            best_hr = val_metrics["hr@10"]
            patience_counter = 0
            torch.save(
                {
                    "model_state_dict": model.state_dict(),
                    "temperature_head_state_dict": None if temperature_head is None else temperature_head.state_dict(),
                    "config": config,
                    "item_vocab_size": item_vocab_size,
                },
                best_checkpoint_path,
            )
        else:
            patience_counter += 1
            if patience_counter >= config["training"]["early_stopping_patience"]:
                break

    save_json({"history": history, "best_hr@10": best_hr}, metrics_dir / "train_metrics.json")
    print(f"Best checkpoint saved to {best_checkpoint_path}")


if __name__ == "__main__":
    main()
