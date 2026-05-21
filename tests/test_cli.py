"""Smoke tests for the CLI."""
import subprocess
import sys

import pytest


def _run_cli(*args, expect_zero=True):
    """Invoke the CLI via the module so it works without pip-install in tests."""
    cmd = [sys.executable, "-m", "spaccbench.cli", *args]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if expect_zero and result.returncode != 0:
        raise AssertionError(
            f"Command {cmd} failed (exit {result.returncode}).\n"
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
    assert "bundled" in out.stdout
    assert "stub" in out.stdout


def test_cli_list_scenarios():
    out = _run_cli("list-scenarios")
    assert "tha" in out.stdout
    assert "ctx" in out.stdout


def test_cli_info_known_scenario():
    out = _run_cli("info", "--scenario", "tha")
    assert "MERFISH" in out.stdout


def test_cli_info_unknown_scenario_exits_nonzero():
    result = _run_cli("info", "--scenario", "does_not_exist", expect_zero=False)
    assert result.returncode != 0


def test_cli_help_runs():
    result = subprocess.run(
        [sys.executable, "-m", "spaccbench.cli", "--help"],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0
    assert "evaluate" in result.stdout
    assert "list-methods" in result.stdout


def test_cli_evaluate_without_data_fails_cleanly():
    """Without bundled data, `evaluate` should fail with a clear error,
    not a stack trace from deep in pandas."""
    result = _run_cli("evaluate", "--method", "LIANA", "--scenario", "tha",
                      expect_zero=False)
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert any(token in combined for token in ["not bundled", "build_adapter_scores"])
