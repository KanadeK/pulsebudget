from __future__ import annotations

from pulsebudget.models import (
    Budget,
    GateResult,
    LimitCheck,
    TraceAnalysis,
    TraceComparison,
)


def evaluate_analysis(analysis: TraceAnalysis, budget: Budget) -> GateResult:
    checks = _metric_checks(analysis, budget)
    regression_limit = budget.limits.max_average_regression_percent
    if regression_limit is not None:
        checks.append(
            LimitCheck(
                name="max_average_regression_percent",
                actual=None,
                limit=regression_limit,
                operator="<=",
                unit="%",
                status="not_applicable",
                reason="requires the compare command",
            )
        )
    return GateResult(
        passed=all(check.status != "fail" for check in checks), checks=tuple(checks)
    )


def evaluate_comparison(comparison: TraceComparison, budget: Budget) -> GateResult:
    checks = _metric_checks(comparison.candidate, budget)
    regression_limit = budget.limits.max_average_regression_percent
    if regression_limit is not None:
        if comparison.regression_percent is None:
            checks.append(
                LimitCheck(
                    name="max_average_regression_percent",
                    actual=None,
                    limit=regression_limit,
                    operator="<=",
                    unit="%",
                    status="fail",
                    reason="baseline average current is zero",
                )
            )
        else:
            checks.append(
                _maximum_check(
                    "max_average_regression_percent",
                    comparison.regression_percent,
                    regression_limit,
                    "%",
                )
            )
    return GateResult(
        passed=all(check.status != "fail" for check in checks), checks=tuple(checks)
    )


def _metric_checks(analysis: TraceAnalysis, budget: Budget) -> list[LimitCheck]:
    checks: list[LimitCheck] = []
    limits = budget.limits
    if limits.max_average_current_ma is not None:
        checks.append(
            _maximum_check(
                "max_average_current_ma",
                analysis.average_current_ma,
                limits.max_average_current_ma,
                "mA",
            )
        )
    if limits.max_peak_current_ma is not None:
        checks.append(
            _maximum_check(
                "max_peak_current_ma",
                analysis.peak_current_ma,
                limits.max_peak_current_ma,
                "mA",
            )
        )
    if limits.max_p95_current_ma is not None:
        checks.append(
            _maximum_check(
                "max_p95_current_ma",
                analysis.p95_current_ma,
                limits.max_p95_current_ma,
                "mA",
            )
        )
    if limits.min_estimated_runtime_hours is not None:
        assert analysis.estimated_runtime_hours is not None
        checks.append(
            _minimum_check(
                "min_estimated_runtime_hours",
                analysis.estimated_runtime_hours,
                limits.min_estimated_runtime_hours,
                "hours",
            )
        )
    return checks


def _maximum_check(name: str, actual: float, limit: float, unit: str) -> LimitCheck:
    return LimitCheck(
        name=name,
        actual=actual,
        limit=limit,
        operator="<=",
        unit=unit,
        status="pass" if actual <= limit else "fail",
    )


def _minimum_check(name: str, actual: float, limit: float, unit: str) -> LimitCheck:
    return LimitCheck(
        name=name,
        actual=actual,
        limit=limit,
        operator=">=",
        unit=unit,
        status="pass" if actual >= limit else "fail",
    )
