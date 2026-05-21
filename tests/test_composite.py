"""Unit tests for rank scoring and geometric-mean composite."""
import numpy as np
import pandas as pd

from spaccbench.core import composite_geo, composite_table, rank_score


def test_rank_score_high_direction():
    s = pd.Series({"A": 0.9, "B": 0.5, "C": 0.1})
    out = rank_score(s, direction="high")
    # N=3: best = 3/3 = 1, worst = 1/3
    assert out["A"] == 1.0
    assert out["C"] == 1 / 3


def test_rank_score_low_direction():
    s = pd.Series({"A": 0.1, "B": 0.5, "C": 0.9})  # low = better
    out = rank_score(s, direction="low")
    assert out["A"] == 1.0
    assert out["C"] == 1 / 3


def test_rank_score_handles_nan():
    s = pd.Series({"A": 0.9, "B": np.nan, "C": 0.1})
    out = rank_score(s, direction="high")
    # NaN goes to bottom rank.
    assert out["A"] == 1.0
    assert out["B"] == 1 / 3
    assert out["C"] == 2 / 3


def test_composite_geo_uniform_input():
    # All 4 dims = 0.5  →  geo mean = 0.5
    assert abs(composite_geo({"d1": 0.5, "d2": 0.5, "d3": 0.5, "d4": 0.5}) - 0.5) < 1e-12


def test_composite_geo_penalises_uneven():
    # Geo mean of (1, 1, 1, 0.1) is much lower than arithmetic mean.
    geo = composite_geo({"d1": 1.0, "d2": 1.0, "d3": 1.0, "d4": 0.1})
    assert geo < 0.6  # geo = (1*1*1*0.1)^(1/4) ≈ 0.5623


def test_composite_geo_returns_nan_for_zero():
    assert np.isnan(composite_geo({"d1": 0.0, "d2": 0.5, "d3": 0.5, "d4": 0.5}))


def test_composite_table_end_to_end():
    df = pd.DataFrame({
        "d1_fraction":   [0.9, 0.5, 0.1],
        "d2_pearson_r":  [0.8, 0.4, 0.2],
        "d3_morans_i":   [0.7, 0.5, 0.3],
        "d4_mean_auc":   [0.7, 0.6, 0.4],
    }, index=["A", "B", "C"])
    out = composite_table(df)
    assert "s_d1_fraction" in out.columns
    assert "composite_geo" in out.columns
    # A is best everywhere → highest composite.
    assert out.loc["A", "composite_geo"] > out.loc["B", "composite_geo"]
    assert out.loc["B", "composite_geo"] > out.loc["C", "composite_geo"]
