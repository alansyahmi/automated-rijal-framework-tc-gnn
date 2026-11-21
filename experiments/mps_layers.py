"""Pure-PyTorch MPS/CPU/CUDA graph layers avoiding PyG scatter_reduce ops unsupported on macOS MPS."""

from __future__ import annotations

import math
from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F


def select_device(requested: str = "auto") -> torch.device:
    """Resolve 'auto' to mps -> cuda -> cpu, or honor explicit device string."""
    req = requested.lower().strip()
    if req == "auto":
        if torch.backends.mps.is_available():
            return torch.device("mps")
        if torch.cuda.is_available():
            return torch.device("cuda")
        return torch.device("cpu")
    if req == "mps":
        if not torch.backends.mps.is_available():
            raise RuntimeError("Requested --device mps, but torch.backends.mps.is_available() is False.")
        return torch.device("mps")
    if req == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("Requested --device cuda, but torch.cuda.is_available() is False.")
        return torch.device("cuda")
    if req == "cpu":
        return torch.device("cpu")
    raise ValueError(f"Unsupported device: {requested!r}")


def empty_device_cache(device: torch.device) -> None:
    if device.type == "cuda":
        torch.cuda.empty_cache()
    elif device.type == "mps" and hasattr(torch, "mps") and hasattr(torch.mps, "empty_cache"):
        torch.mps.empty_cache()


def sync_device(device: torch.device) -> None:
    if device.type == "cuda":
        torch.cuda.synchronize()
    elif device.type == "mps" and hasattr(torch, "mps") and hasattr(torch.mps, "synchronize"):
        torch.mps.synchronize()


def _segment_softmax_index_add(scores: torch.Tensor, dst: torch.Tensor, num_nodes: int) -> torch.Tensor:
    """Numerically bounded edge softmax over destination nodes using only index_add."""
    w = torch.exp(scores.clamp(-15.0, 15.0))
    denom = torch.zeros((num_nodes, scores.size(1)), device=scores.device, dtype=scores.dtype)
    denom = denom.index_add(0, dst, w).clamp_min(1e-8)
    return w / denom[dst]


class MPSGATv2Conv(nn.Module):
    """Edge-conditioned GATv2 (Brody et al., 2022) implemented solely with MPS-safe index_add."""

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        heads: int = 4,
        edge_dim: Optional[int] = None,
        dropout: float = 0.0,
        add_self_loops: bool = False,
        negative_slope: float = 0.2,
    ) -> None:
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.heads = heads
        self.edge_dim = edge_dim
        self.dropout = dropout
        self.add_self_loops = add_self_loops
        self.negative_slope = negative_slope

        dim = heads * out_channels
        self.lin_l = nn.Linear(in_channels, dim, bias=True)
        self.lin_r = nn.Linear(in_channels, dim, bias=True)
        self.lin_edge = nn.Linear(edge_dim, dim, bias=False) if edge_dim is not None else None
        self.att = nn.Parameter(torch.empty(1, heads, out_channels))
        self.bias = nn.Parameter(torch.zeros(dim))
        nn.init.xavier_uniform_(self.att)

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        edge_attr: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        n = x.size(0)
        h, c = self.heads, self.out_channels
        src, dst = edge_index[0], edge_index[1]

        x_l = self.lin_l(x).view(n, h, c)
        x_r = self.lin_r(x).view(n, h, c)
        out = torch.zeros((n, h, c), device=x.device, dtype=x.dtype)

        if src.numel() > 0:
            msg_att = x_l[src] + x_r[dst]
            if self.lin_edge is not None and edge_attr is not None:
                msg_att = msg_att + self.lin_edge(edge_attr).view(-1, h, c)
            e = F.leaky_relu(msg_att, negative_slope=self.negative_slope)
            alpha_raw = (e * self.att).sum(dim=-1)
            alpha = _segment_softmax_index_add(alpha_raw, dst, n)
            alpha = F.dropout(alpha, p=self.dropout, training=self.training)
            msg = x_r[src] * alpha.unsqueeze(-1)
            out = out.index_add(0, dst, msg)

        return out.reshape(n, h * c) + self.bias


class MPSGCNConv(nn.Module):
    """Symmetric normalized GCN convolution implemented with index_add (no scatter_reduce)."""

    def __init__(self, in_channels: int, out_channels: int) -> None:
        super().__init__()
        self.lin = nn.Linear(in_channels, out_channels, bias=False)
        self.bias = nn.Parameter(torch.zeros(out_channels))
        self.reset_parameters()

    def reset_parameters(self) -> None:
        bound = 1.0 / math.sqrt(self.lin.out_features)
        nn.init.uniform_(self.lin.weight, -bound, bound)
        nn.init.zeros_(self.bias)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        n = x.size(0)
        h = self.lin(x)
        self_loops = torch.arange(n, device=x.device, dtype=edge_index.dtype)
        loops = torch.stack([self_loops, self_loops], dim=0)
        ei = torch.cat([edge_index, loops], dim=1) if edge_index.numel() > 0 else loops
        src, dst = ei[0], ei[1]

        deg = torch.zeros(n, device=x.device, dtype=x.dtype).index_add(
            0, dst, torch.ones(dst.size(0), device=x.device, dtype=x.dtype)
        )
        inv_sqrt = deg.clamp_min(1.0).pow(-0.5)
        norm = inv_sqrt[src] * inv_sqrt[dst]
        out = torch.zeros_like(h).index_add(0, dst, h[src] * norm.unsqueeze(-1))
        return out + self.bias


class MPSSAGEConv(nn.Module):
    """Mean-aggregator GraphSAGE layer implemented cleanly with index_add."""

    def __init__(self, in_channels: int, out_channels: int) -> None:
        super().__init__()
        self.lin_l = nn.Linear(in_channels, out_channels, bias=True)
        self.lin_r = nn.Linear(in_channels, out_channels, bias=False)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        n = x.size(0)
        out_neigh = torch.zeros_like(x)
        if edge_index.numel() > 0:
            src, dst = edge_index[0], edge_index[1]
            ones = torch.ones(dst.size(0), device=x.device, dtype=x.dtype)
            deg = torch.zeros(n, device=x.device, dtype=x.dtype).index_add(0, dst, ones).clamp_min(1.0)
            summed = out_neigh.index_add(0, dst, x[src])
            out_neigh = summed / deg.unsqueeze(-1)
        return self.lin_l(out_neigh) + self.lin_r(x)
