from __future__ import annotations

import pytest

from pulsebudget.compare import compare_traces
from pulsebudget.models import Sample, Trace


def make_trace(name: str, *points: tuple[float, float]) -> Trace:
    return Trace(
        name=name,
        samples=tuple(
            Sample(time_s=time_s, current_ma=current_ma) for time_s, current_ma in points
        ),
    )


def test_compare_constant_traces_attributes_delta_to_idle() -> None:
    baseline = make_trace("baseline.csv", (0, 2), (10, 2))
    candidate = make_trace("candidate.csv", (0, 3), (100, 3))

    comparison = compare_traces(baseline, candidate, pulse_threshold_ma=10)

    assert comparison.delta_average_current_ma == pytest.approx(1.0)
    assert comparison.regression_percent == pytest.approx(50.0)
    assert comparison.attribution.idle_drift_ma == pytest.approx(1.0)
    assert comparison.attribution.pulse_amplitude_ma == pytest.approx(0.0)
    assert comparison.attribution.pulse_activity_ma == pytest.approx(0.0)


def test_compare_partitions_every_delta_into_exactly_one_category() -> None:
    baseline = make_trace(
        "baseline.csv",
        (0, 2),
        (1, 2),
        (1.001, 20),
        (2, 20),
        (2.001, 2),
        (3, 2),
    )
    candidate = make_trace(
        "candidate.csv",
        (0, 4),
        (1, 4),
        (1.001, 24),
        (1.5, 24),
        (1.501, 4),
        (3, 4),
    )

    comparison = compare_traces(baseline, candidate, pulse_threshold_ma=10)
    attribution = comparison.attribution

    assert attribution.idle_drift_ma > 0
    assert attribution.pulse_amplitude_ma > 0
    assert attribution.pulse_activity_ma < 0
    assert (
        attribution.idle_drift_ma
        + attribution.pulse_amplitude_ma
        + attribution.pulse_activity_ma
    ) == pytest.approx(comparison.delta_average_current_ma, abs=1e-10)
    assert len(comparison.baseline.pulses) == 1
    assert len(comparison.candidate.pulses) == 1
    assert comparison.baseline.pulse_rate_hz == pytest.approx(1 / 3)
    assert comparison.candidate.pulse_rate_hz == pytest.approx(1 / 3)


def test_compare_reports_undefined_percent_when_baseline_is_zero() -> None:
    baseline = make_trace("baseline.csv", (0, 0), (1, 0))
    candidate = make_trace("candidate.csv", (0, 1), (1, 1))

    comparison = compare_traces(baseline, candidate, pulse_threshold_ma=10)

    assert comparison.delta_average_current_ma == pytest.approx(1.0)
    assert comparison.regression_percent is None
