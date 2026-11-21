"""Tests for pure-PyTorch MPS-native graph layers (runs on CPU and AMD Radeon MPS)."""

from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")

from experiments.mps_layers import MPSGATv2Conv, MPSGCNConv, MPSSAGEConv, select_device


def _devices_to_test() -> list[torch.device]:
    devs = [torch.device("cpu")]
    if torch.backends.mps.is_available():
        devs.append(torch.device("mps"))
    return devs


@pytest.mark.parametrize("device", _devices_to_test(), ids=lambda d: d.type)
def test_mps_gnn_layers_forward_backward(device: torch.device) -> None:
    torch.manual_seed(42)
    n, e, in_c, hid = 64, 180, 32, 32
    x = torch.randn(n, in_c, device=device, requires_grad=True)
    ei = torch.randint(0, n, (2, e), device=device)
    ea = torch.randn(e, 5, device=device)

    for layer, use_ea in [
        (MPSGATv2Conv(in_c, hid // 4, heads=4, edge_dim=5, dropout=0.1).to(device), True),
        (MPSGATv2Conv(in_c, hid // 4, heads=4, edge_dim=None, dropout=0.1).to(device), False),
        (MPSGCNConv(in_c, hid).to(device), False),
        (MPSSAGEConv(in_c, hid).to(device), False),
    ]:
        out = layer(x, ei, ea) if use_ea else layer(x, ei)
        assert out.shape == (n, hid)
        assert torch.isfinite(out).all()
        loss = out.pow(2).mean()
        loss.backward()
        assert x.grad is not None and torch.isfinite(x.grad).all()
        x.grad.zero_()


def test_select_device_auto() -> None:
    dev = select_device("auto")
    if torch.backends.mps.is_available():
        assert dev.type == "mps"
    elif torch.cuda.is_available():
        assert dev.type == "cuda"
    else:
        assert dev.type == "cpu"
