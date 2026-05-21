"""D2: expression fidelity.

Compares each method's per-cell score vector against the expression-derived
reference signal E (cells × top-25 LR) using four complementary similarity
measures: Pearson r, Spearman rho, cosine, JS divergence.
"""
from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd
from scipy.spatial.distance import jensenshannon
from scipy.stats import pearsonr, spearmanr

_EPS = 1e-12


def _normalise_lr(lr: str) -> str:
    return str(lr).strip().lower().replace("_", "-")


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na < _EPS or nb < _EPS:
        return float("nan")
    return float(np.dot(a, b) / (na * nb))


def _js_divergence(a: np.ndarray, b: np.ndarray) -> float:
    """Jensen-Shannon divergence after unit-sum normalisation (base e, squared dist)."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    a = np.clip(a, 0.0, None)
    b = np.clip(b, 0.0, None)
    sa = a.sum()
    sb = b.sum()
    if sa < _EPS or sb < _EPS:
        return float("nan")
    p = a / sa
    q = b / sb
    # scipy returns sqrt(JS divergence) — square back to recover the divergence.
    return float(jensenshannon(p, q, base=np.e) ** 2)


def _pair_metrics(m: np.ndarray, r: np.ndarray) -> dict:
    """Compute (pearson, spearman, cosine, JS) for a single LR pair."""
    mask = np.isfinite(m) & np.isfinite(r)
    if mask.sum() < 3:
        return {"pearson": np.nan, "spearman": np.nan, "cosine": np.nan, "js": np.nan}
    m = m[mask]
    r = r[mask]
    if np.std(m) < _EPS or np.std(r) < _EPS:
        pearson = float("nan")
        spearman = float("nan")
    else:
        pearson = float(pearsonr(m, r).statistic)
        spearman = float(spearmanr(m, r).statistic)
    return {
        "pearson": pearson,
        "spearman": spearman,
        "cosine": _cosine(m, r),
        "js": _js_divergence(m, r),
    }


def d2_fidelity(
    scores: pd.DataFrame,
    reference: pd.DataFrame,
    top25_lr: Iterable[str],
) -> dict:
    """Compute D2 expression fidelity across the top-25 LR list.

    Parameters
    ----------
    scores : pd.DataFrame
        Method scores (cells × LR pairs). LR columns lowercased.
    reference : pd.DataFrame
        Expression-derived reference signal E (cells × LR pairs).
        Must share cell index with ``scores``.
    top25_lr : iterable of str
        Per-sample top-25 LR list.

    Returns
    -------
    dict
        Method-level means (over LR pairs with both score and reference present):

        - ``pearson_r`` (float, higher is better)
        - ``spearman``  (float, higher is better)
        - ``cosine``    (float, higher is better)
        - ``js``        (float, lower is better)
        - ``n_lr``      (int, number of LR pairs contributing)
        - ``per_lr``    (pd.DataFrame: lr × {pearson, spearman, cosine, js})
    """
    top25 = [_normalise_lr(x) for x in top25_lr]
    score_cols = {_normalise_lr(c): c for c in scores.columns}
    ref_cols = {_normalise_lr(c): c for c in reference.columns}

    common_cells = scores.index.intersection(reference.index)
    if len(common_cells) == 0:
        raise ValueError("scores and reference have no overlapping cells")

    rows = []
    for lr in top25:
        if lr not in score_cols or lr not in ref_cols:
            continue
        m = scores.loc[common_cells, score_cols[lr]].to_numpy(dtype=float)
        r = reference.loc[common_cells, ref_cols[lr]].to_numpy(dtype=float)
        # Skip LR pairs where the method emits no signal at all.
        if not np.isfinite(m).any() or np.nanmax(np.abs(m)) < _EPS:
            continue
        metrics = _pair_metrics(m, r)
        metrics["lr"] = lr
        rows.append(metrics)

    per_lr = pd.DataFrame(rows)
    if per_lr.empty:
        return {
            "pearson_r": float("nan"),
            "spearman": float("nan"),
            "cosine": float("nan"),
            "js": float("nan"),
            "n_lr": 0,
            "per_lr": per_lr,
        }

    return {
        "pearson_r": float(per_lr["pearson"].mean(skipna=True)),
        "spearman": float(per_lr["spearman"].mean(skipna=True)),
        "cosine": float(per_lr["cosine"].mean(skipna=True)),
        "js": float(per_lr["js"].mean(skipna=True)),
        "n_lr": int(len(per_lr)),
        "per_lr": per_lr,
    }
