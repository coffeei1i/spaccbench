"""D4: downstream pathway activation via KEGG.

For each (LR pair, candidate pathway P) we cast the prediction as a binary
classification: the top 10% of cells by pathway activity are positives, and
the method's LR score is the classifier score. The per-LR D4 score is the
maximum AUC across the candidate pathway set, averaged over LR pairs at the
method level.

Significance is assessed by permuting the receptor -> pathway mapping (the
candidate count and max-aggregation are preserved), recomputing the method
mean AUC, and comparing the observed value against the permutation null.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

_EPS = 1e-12


def _normalise_lr(lr: str) -> str:
    return str(lr).strip().lower().replace("_", "-")


# ----- KEGG loading -----------------------------------------------------------

def load_gmt(gmt_path: str | Path) -> pd.DataFrame:
    """Load a GMT file into a long-format DataFrame with columns
    ``source`` (pathway) and ``target`` (gene symbol).
    """
    rows = []
    with open(gmt_path) as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 3:
                continue
            pw = parts[0].strip()
            genes = [g.strip() for g in parts[2:] if g.strip()]
            for g in genes:
                rows.append({"source": pw, "target": g})
    return pd.DataFrame(rows)


def receptor_to_pathways(
    kegg: pd.DataFrame,
    max_pw: int = 20,
) -> dict[str, list[str]]:
    """For each gene (target), return up to ``max_pw`` pathways alphabetically.

    Returned keys are lowercased gene names.
    """
    out: dict[str, list[str]] = {}
    for gene, sub in kegg.groupby("target"):
        pws = sorted(set(sub["source"].tolist()))
        out[str(gene).lower()] = pws[:max_pw]
    return out


# ----- Pathway activity (GSVA via decoupleR) ----------------------------------

def compute_pathway_activity(
    adata,
    kegg: pd.DataFrame,
) -> pd.DataFrame:
    """Compute cells × pathways activity using decoupleR's GSVA on log1p
    expression.

    Returns a DataFrame indexed by cell barcodes with one column per pathway.
    Requires ``decoupler`` to be installed.
    """
    try:
        import decoupler as dc
    except ImportError as e:
        raise ImportError(
            "decoupler is required for D4 GSVA. Install via `pip install decoupler`."
        ) from e

    if "log1p" not in adata.layers and adata.X.max() > 50:
        # Crude check: if X looks like raw counts, log1p it on the fly.
        import scanpy as sc
        adata = adata.copy()
        sc.pp.normalize_total(adata, target_sum=1e4)
        sc.pp.log1p(adata)

    dc.run_gsva(
        mat=adata,
        net=kegg,
        source="source",
        target="target",
        use_raw=False,
        verbose=False,
    )
    pw_act = adata.obsm["gsva_estimate"]
    return pd.DataFrame(
        pw_act.values if hasattr(pw_act, "values") else pw_act,
        index=adata.obs_names,
        columns=adata.uns.get("gsva_estimate_columns", pw_act.columns) if hasattr(pw_act, "columns") else None,
    )


# ----- AUC ---------------------------------------------------------------------

def compute_auc(
    lr_score: np.ndarray,
    pathway_act: np.ndarray,
    top_pct: float = 0.10,
) -> float:
    """Compute AUC with the top ``top_pct`` of pathway-activity cells as positives.

    Returns NaN if positive class is empty or LR score has no variance.
    """
    lr_score = np.asarray(lr_score, dtype=float)
    pathway_act = np.asarray(pathway_act, dtype=float)
    n = len(lr_score)
    if n != len(pathway_act):
        return float("nan")
    if not np.isfinite(lr_score).any() or not np.isfinite(pathway_act).any():
        return float("nan")
    n_pos = max(int(round(n * top_pct)), 1)
    if n_pos >= n:
        return float("nan")
    threshold = np.sort(pathway_act)[-n_pos]
    y_true = (pathway_act >= threshold).astype(int)
    if y_true.sum() == 0 or y_true.sum() == n:
        return float("nan")
    score = np.nan_to_num(lr_score, nan=0.0)
    if np.std(score) < _EPS:
        return float("nan")
    try:
        return float(roc_auc_score(y_true, score))
    except Exception:
        return float("nan")


# ----- Method-level mean AUC ---------------------------------------------------

def _per_lr_best_auc(
    scores: pd.DataFrame,
    pw_act: pd.DataFrame,
    top25_lr: Iterable[str],
    rec_to_pw: dict[str, list[str]],
    top_pct: float,
) -> pd.DataFrame:
    """For each LR pair, compute max-AUC over its candidate pathways."""
    top25 = [_normalise_lr(x) for x in top25_lr]
    score_cols = {_normalise_lr(c): c for c in scores.columns}
    common_cells = scores.index.intersection(pw_act.index)

    rows = []
    for lr in top25:
        if lr not in score_cols:
            continue
        try:
            lig, rec = lr.split("-", 1)
        except ValueError:
            continue
        m_vec = scores.loc[common_cells, score_cols[lr]].to_numpy(dtype=float)
        if not np.isfinite(m_vec).any() or np.nanmax(np.abs(m_vec)) < _EPS:
            continue
        candidates = rec_to_pw.get(rec.lower(), [])
        candidates_in_pw = [p for p in candidates if p in pw_act.columns]
        if not candidates_in_pw:
            continue
        best_auc = float("-inf")
        best_pw = None
        for p in candidates_in_pw:
            act = pw_act.loc[common_cells, p].to_numpy(dtype=float)
            auc = compute_auc(m_vec, act, top_pct)
            if np.isfinite(auc) and auc > best_auc:
                best_auc, best_pw = auc, p
        if best_pw is None:
            continue
        rows.append({
            "lr": lr,
            "ligand": lig,
            "receptor": rec,
            "best_pathway": best_pw,
            "best_auc": best_auc,
            "n_candidate": len(candidates_in_pw),
        })
    return pd.DataFrame(rows)


def _permute_rec_to_pw(
    rec_to_pw: dict[str, list[str]],
    all_pathways: list[str],
    rng: np.random.Generator,
) -> dict[str, list[str]]:
    n_total = len(all_pathways)
    out: dict[str, list[str]] = {}
    for rec, pws in rec_to_pw.items():
        k = min(len(pws), n_total)
        if k == 0:
            out[rec] = []
            continue
        idx = rng.choice(n_total, size=k, replace=False)
        out[rec] = [all_pathways[i] for i in idx]
    return out


def d4_pathway(
    scores: pd.DataFrame,
    pw_act: pd.DataFrame,
    top25_lr: Iterable[str],
    kegg: pd.DataFrame,
    n_perm: int = 200,
    top_pct: float = 0.10,
    max_pw_per_receptor: int = 20,
    seed: int = 0,
) -> dict:
    """Compute D4 KEGG pathway activation.

    Parameters
    ----------
    scores : pd.DataFrame
        Per-cell LR score matrix.
    pw_act : pd.DataFrame
        Pre-computed pathway activity (cells × pathways), e.g. from
        ``compute_pathway_activity``.
    top25_lr : iterable of str
        Per-sample top-25 LR list.
    kegg : pd.DataFrame
        Long-format KEGG dataframe with columns ``source`` (pathway) and
        ``target`` (gene). Used to map receptor -> candidate pathways.
    n_perm : int
        Number of permutations for the null distribution. 0 disables permutation.
    top_pct : float
        Fraction of top pathway-activity cells defining positive labels (0.10 = top 10%).
    max_pw_per_receptor : int
        Cap on candidate pathways per receptor (alphabetical truncation).
    seed : int
        RNG seed for permutation.

    Returns
    -------
    dict with keys:
        - ``mean_auc`` (float)
        - ``perm_p`` (float, single-sided; NaN if n_perm=0)
        - ``null_mean`` (float)
        - ``null_std`` (float)
        - ``n_lr`` (int)
        - ``n_sig_lr`` (int, count of LR pairs with best_auc > 0.6)
        - ``per_lr`` (pd.DataFrame)
    """
    rec_to_pw = receptor_to_pathways(kegg, max_pw=max_pw_per_receptor)
    per_lr = _per_lr_best_auc(scores, pw_act, top25_lr, rec_to_pw, top_pct)

    if per_lr.empty:
        return {
            "mean_auc": float("nan"),
            "perm_p": float("nan"),
            "null_mean": float("nan"),
            "null_std": float("nan"),
            "n_lr": 0,
            "n_sig_lr": 0,
            "per_lr": per_lr,
        }

    obs_mean = float(per_lr["best_auc"].mean())
    n_sig = int((per_lr["best_auc"] > 0.6).sum())

    if n_perm > 0:
        rng = np.random.default_rng(seed)
        all_pathways = list(pw_act.columns)
        null_means: list[float] = []
        for _ in range(n_perm):
            rec_to_pw_null = _permute_rec_to_pw(rec_to_pw, all_pathways, rng)
            null_detail = _per_lr_best_auc(scores, pw_act, top25_lr, rec_to_pw_null, top_pct)
            null_means.append(float(null_detail["best_auc"].mean()) if len(null_detail) else float("nan"))
        nulls = np.asarray(null_means)
        nulls_finite = nulls[np.isfinite(nulls)]
        if len(nulls_finite):
            perm_p = (np.sum(nulls_finite >= obs_mean) + 1) / (len(nulls_finite) + 1)
            null_mean = float(nulls_finite.mean())
            null_std = float(nulls_finite.std())
        else:
            perm_p = float("nan")
            null_mean = float("nan")
            null_std = float("nan")
    else:
        perm_p = float("nan")
        null_mean = float("nan")
        null_std = float("nan")

    return {
        "mean_auc": obs_mean,
        "perm_p": float(perm_p),
        "null_mean": null_mean,
        "null_std": null_std,
        "n_lr": int(len(per_lr)),
        "n_sig_lr": n_sig,
        "per_lr": per_lr,
    }
