"""Regression tests for public manuscript metadata."""
from pathlib import Path


TITLE = (
    "SpaCCBench: a scenario-aware four-dimensional benchmark for "
    "spatial cell-cell communication"
)
AUTHORS = ["Yiheng Xu", "Zimu Zhang", "Shuqi Liu", "Xiao-Ming Li", "Bin Yu"]


def test_public_metadata_matches_final_manuscript():
    combined = "\n".join(
        Path(name).read_text(encoding="utf-8")
        for name in ["README.md", "CITATION.cff", "pyproject.toml"]
    )
    assert TITLE in combined
    for author in AUTHORS:
        assert author in combined
    assert "Xiaolan Xie" not in combined
    assert "Xie, Xiaolan" not in combined
