from __future__ import annotations

import argparse

import torch

from common import ensure_dir, load_config, resolve_path
from model import SASRecLite, TemperatureScaledHead


class ExportWrapper(torch.nn.Module):
    def __init__(self, model: torch.nn.Module, temperature_head: torch.nn.Module | None) -> None:
        super().__init__()
        self.model = model
        self.temperature_head = temperature_head

    def forward(self, item_seq: torch.Tensor, seq_len: torch.Tensor) -> torch.Tensor:
        logits = self.model(item_seq, seq_len)
        if self.temperature_head is not None:
            logits = self.temperature_head(logits)
        return logits


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export the best checkpoint to ONNX.")
    parser.add_argument("--config", default="training/configs/default.yaml")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    checkpoint_path = resolve_path(config, "checkpoints_dir") / config["export"]["checkpoint_name"]
    onnx_dir = ensure_dir(resolve_path(config, "onnx_dir"))
    onnx_path = onnx_dir / config["export"]["onnx_name"]

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

    temperature_head = None
    if checkpoint["temperature_head_state_dict"] is not None:
        temperature_head = TemperatureScaledHead()
        temperature_head.load_state_dict(checkpoint["temperature_head_state_dict"])
        temperature_head.eval()

    wrapper = ExportWrapper(model, temperature_head)
    sample_item_seq = torch.zeros((1, config["data"]["max_seq_len"]), dtype=torch.long)
    sample_seq_len = torch.ones((1,), dtype=torch.long)

    torch.onnx.export(
        wrapper,
        (sample_item_seq, sample_seq_len),
        onnx_path,
        input_names=["item_seq", "seq_len"],
        output_names=["scores"],
        dynamic_axes={
            "item_seq": {0: "batch_size"},
            "seq_len": {0: "batch_size"},
            "scores": {0: "batch_size"},
        },
        opset_version=config["export"]["opset_version"],
    )
    print(f"Exported ONNX model to {onnx_path}")


if __name__ == "__main__":
    main()
