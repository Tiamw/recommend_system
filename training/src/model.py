from __future__ import annotations

import torch
from torch import nn


class SASRecLite(nn.Module):
    def __init__(
        self,
        item_vocab_size: int,
        max_seq_len: int,
        embedding_dim: int,
        num_blocks: int,
        num_heads: int,
        dropout: float,
    ) -> None:
        super().__init__()
        self.item_embedding = nn.Embedding(item_vocab_size, embedding_dim, padding_idx=0)
        self.position_embedding = nn.Embedding(max_seq_len, embedding_dim)
        self.dropout = nn.Dropout(dropout)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embedding_dim,
            nhead=num_heads,
            dim_feedforward=embedding_dim * 4,
            dropout=dropout,
            batch_first=True,
            activation="gelu",
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_blocks)
        self.layer_norm = nn.LayerNorm(embedding_dim)

    def encode(self, item_seq: torch.Tensor, seq_len: torch.Tensor) -> torch.Tensor:
        batch_size, seq_size = item_seq.shape
        positions = torch.arange(seq_size, device=item_seq.device).unsqueeze(0).expand(batch_size, -1)
        embeddings = self.item_embedding(item_seq) + self.position_embedding(positions)
        embeddings = self.layer_norm(self.dropout(embeddings))
        causal_mask = torch.triu(torch.ones(seq_size, seq_size, device=item_seq.device, dtype=torch.bool), diagonal=1)
        padding_mask = item_seq.eq(0)
        encoded = self.encoder(embeddings, mask=causal_mask, src_key_padding_mask=padding_mask)
        last_index = (seq_len - 1).clamp(min=0)
        return encoded[torch.arange(batch_size, device=item_seq.device), last_index]

    def forward(self, item_seq: torch.Tensor, seq_len: torch.Tensor) -> torch.Tensor:
        user_state = self.encode(item_seq, seq_len)
        return user_state @ self.item_embedding.weight.t()


class TemperatureScaledHead(nn.Module):
    def __init__(self, initial_temperature: float = 1.0) -> None:
        super().__init__()
        self.log_temperature = nn.Parameter(torch.log(torch.tensor(initial_temperature)))

    def forward(self, logits: torch.Tensor) -> torch.Tensor:
        temperature = torch.exp(self.log_temperature).clamp(min=0.1, max=10.0)
        return logits / temperature
