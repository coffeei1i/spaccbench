"""Regression tests for the public score-matrix harmonization contract."""

from types import SimpleNamespace

import pandas as pd

from manuscript_scripts.run_benchmark import _spider_path
from spaccbench.evaluate import _align_scores_to_adata
from spaccbench.harmonization import harmonize_score_matrix, normalise_lr_name


def test_normalise_lr_name_keeps_first_receptor_in_complex():
    assert normalise_lr_name("TGFB1-TGFBR1_TGFBR2") == "tgfb1-tgfbr1"
    assert normalise_lr_name("Ligand::Receptor") == "ligand-receptor"
    assert normalise_lr_name("Ligand_Receptor") == "ligand-receptor"


def test_harmonize_matrix_merges_duplicates_and_fills_unavailable_values():
    scores = pd.DataFrame(
        {
            "A_B": [1.0, None],
            "A-B": [2.0, "not-numeric"],
            "C|D": [None, 4.0],
        },
        index=["cell1", "cell2"],
    )

    result = harmonize_score_matrix(scores, cell_index=["cell1", "cell2", "cell3"])

    assert list(result.columns) == ["a-b", "c-d"]
    assert result.loc["cell1", "a-b"] == 3.0
    assert result.loc["cell2", "a-b"] == 0.0
    assert (result.loc["cell3"] == 0.0).all()


def test_evaluate_alignment_uses_public_zero_fill_contract():
    scenario = SimpleNamespace(adata=SimpleNamespace(obs_names=pd.Index(["cell1", "cell2"])))
    scores = pd.DataFrame({"A_B": [1.0]}, index=["cell1"])

    aligned = _align_scores_to_adata(scores, scenario)

    assert aligned.loc["cell2", "a-b"] == 0.0


def test_spider_path_falls_back_to_first_csv_in_matching_directory(tmp_path):
    fallback = tmp_path / "spider" / "run_CTX" / "scores.csv"
    fallback.parent.mkdir(parents=True)
    fallback.write_text("cell,a-b\nc1,1\n", encoding="utf-8")

    assert _spider_path(tmp_path, "CTX") == fallback
