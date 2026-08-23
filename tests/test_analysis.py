from __future__ import annotations

import math

import pytest

from pulsebudget.analysis import (
    analyze_trace,
    find_pulses,
    integrate_charge_mas,
    time_weighted_quantile,
)
from pulsebudget.models import Battery, Sample, Trace


def make_trace(*points: tuple[float, float]) -> Trace:
    return Trace(
        name="fixture.csv",
        samples=tuple(
            Sample(time_s=time_s, current_ma=current_ma) for time_s, current_ma in points
        ),
    )


def test_integrate_charge_uses_real_irregular_intervals() -> None:
    trace = make_trace((0, 0), (1, 2), (3, 2))

    charge_mas = integrate_charge_mas(trace.samples)

    assert charge_mas == pytest.approx(5.0)


def test_time_weighted_p95_is_not_biased_by_row_count() -> None:
    trace = make_trace((0, 0), (99, 0), (100, 100))

    p95_ma = time_weighted_quantile(trace.samples, 0.95)

    assert p95_ma == pytest.approx(0.0, abs=1e-9)


def test_find_pulses_interpolates_threshold_crossings() -> None:
    trace = make_trace((0, 0), (1, 20), (2, 20), (3, 0))

    pulses = find_pulses(trace, threshold_ma=10)

    assert len(pulses) == 1
    assert pulses[0].start_s == pytest.approx(0.5)
    assert pulses[0].end_s == pytest.approx(2.5)
    assert pulses[0].duration_s == pytest.approx(2.0)
    assert pulses[0].charge_mah == pytest.approx(35 / 3600)
    assert pulses[0].excess_charge_mah == pytest.approx(15 / 3600)
    assert pulses[0].peak_current_ma == pytest.approx(20.0)


def test_analyze_trace_reports_metrics_and_runtime() -> None:
    trace = make_trace((10, 2), (20, 2))
    battery = Battery(capacity_mah=1000, usable_fraction=0.8, system_efficiency=0.9)

    analysis = analyze_trace(trace, pulse_threshold_ma=10, battery=battery)

    assert analysis.duration_s == pytest.approx(10.0)
    assert analysis.charge_mah == pytest.approx(20 / 3600)
    assert analysis.average_current_ma == pytest.approx(2.0)
    assert analysis.peak_current_ma == pytest.approx(2.0)
    assert analysis.p95_current_ma == pytest.approx(2.0)
    assert analysis.pulses == ()
    assert analysis.estimated_runtime_hours == pytest.approx(360.0)


def test_analyze_zero_current_has_unbounded_ideal_runtime() -> None:
    trace = make_trace((0, 0), (10, 0))
    battery = Battery(capacity_mah=1000, usable_fraction=0.8, system_efficiency=0.9)

    analysis = analyze_trace(trace, pulse_threshold_ma=10, battery=battery)

    assert math.isinf(analysis.estimated_runtime_hours or 0)
