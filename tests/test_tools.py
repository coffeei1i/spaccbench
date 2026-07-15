"""Smoke tests for public data-preparation entry points and documentation."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

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
