"""Smoke tests for the CLI."""

import subprocess
import sys

from spaccbench.cli import _summarise


def _run_cli(*args, expect_zero=True):
    """Invoke the CLI via the module so it works without pip-install in tests."""
    cmd = [sys.executable, "-m", "spaccbench.cli", *args]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if expect_zero and result.returncode != 0:
        raise AssertionError(
            f"Command {cmd} returned exit {result.returncode}.\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result


def test_cli_version():
    out = _run_cli("version")
    assert "spaccbench" in out.stdout


def test_cli_list_methods():
    out = _run_cli("list-methods")
    assert "LIANA" in out.stdout
    assert "COMMOT" in out.stdout
    assert "Spacia" in out.stdout
    assert "file-backed" in out.stdout
    assert "adapter-required" in out.stdout
    assert "No method score matrices are bundled" in out.stdout


def test_cli_list_scenarios():
    out = _run_cli("list-scenarios")
    assert "tha" in out.stdout
    assert "ctx" in out.stdout
    assert "Metadata only" in out.stdout


def test_cli_info_known_scenario():
    out = _run_cli("info", "--scenario", "tha")
    assert "MERFISH" in out.stdout


def test_cli_info_unknown_scenario_exits_nonzero():
    result = _run_cli("info", "--scenario", "does_not_exist", expect_zero=False)
    assert result.returncode != 0


def test_cli_help_runs():
    result = subprocess.run(
        [sys.executable, "-m", "spaccbench.cli", "--help"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    assert "evaluate" in result.stdout
    assert "list-methods" in result.stdout


def test_cli_evaluate_guides_score_generation():
    """The CLI provides a clear score-generation message."""
    result = _run_cli("evaluate", "--method", "LIANA", "--scenario", "tha", expect_zero=False)
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "build_scenario.py" in combined or "build_adapter_scores" in combined


def test_cli_list_methods_is_ascii_and_reports_current_status_terms():
    out = _run_cli("list-methods")
    out.stdout.encode("ascii")
    assert "file-backed" in out.stdout
    assert "adapter-required" in out.stdout


def test_cli_summary_names_auc_threshold_count_accurately():
    summary = _summarise(
        {
            "method": "Example",
            "scenario": "tha",
            "d4": {
                "mean_auc": 0.75,
                "perm_p": 0.01,
                "n_auc_above_0_6": 17,
            },
        }
    )

    assert "n_auc_above_0_6=17" in summary
    assert "n_sig_lr" not in summary
