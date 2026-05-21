"""Unit tests for D2 fidelity."""
import numpy as np
import pandas as pd

from spaccbench.core import d2_fidelity


def _make_pair(values_scores, values_ref):
    cells = [f"c{i}" for i in range(len(values_scores))]
    scores = pd.DataFrame({"lig1-rec1": values_scores}, index=cells)
    ref = pd.DataFrame({"lig1-rec1": values_ref}, index=cells)
    return scores, ref


def test_d2_perfect_linear():
    rng = np.random.default_rng(0)
    x = rng.uniform(0, 10, size=200)
    scores, ref = _make_pair(x, x * 2.0 + 5.0)
    out = d2_fidelity(scores, ref, top25_lr=["lig1-rec1"])
    assert abs(out["pearson_r"] - 1.0) < 1e-9
    assert abs(out["spearman"] - 1.0) < 1e-9
    # cosine: not 1 because of the offset; should still be high.
    assert out["cosine"] > 0.98


def test_d2_anti_correlated():
    x = np.linspace(0, 1, 100)
    scores, ref = _make_pair(x, -x)
    out = d2_fidelity(scores, ref, top25_lr=["lig1-rec1"])
    assert abs(out["pearson_r"] - (-1.0)) < 1e-9


def test_d2_uncorrelated_near_zero():
    rng = np.random.default_rng(0)
    scores, ref = _make_pair(rng.normal(size=500), rng.normal(size=500))
    out = d2_fidelity(scores, ref, top25_lr=["lig1-rec1"])
    assert abs(out["pearson_r"]) < 0.15


def test_d2_skips_lr_not_in_both():
    cells = [f"c{i}" for i in range(10)]
    scores = pd.DataFrame({"lig1-rec1": np.arange(10).astype(float)}, index=cells)
    ref = pd.DataFrame({"lig2-rec2": np.arange(10).astype(float)}, index=cells)
    out = d2_fidelity(scores, ref, top25_lr=["lig1-rec1", "lig2-rec2"])
    assert out["n_lr"] == 0


def test_d2_skips_all_zero_scores():
    cells = [f"c{i}" for i in range(10)]
    scores = pd.DataFrame({"lig1-rec1": np.zeros(10)}, index=cells)
    ref = pd.DataFrame({"lig1-rec1": np.arange(10).astype(float)}, index=cells)
    out = d2_fidelity(scores, ref, top25_lr=["lig1-rec1"])
    assert out["n_lr"] == 0


def test_d2_js_zero_for_identical():
    cells = [f"c{i}" for i in range(50)]
    rng = np.random.default_rng(0)
    vals = rng.uniform(0, 1, size=50)
    scores = pd.DataFrame({"lig1-rec1": vals}, index=cells)
    ref = pd.DataFrame({"lig1-rec1": vals}, index=cells)
    out = d2_fidelity(scores, ref, top25_lr=["lig1-rec1"])
    assert out["js"] < 1e-9
