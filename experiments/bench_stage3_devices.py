#!/usr/bin/env python3
"""Quick Stage 3 speed check: ms per epoch for each GNN on MPS vs CPU (about 2-4 minutes).

It builds the same inputs as run_stage3_tc_gnn_benchmarks_v3.py, then times a few full epochs
(train forward + backward + optimizer step + eval forward, with a device sync) for each model.
It writes nothing. Use it to pick --device for Stage 3:

    python experiments/bench_stage3_devices.py                 # mps and cpu
    python experiments/bench_stage3_devices.py --devices cpu --threads 4 8

It also times the two gather styles (x[idx] vs x.index_select) on each device, because their
backward passes use different kernels (index_put_ accumulate vs index_add).
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import experiments.run_stage3_tc_gnn_benchmarks_v3 as s3  # noqa: E402
from experiments.mps_layers import select_device, sync_device  # noqa: E402


def build_inputs() -> dict:
    with s3.GRAPH_EDGES.open(encoding="utf-8-sig") as f:
        edge_rows = list(csv.DictReader(f))
    with (s3.DEFAULT_STAGE2_DIR / "STAGE2_OOF_ESA_FEATURES_8827_V3.csv").open(encoding="utf-8-sig") as f:
        oof_rows = list(csv.DictReader(f))
    d = s3.load_v3_stage2_inputs()
    node_rows = d["all_rows"]
    id_to_idx = {r["entry_id"]: i for i, r in enumerate(node_rows)}
    tab = np.array([int(r["tabaqa_1_to_12"]) if r["tabaqa_1_to_12"] else -1 for r in node_rows])
    x_meta, _ = s3.build_meta_matrix(node_rows)
    sem_cols = [c for c in oof_rows[0].keys() if c not in ("entry_id", "split", "in_core_cohort_7258")]
    x_sem = np.array([[float(r[c]) for c in sem_cols] for r in oof_rows], dtype=np.float32)
    cls_pca = np.array([[float(r[f"arabert_cls_pca_{k:02d}"]) for k in range(32)] for r in oof_rows], dtype=np.float32)
    g = s3.load_graph_and_struct_features(node_rows, edge_rows, id_to_idx, d["score_b_all"], tab, "chrono_sanad")
    x_np = np.hstack([x_meta, x_sem, g["struct"]])
    x_np = StandardScaler().fit(x_np[d["idx_train"]]).transform(x_np).astype(np.float32)
    ei_knn, ea_knn = s3.build_semantic_knn_view(cls_pca, k=8)
    return {"d": d, "g": g, "x": x_np, "ei_knn": ei_knn, "ea_knn": ea_knn}


def time_models(inp: dict, device: torch.device, epochs: int) -> dict[str, float]:
    d, g = inp["d"], inp["g"]
    x = torch.tensor(inp["x"], device=device)
    ei = {k: g[k].to(device) for k in ("edge_index_fwd", "edge_attr_fwd", "edge_index_rev", "edge_attr_rev", "edge_index_undir")}
    g4a = (x, ei["edge_index_fwd"], ei["edge_attr_fwd"], ei["edge_index_rev"], ei["edge_attr_rev"])
    be = "mps_native"
    models = {
        "G2b_MLP": (lambda: s3.DualHeadMLP(x.size(1)), (x,)),
        "G3a_GCN": (lambda: s3.UndirectedGNN(x.size(1), "gcn", backend=be), (x, ei["edge_index_undir"])),
        "G3b_SAGE": (lambda: s3.UndirectedGNN(x.size(1), "sage", backend=be), (x, ei["edge_index_undir"])),
        "G3c_GATv2": (lambda: s3.UndirectedGNN(x.size(1), "gatv2", backend=be), (x, ei["edge_index_undir"])),
        "G4a_TC_GNN": (lambda: s3.DirectedTCGNN(x.size(1), backend=be), g4a),
        "G4c_TC_GNN_kNN": (
            lambda: s3.DirectedTCGNN(x.size(1), use_knn=True, backend=be),
            (*g4a, inp["ei_knn"].to(device), inp["ea_knn"].to(device)),
        ),
    }
    tr = torch.tensor(d["idx_train"], device=device)
    y = torch.tensor(d["y_rank_all"][d["idx_train"]] - 1, device=device)
    out = {}
    for name, (fn, args) in models.items():
        model = fn().to(device)
        opt = torch.optim.AdamW(model.parameters(), lr=1.5e-3)

        def one_epoch() -> None:
            model.train()
            opt.zero_grad()
            r, s, _ = model(*args)
            nn.functional.cross_entropy(r.index_select(0, tr), y).backward()
            opt.step()
            model.eval()
            with torch.no_grad():
                r, s, _ = model(*args)
                torch.softmax(r, dim=-1).cpu()

        one_epoch()
        one_epoch()
        sync_device(device)
        t = time.perf_counter()
        for _ in range(epochs):
            one_epoch()
        sync_device(device)
        out[name] = 1000.0 * (time.perf_counter() - t) / epochs
    return out


def time_gather(device: torch.device, reps: int = 20) -> dict[str, float]:
    torch.manual_seed(0)
    n, e = 8827, 37364
    src = torch.randint(0, n, (e,), device=device)
    xs = torch.randn(n, 4, 32, device=device, requires_grad=True)
    go = torch.randn(e, 4, 32, device=device)
    res = {}
    for name, f in (("x[idx]", lambda: xs[src]), ("index_select", lambda: xs.index_select(0, src))):
        for _ in range(3):
            xs.grad = None
            f().backward(go)
        sync_device(device)
        t = time.perf_counter()
        for _ in range(reps):
            xs.grad = None
            f().backward(go)
        sync_device(device)
        res[name] = 1000.0 * (time.perf_counter() - t) / reps
    return res


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--devices", nargs="+", default=["mps", "cpu"])
    ap.add_argument("--threads", nargs="+", type=int, default=[0], help="CPU thread counts to try (0 = PyTorch default).")
    ap.add_argument("--epochs", type=int, default=5)
    args = ap.parse_args()
    torch.use_deterministic_algorithms(True, warn_only=True)
    print(f"torch {torch.__version__}, default CPU threads {torch.get_num_threads()}")
    inp = build_inputs()
    default_threads = torch.get_num_threads()
    rows = []
    for dev_name in args.devices:
        try:
            device = select_device(dev_name)
        except RuntimeError as exc:
            print(f"skip {dev_name}: {exc}")
            continue
        for th in args.threads if device.type == "cpu" else [0]:
            torch.set_num_threads(th if th > 0 else default_threads)
            label = f"{device.type}" + (f" ({torch.get_num_threads()} threads)" if device.type == "cpu" else "")
            print(f"\n== {label}")
            gt = time_gather(device)
            print("  gather fwd+bwd ms: " + ", ".join(f"{k}={v:.1f}" for k, v in gt.items()))
            ms = time_models(inp, device, args.epochs)
            for k, v in ms.items():
                print(f"  {k:16s} {v:8.1f} ms/epoch")
            rows.append((label, ms))
    if len(rows) > 1:
        print("\nSum over the 6 models (ms per epoch of each):")
        for label, ms in rows:
            print(f"  {label:24s} {sum(ms.values()):8.0f}")
        print("Lower is faster. Stage 3 trains each GNN 5 seeds x up to 200 epochs, so the ratio carries over.")


if __name__ == "__main__":
    main()
