"""D1: candidate-pair recovery.

For each pair (L, R) in the per-sample top-25 list, recovery is defined as:

    det(L, R) = 1  if  m_{L,R} is present  AND  max_i m_{L,R,i} > 0
              = 0  otherwise.

Method-level statistic is the hit count n_hit = sum det, reported as
n_hit / 25.
"""
from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd


def _normalise_lr(lr: str) -> str:
    return str(lr).strip().lower().replace("_", "-")


def d1_detection(
    scores: pd.DataFrame,
    top25_lr: Iterable[str],
) -> dict:
    """Compute D1 candidate-pair recovery.

    Parameters
    ----------
    scores : pd.DataFrame
        Per-cell LR score matrix (cells × LR pairs). Columns are LR strings.
    top25_lr : iterable of str
        The per-sample top-25 LR list (lowercased ``"ligand-receptor"`` strings).

    Returns
    -------
    dict
        Keys:

        - ``"n_hit"`` : int, number of LR pairs recovered.
        - ``"fraction"`` : float, n_hit / len(top25_lr).
        - ``"per_lr"`` : pd.DataFrame with columns ``lr``, ``detected``.
    """
    top25 = [_normalise_lr(x) for x in top25_lr]
    score_cols_norm = {_normalise_lr(c): c for c in scores.columns}

    rows = []
    for lr in top25:
        if lr not in score_cols_norm:
            rows.append({"lr": lr, "detected": 0, "reason": "not_in_output"})
            continue
        col = score_cols_norm[lr]
        vec = scores[col].to_numpy(dtype=float)
        if not np.isfinite(vec).any():
            rows.append({"lr": lr, "detected": 0, "reason": "all_nan"})
            continue
        max_val = float(np.nanmax(vec))
        if max_val > 0:
            rows.append({"lr": lr, "detected": 1, "reason": "ok"})
        else:
            rows.append({"lr": lr, "detected": 0, "reason": "max_le_zero"})

    per_lr = pd.DataFrame(rows, columns=["lr", "detected", "reason"])
    n_hit = int(per_lr["detected"].sum()) if len(per_lr) else 0
    n_total = len(top25)
    return {
        "n_hit": n_hit,
        "n_total": n_total,
        "fraction": n_hit / n_total if n_total else float("nan"),
        "per_lr": per_lr,
    }
