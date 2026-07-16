"""Smoke tests for public data-preparation entry points and documentation."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "script",
    [
        "tools/build_scenario.py",
        "tools/build_adapter_scores.py",
        "manuscript_scripts/run_benchmark.py",
    ],
)
def test_public_scripts_expose_help(script):
    result = subprocess.run(
        [sys.executable, script, "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout.lower()


def test_tools_readme_uses_real_cli_options_and_local_data_boundary():
    text = (ROOT / "tools" / "README.md").read_text(encoding="utf-8")

    assert "--input-csv" in text
    assert "--output-dir" in text
    assert "--raw " not in text
    assert "../sup/" not in text
    assert "outside Git" in text


def test_parquet_and_pathway_extras_are_declared():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert "data = [" in text
    assert '"pyarrow>=10"' in text
    assert '"decoupler>=1.9,<2"' in text


def test_result_examples_use_one_unambiguous_metric_schema():
    expected_columns = [
        "display",
        "d1_raw",
        "d2_raw",
        "d3_raw",
        "d4_raw",
        "d1_rank_score",
        "d2_rank_score",
        "d3_rank_score",
        "d4_rank_score",
        "composite_geo",
    ]

    for filename in (
        "THA_method_scores.csv",
        "CTX_method_scores.csv",
    ):
        table = pd.read_csv(ROOT / "examples" / "results" / filename)

        assert list(table.columns) == expected_columns
        assert len(table) == 10
        assert table["display"].is_unique
