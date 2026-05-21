"""Cross-dimensional integration.

A method is considered globally strong only if it performs well across all
four dimensions. For each metric we compute rank-normalised scores
s_d(m) = (N - rank(m, d) + 1) / N with N=10, and aggregate via the geometric
mean to penalise uneven performance.
"""
from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd

# Which direction is "better" for each metric.
METRIC_DIRECTION = {
    "d1_fraction":   "high",
    "d2_pearson_r":  "high",
    "d2_spearman":   "high",
    "d2_cosine":     "high",
    "d2_js":         "low",   # JS divergence: lower is better
    "d3_morans_i":   "high",
    "d3_gearys_c":   "low",   # Geary's C: lower is better
    "d4_mean_auc":   "high",
}


def rank_score(values: pd.Series, direction: str = "high") -> pd.Series:
    """Compute rank-normalised score in (0, 1], 1 = best.

    Parameters
    ----------
    values : pd.Series
        Raw metric values (NaN allowed; NaN gets the worst rank).
    direction : {"high", "low"}
        Whether higher or lower values are better.

    Returns
    -------
    pd.Series
        Rank score = (N - rank + 1) / N with 1 = best, 1/N = worst.
    """
    if direction not in {"high", "low"}:
        raise ValueError(f"direction must be 'high' or 'low', got {direction!r}")
    ascending = direction == "low"
    n = len(values)
    if n == 0:
        return values.copy()
    ranks = values.rank(method="min", ascending=ascending, na_option="bottom")
    return (n - ranks + 1) / n


def composite_geo(rank_scores: Mapping[str, float] | pd.Series) -> float:
    """Geometric mean of per-dimension rank scores.

    Parameters
    ----------
    rank_scores : mapping of dim_name -> rank_score in (0, 1].
        Typically 4 entries (one per D1-D4). Each value must be > 0
        (handled by the >= 1/N construction).

    Returns
    -------
    float
        Geometric mean. Returns NaN if any input is non-positive or NaN.
    """
    if isinstance(rank_scores, pd.Series):
        vals = rank_scores.to_numpy(dtype=float)
    else:
        vals = np.asarray(list(rank_scores.values()), dtype=float)
    if not np.isfinite(vals).all() or (vals <= 0).any():
        return float("nan")
    return float(np.exp(np.log(vals).mean()))


def composite_table(method_metrics: pd.DataFrame) -> pd.DataFrame:
    """Build a methods × dimensions composite table.

    Parameters
    ----------
    method_metrics : pd.DataFrame
        Index = method names. Columns = metric names matching keys in
        ``METRIC_DIRECTION`` (e.g. ``d1_fraction``, ``d2_pearson_r``,
        ``d3_morans_i``, ``d4_mean_auc``).

    Returns
    -------
    pd.DataFrame
        Original columns + ``s_<col>`` rank-score columns + ``composite_geo``.

        Missing metric columns are skipped (so callers can pass any subset).
    """
    df = method_metrics.copy()
    rank_cols: list[str] = []
    for col, direction in METRIC_DIRECTION.items():
        if col not in df.columns:
            continue
        s_col = f"s_{col}"
        df[s_col] = rank_score(df[col], direction=direction)
        rank_cols.append(s_col)

    if rank_cols:
        # Default composite uses the four "main" rank scores (one per D-axis).
        # Caller can pick any subset via composite_geo().
        main_dims = [c for c in ["s_d1_fraction", "s_d2_pearson_r",
                                  "s_d3_morans_i", "s_d4_mean_auc"]
                     if c in rank_cols]
        if main_dims:
            df["composite_geo"] = df[main_dims].apply(
                lambda row: composite_geo(row), axis=1
            )
    return df
