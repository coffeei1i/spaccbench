"""Build a scenario data bundle for SpaCCBench.

Produces (in ``--output-dir``):

  <scenario>.h5ad                 — copy of the raw AnnData (cells × genes,
                                    plus obsm['spatial'] and obs cell-type col).
  <scenario>_top25.csv            — per-sample top-25 LR table.
  <scenario>_gt_signal.parquet    — cells × 25 expression-derived reference E.
  <scenario>_pw_act.parquet       — cells × pathways GSVA activity.

The top-25 selection logic mirrors scripts/prepare_interactions.py:

  E_i(L, R) = R_norm_i * smooth(L_norm, KNN5)_i
  score(L, R) = n_sources(L, R) * mean_{top 10% i} E_i(L, R)

This script intentionally has no dependency on scripts/io_methods.py so that
the package is self-contained.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import warnings

import numpy as np
import pandas as pd


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--scenario", required=True, help="Scenario name (e.g. tha)")
    p.add_argument("--adata", required=True, type=Path, help="Path to raw .h5ad")
    p.add_argument("--lr-db", required=True, type=Path,
                   help="Unified LR DB CSV (cols: ligand, receptor, n_sources, sources)")
    p.add_argument("--kegg", required=True, type=Path,
                   help="KEGG GMT file (e.g. kegg_mouse.gmt)")
    p.add_argument("--cell-type-col", default="cell_type",
                   help="adata.obs column containing cell type labels (default: cell_type)")
    p.add_argument("--output-dir", required=True, type=Path,
                   help="Where to write the bundled files (typically spaccbench/data/)")
    p.add_argument("--top-n", type=int, default=25, help="Top N LR pairs (default 25)")
    p.add_argument("--k-neighbours", type=int, default=5,
                   help="KNN neighbours for ligand smoothing (default 5)")
    p.add_argument("--top-pct-mean", type=float, default=0.10,
                   help="Use top this fraction of E values per LR for the ranking mean (default 0.10)")
    p.add_argument("--skip-pw-act", action="store_true",
                   help="Skip GSVA pathway activity computation (D4 will be unusable).")
    return p.parse_args()


def _minmax(x: np.ndarray) -> np.ndarray:
    lo, hi = float(np.nanmin(x)), float(np.nanmax(x))
    if hi - lo < 1e-12:
        return np.zeros_like(x)
    return (x - lo) / (hi - lo)


def _knn_smooth(L: np.ndarray, coords: np.ndarray, k: int) -> np.ndarray:
    from scipy.spatial import cKDTree
    tree = cKDTree(coords)
    _, idx = tree.query(coords, k=k + 1)  # includes self
    return L[idx].mean(axis=1)


def select_top25(
    adata,
    lr_db: pd.DataFrame,
    top_n: int = 25,
    k: int = 5,
    top_pct_mean: float = 0.10,
    cell_type_col: str = "cell_type",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (top25_table, gt_signal_matrix).

    top25_table columns: ligand, receptor, lr, n_sources, score, sender_celltype, receiver_celltype
    gt_signal_matrix:    cells × top_n DataFrame with column names 'lig-rec' (lowercase)
    """
    # Symbol lookup index for genes (case-insensitive).
    var_idx = {str(g).lower(): g for g in adata.var_names}
    coords = np.asarray(adata.obsm["spatial"], dtype=float)
    n_cells = adata.n_obs

    rows = []
    e_columns: dict[str, np.ndarray] = {}

    print(f"[1/3] Scoring {len(lr_db)} candidate LR pairs ...", flush=True)
    for _, row in lr_db.iterrows():
        lig = str(row["ligand"]).strip()
        rec = str(row["receptor"]).strip()
        lig_key = lig.lower()
        rec_key = rec.lower()
        if lig_key not in var_idx or rec_key not in var_idx:
            continue

        lig_vec = adata[:, var_idx[lig_key]].X
        rec_vec = adata[:, var_idx[rec_key]].X
        if hasattr(lig_vec, "toarray"):
            lig_vec = lig_vec.toarray().ravel()
            rec_vec = rec_vec.toarray().ravel()
        else:
            lig_vec = np.asarray(lig_vec).ravel()
            rec_vec = np.asarray(rec_vec).ravel()

        L_norm = _minmax(lig_vec)
        L_smooth = _knn_smooth(L_norm, coords, k=k)
        L_smooth_norm = _minmax(L_smooth)
        R_norm = _minmax(rec_vec)

        E = R_norm * L_smooth_norm
        if not np.isfinite(E).any() or float(np.nanmax(E)) < 1e-12:
            continue

        n_top = max(int(round(n_cells * top_pct_mean)), 1)
        top_vals = np.sort(E)[-n_top:]
        mean_top = float(top_vals.mean())
        n_sources = int(row.get("n_sources", 1) or 1)
        score = n_sources * mean_top

        lr_key = f"{lig_key}-{rec_key}"
        e_columns[lr_key] = E
        rows.append({
            "ligand": lig,
            "receptor": rec,
            "lr": lr_key,
            "n_sources": n_sources,
            "score": score,
        })

    if not rows:
        raise RuntimeError("No LR pair scored. Check gene overlap between adata and LR DB.")

    scored = pd.DataFrame(rows).sort_values("score", ascending=False)
    top25 = scored.head(top_n).reset_index(drop=True)

    # Add sender/receiver cell type by argmax of mean L_norm / R_norm per cell type.
    if cell_type_col in adata.obs:
        ct = adata.obs[cell_type_col].astype(str).to_numpy()
        ct_levels = pd.Series(ct).unique().tolist()
        ct_mat = pd.DataFrame({"ct": ct})

        senders = []
        receivers = []
        for _, r in top25.iterrows():
            lig_key = r["ligand"].lower()
            rec_key = r["receptor"].lower()
            if lig_key not in var_idx or rec_key not in var_idx:
                senders.append("")
                receivers.append("")
                continue
            lig_vec = adata[:, var_idx[lig_key]].X
            rec_vec = adata[:, var_idx[rec_key]].X
            if hasattr(lig_vec, "toarray"):
                lig_vec = lig_vec.toarray().ravel()
                rec_vec = rec_vec.toarray().ravel()
            else:
                lig_vec = np.asarray(lig_vec).ravel()
                rec_vec = np.asarray(rec_vec).ravel()
            ct_mat["L"] = lig_vec
            ct_mat["R"] = rec_vec
            sender_means = ct_mat.groupby("ct")["L"].mean()
            recv_means = ct_mat.groupby("ct")["R"].mean()
            senders.append(sender_means.idxmax())
            receivers.append(recv_means.idxmax())
        top25["sender_celltype"] = senders
        top25["receiver_celltype"] = receivers
    else:
        warnings.warn(
            f"adata.obs has no column {cell_type_col!r}; skipping sender/receiver assignment."
        )

    # Build GT matrix (cells × top_n).
    gt = pd.DataFrame(
        {lr: e_columns[lr] for lr in top25["lr"]},
        index=adata.obs_names,
    )
    return top25, gt


def compute_pathway_activity(adata, kegg_path: Path) -> pd.DataFrame:
    """Compute cells × pathways via decoupleR GSVA."""
    try:
        import decoupler as dc
        import scanpy as sc
    except ImportError:
        raise ImportError("Install decoupler + scanpy for D4: `pip install decoupler scanpy`")

    from spaccbench.core.d4_pathway import load_gmt
    kegg = load_gmt(kegg_path)

    if adata.X.max() > 50:
        adata = adata.copy()
        sc.pp.normalize_total(adata, target_sum=1e4)
        sc.pp.log1p(adata)

    dc.run_gsva(
        mat=adata, net=kegg, source="source", target="target",
        use_raw=False, verbose=True,
    )
    pw_act = adata.obsm["gsva_estimate"]
    if hasattr(pw_act, "values"):
        return pd.DataFrame(pw_act.values, index=adata.obs_names, columns=pw_act.columns)
    pathway_names = adata.uns.get("gsva_estimate_columns", [f"pw{i}" for i in range(pw_act.shape[1])])
    return pd.DataFrame(pw_act, index=adata.obs_names, columns=pathway_names)


def main():
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[0/3] Loading adata: {args.adata}", flush=True)
    import anndata as ad
    adata = ad.read_h5ad(args.adata)
    lr_db = pd.read_csv(args.lr_db)
    print(f"      cells={adata.n_obs}  genes={adata.n_vars}  LR pool={len(lr_db)}")

    top25, gt = select_top25(
        adata, lr_db,
        top_n=args.top_n,
        k=args.k_neighbours,
        top_pct_mean=args.top_pct_mean,
        cell_type_col=args.cell_type_col,
    )

    # Save outputs.
    scn = args.scenario
    h5ad_path = args.output_dir / f"{scn}.h5ad"
    top25_path = args.output_dir / f"{scn}_top25.csv"
    gt_path = args.output_dir / f"{scn}_gt_signal.parquet"

    print(f"[2/3] Writing scenario bundle to {args.output_dir} ...")
    adata.write_h5ad(h5ad_path, compression="gzip")
    top25.to_csv(top25_path, index=False)
    gt.to_parquet(gt_path)

    if not args.skip_pw_act:
        print(f"[3/3] Running GSVA pathway activity (may take 5-10 min)...")
        pw_act = compute_pathway_activity(adata, args.kegg)
        pw_path = args.output_dir / f"{scn}_pw_act.parquet"
        pw_act.to_parquet(pw_path)
        print(f"      Wrote {pw_path} (shape {pw_act.shape})")

    print("Done.")


if __name__ == "__main__":
    sys.exit(main())
