from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from pulsebudget.cli import main

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    return subprocess.run(
        [sys.executable, "-m", "pulsebudget", *arguments],
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def write_trace(path: Path, current_ma: float) -> None:
    path.write_text(f"time,current\n0,{current_ma}\n10,{current_ma}\n", encoding="utf-8")


def write_budget(path: Path, limits: str) -> None:
    path.write_text(
        '{"schema_version":1,"pulse_threshold_ma":10,"limits":' + limits + "}\n",
        encoding="utf-8",
    )


def test_analyze_command_passes_and_writes_all_artifacts(tmp_path: Path) -> None:
    trace = tmp_path / "trace.csv"
    budget = tmp_path / "budget.json"
    output = tmp_path / "report"
    write_trace(trace, 1)
    write_budget(budget, '{"max_average_current_ma":2}')

    result = run_cli(
        "analyze",
        str(trace),
        "--budget",
        str(budget),
        "--output",
        str(output),
    )

    assert result.returncode == 0
    assert result.stdout == "PASS: all applicable budget limits passed\n"
    assert result.stderr == ""
    assert set(path.name for path in output.iterdir()) == {
        "report.json",
        "report.md",
        "trace.svg",
    }


def test_compare_command_reports_budget_failure_with_exit_one(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.csv"
    candidate = tmp_path / "candidate.csv"
    budget = tmp_path / "budget.json"
    output = tmp_path / "report"
    write_trace(baseline, 1)
    write_trace(candidate, 2)
    write_budget(budget, '{"max_average_regression_percent":10}')

    result = run_cli(
        "compare",
        str(baseline),
        str(candidate),
        "--budget",
        str(budget),
        "--output",
        str(output),
    )

    assert result.returncode == 1
    assert result.stdout == "FAIL: one or more budget limits failed\n"
    assert result.stderr == ""
    assert (output / "comparison.svg").is_file()


def test_invalid_input_returns_two_without_reports(tmp_path: Path) -> None:
    trace = tmp_path / "trace.csv"
    budget = tmp_path / "budget.json"
    output = tmp_path / "report"
    trace.write_text("time,current\n0,1\n", encoding="utf-8")
    write_budget(budget, "{}")

    result = run_cli(
        "analyze",
        str(trace),
        "--budget",
        str(budget),
        "--output",
        str(output),
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "pulsebudget: error: trace must contain at least two samples\n"
    assert not output.exists()


def test_main_analyze_path_returns_pass(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    trace = tmp_path / "trace.csv"
    budget = tmp_path / "budget.json"
    write_trace(trace, 1)
    write_budget(budget, '{"max_average_current_ma":2}')

    result = main(
        [
            "analyze",
            str(trace),
            "--budget",
            str(budget),
            "--output",
            str(tmp_path / "report"),
        ]
    )

    assert result == 0
    assert capsys.readouterr().out == "PASS: all applicable budget limits passed\n"


def test_main_compare_path_returns_budget_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    baseline = tmp_path / "baseline.csv"
    candidate = tmp_path / "candidate.csv"
    budget = tmp_path / "budget.json"
    write_trace(baseline, 1)
    write_trace(candidate, 2)
    write_budget(budget, '{"max_average_regression_percent":10}')

    result = main(
        [
            "compare",
            str(baseline),
            str(candidate),
            "--budget",
            str(budget),
            "--output",
            str(tmp_path / "report"),
        ]
    )

    assert result == 1
    assert capsys.readouterr().out == "FAIL: one or more budget limits failed\n"


def test_main_invalid_path_returns_input_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    trace = tmp_path / "trace.csv"
    budget = tmp_path / "budget.json"
    trace.write_text("time,current\n0,1\n", encoding="utf-8")
    write_budget(budget, "{}")

    result = main(
        [
            "analyze",
            str(trace),
            "--budget",
            str(budget),
            "--output",
            str(tmp_path / "report"),
        ]
    )

    assert result == 2
    assert capsys.readouterr().err == (
        "pulsebudget: error: trace must contain at least two samples\n"
    )
