from __future__ import annotations

from pulsebudget.analysis import analyze_trace
from pulsebudget.compare import compare_traces
from pulsebudget.gate import evaluate_analysis, evaluate_comparison
from pulsebudget.models import Battery, Budget, BudgetLimits, Sample, Trace


def constant_trace(name: str, current_ma: float) -> Trace:
    return Trace(
        name=name,
        samples=(
            Sample(time_s=0, current_ma=current_ma),
            Sample(time_s=10, current_ma=current_ma),
        ),
    )


def test_analysis_gate_reports_pass_fail_and_not_applicable_limits() -> None:
    battery = Battery(capacity_mah=100, usable_fraction=1, system_efficiency=1)
    budget = Budget(
        pulse_threshold_ma=10,
        limits=BudgetLimits(
            max_average_current_ma=2.5,
            max_peak_current_ma=3,
            max_p95_current_ma=3,
            max_average_regression_percent=5,
            min_estimated_runtime_hours=34,
        ),
        battery=battery,
    )
    analysis = analyze_trace(constant_trace("trace.csv", 3), 10, battery)

    gate = evaluate_analysis(analysis, budget)
    checks = {check.name: check for check in gate.checks}

    assert gate.passed is False
    assert checks["max_average_current_ma"].status == "fail"
    assert checks["max_peak_current_ma"].status == "pass"
    assert checks["max_p95_current_ma"].status == "pass"
    assert checks["max_average_regression_percent"].status == "not_applicable"
    assert checks["min_estimated_runtime_hours"].status == "fail"


def test_comparison_gate_applies_candidate_and_regression_limits() -> None:
    budget = Budget(
        pulse_threshold_ma=10,
        limits=BudgetLimits(
            max_average_current_ma=3,
            max_average_regression_percent=49,
        ),
        battery=None,
    )
    comparison = compare_traces(
        constant_trace("baseline.csv", 2),
        constant_trace("candidate.csv", 3),
        pulse_threshold_ma=10,
    )

    gate = evaluate_comparison(comparison, budget)
    checks = {check.name: check for check in gate.checks}

    assert gate.passed is False
    assert checks["max_average_current_ma"].status == "pass"
    assert checks["max_average_regression_percent"].actual == 50
    assert checks["max_average_regression_percent"].status == "fail"


def test_regression_limit_fails_explicitly_when_zero_baseline_is_undefined() -> None:
    budget = Budget(
        pulse_threshold_ma=10,
        limits=BudgetLimits(max_average_regression_percent=10),
        battery=None,
    )
    comparison = compare_traces(
        constant_trace("baseline.csv", 0),
        constant_trace("candidate.csv", 1),
        pulse_threshold_ma=10,
    )

    gate = evaluate_comparison(comparison, budget)

    assert gate.passed is False
    assert gate.checks[0].status == "fail"
    assert gate.checks[0].actual is None
    assert gate.checks[0].reason == "baseline average current is zero"
