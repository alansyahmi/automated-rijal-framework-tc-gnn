#!/usr/bin/env python3
"""End-to-end pipeline orchestrator for AMD Radeon Pro 5500M (macOS Metal/MPS, 4 GB VRAM).

Runs Track L (Stage 2 ESA with dynamic padding + gradient accumulation, Stage 3
TC-GNN using pure-PyTorch MPS-native index_add graph layers), Track R
experiments A-D, al-Kashif external validation, stepped showcases, and pytest.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.mps_layers import empty_device_cache, select_device  # noqa: E402


def _run(cmd: list[str], title: str) -> None:
    print(f"\n=== [Radeon 5500M MPS] {title} ===")
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


def check_radeon_mps() -> torch.device:
    dev = select_device("mps")
    print(f"PyTorch: {torch.__version__} | mps built={torch.backends.mps.is_built()} available={torch.backends.mps.is_available()}")
    try:
        out = subprocess.check_output(["system_profiler", "SPDisplaysDataType"], text=True)
        for line in out.splitlines():
            if any(k in line for k in ("Chipset Model", "VRAM", "Metal Support")):
                print(" ", line.strip())
    except Exception:
        pass
    a = torch.randn(256, 256, device=dev)
    b = torch.randn(256, 256, device=dev)
    _ = (a @ b).sum().item()
    empty_device_cache(dev)
    return dev


def main() -> None:
    parser = argparse.ArgumentParser(description="Run full Track R+L v3 pipeline on AMD Radeon Pro 5500M (MPS).")
    parser.add_argument("--epochs", type=int, default=5, help="Stage 2 ESA fine-tuning epochs per fold.")
    parser.add_argument("--batch-size", type=int, default=16, help="Stage 2 micro-batch size (16 tuned for 4GB VRAM FP32).")
    parser.add_argument("--grad-accum", type=int, default=2, help="Gradient accumulation steps (16*2 = 32 effective bs).")
    parser.add_argument("--stage2-dir", type=Path, default=ROOT / "results/stage2_esa_benchmarks_v3_2026-11-21")
    parser.add_argument("--stage3-dir", type=Path, default=ROOT / "results/stage3_tc_gnn_benchmarks_v3_2026-11-21")
    parser.add_argument("--exp-dir", type=Path, default=ROOT / "results/layered_experiments_v3_2026-11-21")
    parser.add_argument("--rebuild-deterministic", action="store_true", help="Re-run P2 and P3 deterministic builders.")
    parser.add_argument("--skip-stage2", action="store_true", help="Skip Stage 2 ESA if OOF CSV already exists.")
    parser.add_argument("--no-resume", action="store_true", help="Disable Stage 2 checkpoint resumption.")
    parser.add_argument("--smoke", action="store_true", help="Verify MPS hardware + run full pytest suite (fast check).")
    args = parser.parse_args()

    py = sys.executable
    check_radeon_mps()

    if args.smoke:
        _run([py, "-m", "pytest", "-q"], "Full Pytest Suite (CPU + MPS GPU contract checks)")
        print("\nRadeon 5500M MPS smoke check passed.")
        return

    if args.rebuild_deterministic:
        _run([py, "dataset_discovery/target_feasibility/build_layered_scores_v3.py"], "P2: Deterministic Layers (B, E1, E2)")
        _run([py, "dataset_discovery/target_feasibility/build_kashif_validation_v1.py"], "P3: al-Kashif External Validation")

    if not args.skip_stage2:
        cmd_s2 = [
            py,
            "experiments/run_stage2_esa_benchmarks_v3.py",
            "--device", "mps",
            "--epochs", str(args.epochs),
            "--batch-size", str(args.batch_size),
            "--grad-accum", str(args.grad_accum),
            "--out-dir", str(args.stage2_dir),
            "--allow-hf-download",
        ]
        if not args.no_resume:
            cmd_s2.append("--resume")
        _run(cmd_s2, "Stage 2: AraBERTv02 ESA & Generic-Sentiment Baseline (MPS FP32)")

    _run(
        [
            py,
            "experiments/run_stage3_tc_gnn_benchmarks_v3.py",
            "--device", "mps",
            "--backend", "mps_native",
            "--stage2-dir", str(args.stage2_dir),
            "--out-dir", str(args.stage3_dir),
        ],
        "Stage 3: TC-GNN 5-Seed Ablations (Pure-PyTorch MPS index_add)",
    )

    _run(
        [
            py,
            "experiments/run_layered_experiments_v3.py",
            "--stage2-dir", str(args.stage2_dir),
            "--stage3-dir", str(args.stage3_dir),
            "--out-dir", str(args.exp_dir),
        ],
        "Stage 4 (P5): Unified Track R+L Experiments, al-Kashif Bootstrap & Final 8827 Table",
    )

    _run([py, "experiments/visualize_layered_showcases_v3.py"], "Stage 5 (P6): Stepped Layered Showcases")
    _run([py, "-m", "pytest", "-q"], "Full Verification Suite (CPU + MPS)")
    print(f"\nRadeon 5500M MPS pipeline complete -> {args.exp_dir}")


if __name__ == "__main__":
    main()
