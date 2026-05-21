"""D3: spatial structure coherence.

Measures spatial autocorrelation of each method's score vector against a
row-normalised k-nearest-neighbour weight matrix:

- Moran's I (higher-is-better, global autocorrelation)
- Geary's C (lower-is-better, sensitive to local pairwise differences)

The kNN weight matrix uses k=6 neighbours, excluding self.
"""
from __future__ import annotations

from typing import Iterable, Tuple

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.spatial import cKDTree

_EPS = 1e-12


def _normalise_lr(lr: str) -> str:
    return str(lr).strip().lower().replace("_", "-")


def build_knn_weights(coords: np.ndarray, k: int = 6) -> csr_matrix:
    """Build a row-normalised kNN spatial weight matrix.

    Excludes self. Each row sums to 1.
    """
    coords = np.asarray(coords, dtype=float)
    n = coords.shape[0]
    tree = cKDTree(coords)
    # Query k+1 to drop self.
    _, idx = tree.query(coords, k=k + 1)
    idx = idx[:, 1:]  # drop self column
    rows = np.repeat(np.arange(n), k)
    cols = idx.reshape(-1)
    data = np.full(n * k, 1.0 / k, dtype=float)
    W = csr_matrix((data, (rows, cols)), shape=(n, n))
    return W


def morans_i(x: np.ndarray, W: csr_matrix) -> float:
    """Moran's I with a row-normalised W.

    With row-normalised W, W_0 = n, so I reduces to
    (sum_ij w_ij z_i z_j) / (sum_i z_i^2), where z = x - x_bar.
    """
    x = np.asarray(x, dtype=float)
    if not np.isfinite(x).all() or np.std(x) < _EPS:
        return float("nan")
    z = x - x.mean()
    denom = float(np.dot(z, z))
    if denom < _EPS:
        return float("nan")
    Wz = W.dot(z)
    num = float(np.dot(z, Wz))
    return num / denom


def gearys_c(x: np.ndarray, W: csr_matrix) -> float:
    """Geary's C with a row-normalised W.

    C = ((n-1) / (2 W_0)) * sum_ij w_ij (x_i - x_j)^2 / sum_i z_i^2
    """
    x = np.asarray(x, dtype=float)
    if not np.isfinite(x).all() or np.std(x) < _EPS:
        return float("nan")
    n = len(x)
    z = x - x.mean()
    denom = float(np.dot(z, z))
    if denom < _EPS:
        return float("nan")
    W_coo = W.tocoo()
    diffs2 = (x[W_coo.row] - x[W_coo.col]) ** 2
    weighted = (W_coo.data * diffs2).sum()
    W_0 = float(W_coo.data.sum())
    if W_0 < _EPS:
        return float("nan")
    return float((n - 1) / (2.0 * W_0) * weighted / denom)


def d3_spatial(
    scores: pd.DataFrame,
    coords: np.ndarray,
    top25_lr: Iterable[str],
    k: int = 6,
    W: csr_matrix | None = None,
) -> dict:
    """Compute D3 spatial autocorrelation across the top-25 LR list.

    Parameters
    ----------
    scores : pd.DataFrame
        Per-cell LR score matrix (cells × LR pairs).
    coords : np.ndarray
        Spatial coordinates, shape (n_cells, 2). Must align row-wise with
        ``scores.index``.
    top25_lr : iterable of str
        Per-sample top-25 LR list.
    k : int
        Number of neighbours for the kNN weight matrix (excludes self).
    W : csr_matrix, optional
        Pre-computed weight matrix (skips kNN construction). Caller is
        responsible for matching ``coords`` shape and row-normalisation.

    Returns
    -------
    dict with keys ``morans_i``, ``gearys_c``, ``n_lr``, ``per_lr``.
    """
    top25 = [_normalise_lr(x) for x in top25_lr]
    score_cols = {_normalise_lr(c): c for c in scores.columns}

    if W is None:
        W = build_knn_weights(coords, k=k)

    rows = []
    for lr in top25:
        if lr not in score_cols:
            continue
        x = scores[score_cols[lr]].to_numpy(dtype=float)
        if not np.isfinite(x).any() or np.nanmax(np.abs(x)) < _EPS:
            continue
        # NaN-safe: fill NaN with column mean before computing autocorrelation.
        if np.isnan(x).any():
            mean_val = np.nanmean(x)
            x = np.where(np.isnan(x), mean_val, x)
        rows.append({
            "lr": lr,
            "morans_i": morans_i(x, W),
            "gearys_c": gearys_c(x, W),
        })

    per_lr = pd.DataFrame(rows)
    if per_lr.empty:
        return {
            "morans_i": float("nan"),
            "gearys_c": float("nan"),
            "n_lr": 0,
            "per_lr": per_lr,
        }
    return {
        "morans_i": float(per_lr["morans_i"].mean(skipna=True)),
        "gearys_c": float(per_lr["gearys_c"].mean(skipna=True)),
        "n_lr": int(len(per_lr)),
        "per_lr": per_lr,
    }
