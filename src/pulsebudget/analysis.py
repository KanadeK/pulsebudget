from __future__ import annotations

import math
from itertools import pairwise

from pulsebudget.models import Battery, Pulse, Sample, Trace, TraceAnalysis


def integrate_charge_mas(samples: tuple[Sample, ...]) -> float:
    return sum(
        (left.current_ma + right.current_ma)
        * 0.5
        * (right.time_s - left.time_s)
        for left, right in pairwise(samples)
    )


def time_weighted_quantile(samples: tuple[Sample, ...], quantile: float) -> float:
    minimum = min(sample.current_ma for sample in samples)
    maximum = max(sample.current_ma for sample in samples)
    if minimum == maximum:
        return minimum

    duration_s = samples[-1].time_s - samples[0].time_s
    target_s = duration_s * quantile
    if _duration_at_or_below(samples, minimum) >= target_s:
        return minimum

    low = minimum
    high = maximum
    for _ in range(80):
        middle = (low + high) * 0.5
        if _duration_at_or_below(samples, middle) >= target_s:
            high = middle
        else:
            low = middle
    return high


def find_pulses(trace: Trace, threshold_ma: float) -> tuple[Pulse, ...]:
    points = _insert_threshold_crossings(trace.samples, threshold_ma)
    pulses: list[Pulse] = []
    start_s: float | None = None
    end_s = 0.0
    charge_mas = 0.0
    excess_charge_mas = 0.0
    peak_current_ma = 0.0

    for left, right in pairwise(points):
        is_above = (left.current_ma + right.current_ma) * 0.5 > threshold_ma
        if is_above:
            if start_s is None:
                start_s = left.time_s
                peak_current_ma = max(left.current_ma, right.current_ma)
            end_s = right.time_s
            duration_s = right.time_s - left.time_s
            charge_mas += (left.current_ma + right.current_ma) * 0.5 * duration_s
            excess_charge_mas += (
                max(0.0, left.current_ma - threshold_ma)
                + max(0.0, right.current_ma - threshold_ma)
            ) * 0.5 * duration_s
            peak_current_ma = max(peak_current_ma, left.current_ma, right.current_ma)
        elif start_s is not None:
            pulses.append(
                _make_pulse(
                    start_s,
                    end_s,
                    charge_mas,
                    excess_charge_mas,
                    peak_current_ma,
                )
            )
            start_s = None
            charge_mas = 0.0
            excess_charge_mas = 0.0
            peak_current_ma = 0.0

    if start_s is not None:
        pulses.append(
            _make_pulse(
                start_s,
                end_s,
                charge_mas,
                excess_charge_mas,
                peak_current_ma,
            )
        )
    return tuple(pulses)


def analyze_trace(
    trace: Trace, pulse_threshold_ma: float, battery: Battery | None = None
) -> TraceAnalysis:
    charge_mas = integrate_charge_mas(trace.samples)
    average_current_ma = charge_mas / trace.duration_s
    pulses = find_pulses(trace, pulse_threshold_ma)
    estimated_runtime_hours: float | None = None
    if battery is not None:
        if average_current_ma == 0:
            estimated_runtime_hours = math.inf
        else:
            estimated_runtime_hours = (
                battery.capacity_mah
                * battery.usable_fraction
                * battery.system_efficiency
                / average_current_ma
            )
    return TraceAnalysis(
        trace_name=trace.name,
        duration_s=trace.duration_s,
        charge_mah=charge_mas / 3600,
        average_current_ma=average_current_ma,
        peak_current_ma=max(sample.current_ma for sample in trace.samples),
        p95_current_ma=time_weighted_quantile(trace.samples, 0.95),
        pulses=pulses,
        pulse_rate_hz=len(pulses) / trace.duration_s,
        estimated_runtime_hours=estimated_runtime_hours,
    )


def _duration_at_or_below(samples: tuple[Sample, ...], current_ma: float) -> float:
    duration_s = 0.0
    for left, right in pairwise(samples):
        interval_s = right.time_s - left.time_s
        low = min(left.current_ma, right.current_ma)
        high = max(left.current_ma, right.current_ma)
        if current_ma >= high:
            duration_s += interval_s
        elif current_ma > low:
            duration_s += interval_s * (current_ma - low) / (high - low)
        elif current_ma == low and low == high:
            duration_s += interval_s
    return duration_s


def _insert_threshold_crossings(
    samples: tuple[Sample, ...], threshold_ma: float
) -> tuple[Sample, ...]:
    points = [samples[0]]
    for left, right in pairwise(samples):
        left_delta = left.current_ma - threshold_ma
        right_delta = right.current_ma - threshold_ma
        if left_delta * right_delta < 0:
            fraction = (threshold_ma - left.current_ma) / (right.current_ma - left.current_ma)
            points.append(
                Sample(
                    time_s=left.time_s + fraction * (right.time_s - left.time_s),
                    current_ma=threshold_ma,
                )
            )
        points.append(right)
    return tuple(points)


def _make_pulse(
    start_s: float,
    end_s: float,
    charge_mas: float,
    excess_charge_mas: float,
    peak_current_ma: float,
) -> Pulse:
    return Pulse(
        start_s=start_s,
        end_s=end_s,
        duration_s=end_s - start_s,
        charge_mah=charge_mas / 3600,
        excess_charge_mah=excess_charge_mas / 3600,
        peak_current_ma=peak_current_ma,
    )
