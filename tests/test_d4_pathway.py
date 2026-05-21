"""Unit tests for D4 pathway AUC and permutation."""
import numpy as np
import pandas as pd

from spaccbench.core import compute_auc, d4_pathway, receptor_to_pathways


def test_compute_auc_perfect_classifier():
    n = 100
    rng = np.random.default_rng(0)
    pathway_act = np.concatenate([np.zeros(n - 10), np.ones(10)])  # last 10 = top 10%
    lr_score = pathway_act.copy() + rng.normal(scale=1e-6, size=n)
    auc = compute_auc(lr_score, pathway_act, top_pct=0.10)
    assert auc > 0.99


def test_compute_auc_random_classifier_near_half():
    n = 200
    rng = np.random.default_rng(0)
    pathway_act = rng.uniform(size=n)
    lr_score = rng.uniform(size=n)
    auc = compute_auc(lr_score, pathway_act, top_pct=0.10)
    assert 0.3 < auc < 0.7


def test_compute_auc_constant_score_returns_nan():
    pathway_act = np.arange(100, dtype=float)
    lr_score = np.ones(100)
    auc = compute_auc(lr_score, pathway_act, top_pct=0.10)
    assert np.isnan(auc)


def test_receptor_to_pathways_truncation():
    kegg = pd.DataFrame({
        "source": [f"pw{i}" for i in range(30)],
        "target": ["Gene1"] * 30,
    })
    out = receptor_to_pathways(kegg, max_pw=20)
    assert "gene1" in out
    assert len(out["gene1"]) == 20


def test_d4_full_pipeline_simple_case():
    """Method LR score is perfectly correlated with one pathway's activity."""
    rng = np.random.default_rng(0)
    n_cells = 200
    cells = [f"c{i}" for i in range(n_cells)]

    pw_act = pd.DataFrame(
        {
            "Wnt": rng.uniform(size=n_cells),
            "BMP": rng.uniform(size=n_cells),
            "Notch": rng.uniform(size=n_cells),
        },
        index=cells,
    )
    # LR score for "lig1-rec1" = perfect copy of Wnt activity.
    scores = pd.DataFrame(
        {"lig1-rec1": pw_act["Wnt"].values},
        index=cells,
    )
    kegg = pd.DataFrame({
        "source": ["Wnt", "BMP", "Notch"],
        "target": ["Rec1", "Rec1", "Rec1"],
    })
    out = d4_pathway(
        scores=scores, pw_act=pw_act, top25_lr=["lig1-rec1"],
        kegg=kegg, n_perm=20, seed=0,
    )
    assert out["n_lr"] == 1
    assert out["mean_auc"] > 0.99  # perfect classifier


def test_d4_no_perm_returns_nan_pvalue():
    n_cells = 50
    cells = [f"c{i}" for i in range(n_cells)]
    rng = np.random.default_rng(0)
    pw_act = pd.DataFrame({"Wnt": rng.uniform(size=n_cells)}, index=cells)
    scores = pd.DataFrame({"lig1-rec1": rng.uniform(size=n_cells)}, index=cells)
    kegg = pd.DataFrame({"source": ["Wnt"], "target": ["Rec1"]})
    out = d4_pathway(scores, pw_act, ["lig1-rec1"], kegg, n_perm=0)
    assert np.isnan(out["perm_p"])
