from __future__ import annotations

import json
from pathlib import Path

from pulsebudget.analysis import analyze_trace
from pulsebudget.compare import compare_traces
from pulsebudget.gate import evaluate_analysis, evaluate_comparison
from pulsebudget.models import Battery, Budget, BudgetLimits, Sample, Trace
from pulsebudget.report import write_analysis_report, write_comparison_report


def make_trace(name: str, current_ma: float) -> Trace:
    return Trace(
        name=name,
        samples=(
            Sample(time_s=0, current_ma=current_ma),
            Sample(time_s=10, current_ma=current_ma),
        ),
    )


def test_analysis_report_is_deterministic_escaped_and_strict_json(tmp_path: Path) -> None:
    trace = make_trace("<script>alert(1)</script>.csv", 0)
    battery = Battery(capacity_mah=100, usable_fraction=1, system_efficiency=1)
    budget = Budget(
        pulse_threshold_ma=10,
        limits=BudgetLimits(min_estimated_runtime_hours=1),
        battery=battery,
    )
    analysis = analyze_trace(trace, budget.pulse_threshold_ma, battery)
    gate = evaluate_analysis(analysis, budget)

    write_analysis_report(tmp_path, trace, analysis, gate, budget)
    first = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    write_analysis_report(tmp_path, trace, analysis, gate, budget)
    second = {path.name: path.read_bytes() for path in tmp_path.iterdir()}

    assert first == second
    assert set(first) == {"report.json", "report.md", "trace.svg"}
    payload = json.loads(first["report.json"])
    assert payload["analysis"]["estimated_runtime_hours"] is None
    assert payload["analysis"]["estimated_runtime_status"] == "unbounded"
    assert b'"passed": true' in first["report.json"]
    assert b"<script>" not in first["report.md"]
    assert b"<script>" not in first["trace.svg"]
    assert b"&lt;script&gt;" in first["trace.svg"]


def test_comparison_report_contains_exact_attribution(tmp_path: Path) -> None:
    baseline = make_trace("baseline.csv", 2)
    candidate = make_trace("candidate.csv", 3)
    budget = Budget(
        pulse_threshold_ma=10,
        limits=BudgetLimits(max_average_regression_percent=60),
        battery=None,
    )
    comparison = compare_traces(baseline, candidate, budget.pulse_threshold_ma)
    gate = evaluate_comparison(comparison, budget)

    write_comparison_report(tmp_path, baseline, candidate, comparison, gate, budget)

    payload = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert set(path.name for path in tmp_path.iterdir()) == {
        "report.json",
        "report.md",
        "comparison.svg",
    }
    assert payload["command"] == "compare"
    assert payload["comparison"]["delta_average_current_ma"] == 1
    assert payload["comparison"]["attribution"] == {
        "idle_drift_ma": 1,
        "pulse_activity_ma": 0,
        "pulse_amplitude_ma": 0,
    }
