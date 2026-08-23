from __future__ import annotations

import math
from bisect import bisect_right
from itertools import pairwise

from pulsebudget.analysis import analyze_trace
from pulsebudget.models import Attribution, Battery, Trace, TraceComparison


def compare_traces(
    baseline: Trace,
    candidate: Trace,
    pulse_threshold_ma: float,
    battery: Battery | None = None,
) -> TraceComparison:
    baseline_analysis = analyze_trace(baseline, pulse_threshold_ma, battery)
    candidate_analysis = analyze_trace(candidate, pulse_threshold_ma, battery)
    delta_average_current_ma = (
        candidate_analysis.average_current_ma - baseline_analysis.average_current_ma
    )

    breakpoints = sorted(
        _normalized_breakpoints(baseline, pulse_threshold_ma)
        | _normalized_breakpoints(candidate, pulse_threshold_ma)
    )
    idle_drift_ma = 0.0
    pulse_amplitude_ma = 0.0
    pulse_activity_ma = 0.0

    for left, right in pairwise(breakpoints):
        baseline_left = _current_at(baseline, left)
        baseline_right = _current_at(baseline, right)
        candidate_left = _current_at(candidate, left)
        candidate_right = _current_at(candidate, right)
        contribution_ma = (
            (candidate_left - baseline_left)
            + (candidate_right - baseline_right)
        ) * 0.5 * (right - left)

        middle = (left + right) * 0.5
        baseline_is_pulse = _current_at(baseline, middle) > pulse_threshold_ma
        candidate_is_pulse = _current_at(candidate, middle) > pulse_threshold_ma
        if baseline_is_pulse and candidate_is_pulse:
            pulse_amplitude_ma += contribution_ma
        elif baseline_is_pulse or candidate_is_pulse:
            pulse_activity_ma += contribution_ma
        else:
            idle_drift_ma += contribution_ma

    attributed_delta_ma = idle_drift_ma + pulse_amplitude_ma + pulse_activity_ma
    if not math.isclose(
        attributed_delta_ma,
        delta_average_current_ma,
        rel_tol=1e-10,
        abs_tol=1e-10,
    ):
        raise AssertionError("attribution does not sum to the observed average-current delta")

    regression_percent = None
    if baseline_analysis.average_current_ma != 0:
        regression_percent = (
            delta_average_current_ma / baseline_analysis.average_current_ma * 100
        )

    return TraceComparison(
        baseline=baseline_analysis,
        candidate=candidate_analysis,
        delta_average_current_ma=delta_average_current_ma,
        regression_percent=regression_percent,
        attribution=Attribution(
            idle_drift_ma=idle_drift_ma,
            pulse_amplitude_ma=pulse_amplitude_ma,
            pulse_activity_ma=pulse_activity_ma,
        ),
    )


def _normalized_breakpoints(trace: Trace, threshold_ma: float) -> set[float]:
    start_s = trace.samples[0].time_s
    duration_s = trace.duration_s
    breakpoints = {
        (sample.time_s - start_s) / duration_s for sample in trace.samples
    }
    for left, right in pairwise(trace.samples):
        left_delta = left.current_ma - threshold_ma
        right_delta = right.current_ma - threshold_ma
        if left_delta * right_delta < 0:
            fraction = (threshold_ma - left.current_ma) / (
                right.current_ma - left.current_ma
            )
            crossing_s = left.time_s + fraction * (right.time_s - left.time_s)
            breakpoints.add((crossing_s - start_s) / duration_s)
    return breakpoints


def _current_at(trace: Trace, normalized_time: float) -> float:
    start_s = trace.samples[0].time_s
    target_s = start_s + normalized_time * trace.duration_s
    times = tuple(sample.time_s for sample in trace.samples)
    left_index = min(bisect_right(times, target_s) - 1, len(trace.samples) - 2)
    left = trace.samples[left_index]
    right = trace.samples[left_index + 1]
    fraction = (target_s - left.time_s) / (right.time_s - left.time_s)
    return left.current_ma + fraction * (right.current_ma - left.current_ma)
