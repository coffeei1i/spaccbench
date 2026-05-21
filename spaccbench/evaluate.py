"""Top-level ``evaluate`` entry point.

Orchestrates D1-D4 evaluation for a single (method, scenario) pair and
returns a nested result dict including the geometric-mean composite.
"""
from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd

from spaccbench.adapters import BaseAdapter, get_adapter
from spaccbench.core import (
    METRIC_DIRECTION,
    composite_geo,
    d1_detection,
    d2_fidelity,
    d3_spatial,
    d4_pathway,
    rank_score,
)
from spaccbench.scenarios import Scenario, load_scenario

DEFAULT_DIMS = ("d1", "d2", "d3", "d4")


def evaluate(
    method: str | BaseAdapter,
    scenario: str | Scenario,
    dimensions: Iterable[str] = DEFAULT_DIMS,
    n_perm: int = 200,
    seed: int = 0,
    return_per_lr: bool = True,
) -> dict:
    """Evaluate a method on a scenario along the requested dimensions.

    Parameters
    ----------
    method : str or BaseAdapter
        Method name (looked up via ``get_adapter``) or an adapter instance.
    scenario : str or Scenario
        Scenario name (e.g. ``"tha"``) or a loaded ``Scenario`` instance.
    dimensions : iterable of str
        Subset of {"d1", "d2", "d3", "d4"}.
    n_perm : int
        Permutations for D4 (0 to skip).
    seed : int
        RNG seed for permutation.
    return_per_lr : bool
        Whether to include ``per_lr`` DataFrames in the output.

    Returns
    -------
    dict
        Nested results with keys ``method``, ``scenario``, ``d1``..``d4``,
        ``composite_geo``.
    """
    # Resolve adapter
    if isinstance(method, BaseAdapter):
        adapter = method
        method_name = adapter.name
    else:
        adapter = get_adapter(method)
        method_name = adapter.name

    # Resolve scenario
    if isinstance(scenario, Scenario):
        scn = scenario
    else:
        scn = load_scenario(scenario)

    dims = {d.lower() for d in dimensions}
    if not dims.issubset({"d1", "d2", "d3", "d4"}):
        raise ValueError(
            f"dimensions must be subset of {{d1, d2, d3, d4}}, got {dimensions}"
        )

    # Adapter -> per-cell LR matrix
    raw_scores = adapter.load_scores(scn.name)
    scores = _align_scores_to_adata(raw_scores, scn)

    result: dict = {
        "method": method_name,
        "scenario": scn.name,
    }

    # D1
    if "d1" in dims:
        result["d1"] = d1_detection(scores, scn.top25_lr)
        if not return_per_lr:
            result["d1"].pop("per_lr", None)

    # D2
    if "d2" in dims:
        result["d2"] = d2_fidelity(scores, scn.gt_signal, scn.top25_lr)
        if not return_per_lr:
            result["d2"].pop("per_lr", None)

    # D3
    if "d3" in dims:
        result["d3"] = d3_spatial(
            scores, scn.coords, scn.top25_lr, k=6,
        )
        if not return_per_lr:
            result["d3"].pop("per_lr", None)

    # D4
    if "d4" in dims:
        result["d4"] = d4_pathway(
            scores=scores,
            pw_act=scn.pw_act,
            top25_lr=scn.top25_lr,
            kegg=scn.kegg,
            n_perm=n_perm,
            seed=seed,
        )
        if not return_per_lr:
            result["d4"].pop("per_lr", None)

    # Composite (only meaningful when single method ranked against itself
    # produces NaN — composite_geo expects pre-ranked scores from a method
    # cohort. For single-method evaluate() we report None and let
    # tools/compose_results.py compute the cohort-level composite.)
    result["composite_geo"] = None

    return result


def _align_scores_to_adata(scores: pd.DataFrame, scn: Scenario) -> pd.DataFrame:
    """Reindex score rows to match ``scn.adata.obs_names``.

    Cells present in adata but missing from scores get all-NaN rows.
    Cells in scores not in adata are dropped.
    """
    obs_names = scn.adata.obs_names.astype(str)
    score_index = scores.index.astype(str)
    scores = scores.copy()
    scores.index = score_index
    aligned = scores.reindex(obs_names)
    return aligned


# ----- Cohort-level composite -------------------------------------------------

def compose_cohort(results: list[dict]) -> pd.DataFrame:
    """Combine per-method ``evaluate()`` results into a cohort table with
    rank scores and geometric-mean composite.

    Parameters
    ----------
    results : list of dict
        Outputs of ``evaluate``, one per method, all on the same scenario.

    Returns
    -------
    pd.DataFrame
        Index = method name. Columns include the raw metrics, rank scores
        (prefixed ``s_``), and ``composite_geo``.
    """
    if not results:
        return pd.DataFrame()

    rows = []
    for r in results:
        row = {"method": r["method"]}
        if "d1" in r:
            row["d1_fraction"] = r["d1"]["fraction"]
        if "d2" in r:
            row["d2_pearson_r"] = r["d2"]["pearson_r"]
            row["d2_spearman"] = r["d2"]["spearman"]
            row["d2_cosine"] = r["d2"]["cosine"]
            row["d2_js"] = r["d2"]["js"]
        if "d3" in r:
            row["d3_morans_i"] = r["d3"]["morans_i"]
            row["d3_gearys_c"] = r["d3"]["gearys_c"]
        if "d4" in r:
            row["d4_mean_auc"] = r["d4"]["mean_auc"]
        rows.append(row)
    df = pd.DataFrame(rows).set_index("method")

    # Compute rank scores per metric, then composite over main D-axes.
    rank_cols = []
    for col, direction in METRIC_DIRECTION.items():
        if col not in df.columns:
            continue
        s_col = f"s_{col}"
        df[s_col] = rank_score(df[col], direction=direction)
        rank_cols.append(s_col)

    main = [c for c in ["s_d1_fraction", "s_d2_pearson_r",
                         "s_d3_morans_i", "s_d4_mean_auc"]
            if c in rank_cols]
    if main:
        df["composite_geo"] = df[main].apply(
            lambda row: composite_geo(row), axis=1
        )
    return df
