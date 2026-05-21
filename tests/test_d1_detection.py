"""Unit tests for D1 detection."""
import numpy as np
import pandas as pd

from spaccbench.core import d1_detection


def test_d1_exact_count():
    scores = pd.DataFrame(
        {"lig1-rec1": [1.0, 0.0, 2.0],
         "lig2-rec2": [0.0, 0.0, 0.0],
         "lig3-rec3": [3.0, 1.0, 0.0]},
        index=["c1", "c2", "c3"],
    )
    out = d1_detection(scores, top25_lr=["lig1-rec1", "lig2-rec2", "lig3-rec3", "lig4-rec4"])
    assert out["n_hit"] == 2
    assert out["n_total"] == 4
    assert out["fraction"] == 0.5


def test_d1_normalises_underscore_and_case():
    scores = pd.DataFrame(
        {"LIG1_REC1": [1.0, 2.0]},
        index=["c1", "c2"],
    )
    out = d1_detection(scores, top25_lr=["lig1-rec1"])
    assert out["n_hit"] == 1


def test_d1_all_nan_treated_as_not_detected():
    scores = pd.DataFrame(
        {"lig1-rec1": [np.nan, np.nan]},
        index=["c1", "c2"],
    )
    out = d1_detection(scores, top25_lr=["lig1-rec1"])
    assert out["n_hit"] == 0


def test_d1_max_zero_treated_as_not_detected():
    scores = pd.DataFrame(
        {"lig1-rec1": [0.0, 0.0, 0.0]},
        index=["c1", "c2", "c3"],
    )
    out = d1_detection(scores, top25_lr=["lig1-rec1"])
    assert out["n_hit"] == 0


def test_d1_per_lr_dataframe_shape():
    scores = pd.DataFrame({"lig1-rec1": [1.0]}, index=["c1"])
    out = d1_detection(scores, top25_lr=["lig1-rec1", "lig2-rec2"])
    assert len(out["per_lr"]) == 2
    assert set(out["per_lr"].columns) == {"lr", "detected", "reason"}


def test_d1_empty_top25():
    scores = pd.DataFrame({"lig1-rec1": [1.0]}, index=["c1"])
    out = d1_detection(scores, top25_lr=[])
    assert out["n_hit"] == 0
    assert out["n_total"] == 0
    assert np.isnan(out["fraction"])
