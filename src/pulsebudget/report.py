from __future__ import annotations

import html
import json
import math
from pathlib import Path

from pulsebudget.models import (
    Budget,
    GateResult,
    Pulse,
    Trace,
    TraceAnalysis,
    TraceComparison,
)


def write_analysis_report(
    output_dir: Path,
    trace: Trace,
    analysis: TraceAnalysis,
    gate: GateResult,
    budget: Budget,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {
        "analysis": _analysis_payload(analysis),
        "budget_checks": _checks_payload(gate),
        "command": "analyze",
        "passed": gate.passed,
        "pulse_threshold_ma": budget.pulse_threshold_ma,
        "schema_version": 1,
    }
    _write_json(output_dir / "report.json", payload)
    _write_text(output_dir / "report.md", _analysis_markdown(analysis, gate))
    _write_text(
        output_dir / "trace.svg",
        _analysis_svg(trace, budget.pulse_threshold_ma, gate.passed),
    )


def write_comparison_report(
    output_dir: Path,
    baseline: Trace,
    candidate: Trace,
    comparison: TraceComparison,
    gate: GateResult,
    budget: Budget,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {
        "baseline": _analysis_payload(comparison.baseline),
        "budget_checks": _checks_payload(gate),
        "candidate": _analysis_payload(comparison.candidate),
        "command": "compare",
        "comparison": {
            "attribution": {
                "idle_drift_ma": comparison.attribution.idle_drift_ma,
                "pulse_activity_ma": comparison.attribution.pulse_activity_ma,
                "pulse_amplitude_ma": comparison.attribution.pulse_amplitude_ma,
            },
            "delta_average_current_ma": comparison.delta_average_current_ma,
            "regression_percent": comparison.regression_percent,
        },
        "passed": gate.passed,
        "pulse_threshold_ma": budget.pulse_threshold_ma,
        "schema_version": 1,
    }
    _write_json(output_dir / "report.json", payload)
    _write_text(output_dir / "report.md", _comparison_markdown(comparison, gate))
    _write_text(
        output_dir / "comparison.svg",
        _comparison_svg(
            baseline,
            candidate,
            budget.pulse_threshold_ma,
            gate.passed,
        ),
    )


def _analysis_payload(analysis: TraceAnalysis) -> dict[str, object]:
    runtime_status = "not_requested"
    runtime_hours = analysis.estimated_runtime_hours
    if runtime_hours is not None:
        runtime_status = "unbounded" if math.isinf(runtime_hours) else "estimated"
    return {
        "average_current_ma": analysis.average_current_ma,
        "charge_mah": analysis.charge_mah,
        "duration_s": analysis.duration_s,
        "estimated_runtime_hours": (
            runtime_hours if runtime_hours is not None and math.isfinite(runtime_hours) else None
        ),
        "estimated_runtime_status": runtime_status,
        "p95_current_ma": analysis.p95_current_ma,
        "peak_current_ma": analysis.peak_current_ma,
        "pulse_count": len(analysis.pulses),
        "pulse_rate_hz": analysis.pulse_rate_hz,
        "pulses": [_pulse_payload(pulse) for pulse in analysis.pulses],
        "trace_name": analysis.trace_name,
    }


def _pulse_payload(pulse: Pulse) -> dict[str, float]:
    return {
        "charge_mah": pulse.charge_mah,
        "duration_s": pulse.duration_s,
        "end_s": pulse.end_s,
        "excess_charge_mah": pulse.excess_charge_mah,
        "peak_current_ma": pulse.peak_current_ma,
        "start_s": pulse.start_s,
    }


def _checks_payload(gate: GateResult) -> list[dict[str, object]]:
    checks: list[dict[str, object]] = []
    for check in gate.checks:
        actual_status = "not_available"
        if check.actual is not None:
            actual_status = "unbounded" if math.isinf(check.actual) else "measured"
        checks.append(
            {
                "actual": (
                    check.actual
                    if check.actual is not None and math.isfinite(check.actual)
                    else None
                ),
                "actual_status": actual_status,
                "limit": check.limit,
                "name": check.name,
                "operator": check.operator,
                "reason": check.reason,
                "status": check.status,
                "unit": check.unit,
            }
        )
    return checks


def _analysis_markdown(analysis: TraceAnalysis, gate: GateResult) -> str:
    lines = [
        "# PulseBudget analysis",
        "",
        f"**{_status(gate)}** — `{_escape_text(analysis.trace_name)}`",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Duration | {_format_number(analysis.duration_s)} s |",
        f"| Charge | {_format_number(analysis.charge_mah)} mAh |",
        f"| Average current | {_format_number(analysis.average_current_ma)} mA |",
        f"| Peak current | {_format_number(analysis.peak_current_ma)} mA |",
        f"| Time-weighted p95 | {_format_number(analysis.p95_current_ma)} mA |",
        f"| Pulse count | {len(analysis.pulses)} |",
        f"| Pulse rate | {_format_number(analysis.pulse_rate_hz)} Hz |",
        f"| Estimated runtime | {_format_number(analysis.estimated_runtime_hours)} h |",
        "",
        *_checks_markdown(gate),
    ]
    return "\n".join(lines) + "\n"


def _comparison_markdown(comparison: TraceComparison, gate: GateResult) -> str:
    lines = [
        "# PulseBudget comparison",
        "",
        f"**{_status(gate)}** — `{_escape_text(comparison.baseline.trace_name)}` → "
        f"`{_escape_text(comparison.candidate.trace_name)}`",
        "",
        "## Summary",
        "",
        "| Metric | Baseline | Candidate |",
        "| --- | ---: | ---: |",
        f"| Average current | {_format_number(comparison.baseline.average_current_ma)} mA | "
        f"{_format_number(comparison.candidate.average_current_ma)} mA |",
        f"| Peak current | {_format_number(comparison.baseline.peak_current_ma)} mA | "
        f"{_format_number(comparison.candidate.peak_current_ma)} mA |",
        f"| Time-weighted p95 | {_format_number(comparison.baseline.p95_current_ma)} mA | "
        f"{_format_number(comparison.candidate.p95_current_ma)} mA |",
        f"| Pulse count | {len(comparison.baseline.pulses)} | "
        f"{len(comparison.candidate.pulses)} |",
        "",
        f"Average-current delta: **{_format_number(comparison.delta_average_current_ma)} mA**  ",
        f"Regression: **{_format_number(comparison.regression_percent)}%**",
        "",
        "## Exact attribution",
        "",
        "| Category | Contribution |",
        "| --- | ---: |",
        f"| Idle drift | {_format_number(comparison.attribution.idle_drift_ma)} mA |",
        f"| Pulse amplitude | {_format_number(comparison.attribution.pulse_amplitude_ma)} mA |",
        f"| Pulse activity/timing | "
        f"{_format_number(comparison.attribution.pulse_activity_ma)} mA |",
        "",
        *_checks_markdown(gate),
    ]
    return "\n".join(lines) + "\n"


def _checks_markdown(gate: GateResult) -> list[str]:
    lines = [
        "## Budget checks",
        "",
    ]
    if not gate.checks:
        return [*lines, "No limits configured."]
    lines.extend(
        [
            "| Limit | Actual | Rule | Status |",
            "| --- | ---: | ---: | --- |",
        ]
    )
    for check in gate.checks:
        actual = _format_number(check.actual)
        reason = f" ({_escape_text(check.reason)})" if check.reason else ""
        lines.append(
            f"| `{check.name}` | {actual} {check.unit} | {check.operator} "
            f"{_format_number(check.limit)} {check.unit} | {check.status.upper()}{reason} |"
        )
    return lines


def _analysis_svg(trace: Trace, threshold_ma: float, passed: bool) -> str:
    maximum_ma = max(
        threshold_ma,
        max(sample.current_ma for sample in trace.samples),
        1.0,
    )
    return _svg_document(
        title="PulseBudget analysis",
        subtitle=trace.name,
        passed=passed,
        maximum_ma=maximum_ma,
        threshold_ma=threshold_ma,
        polylines=[("trace", "#2563eb", _polyline(trace, maximum_ma))],
    )


def _comparison_svg(
    baseline: Trace,
    candidate: Trace,
    threshold_ma: float,
    passed: bool,
) -> str:
    maximum_ma = max(
        threshold_ma,
        max(sample.current_ma for sample in baseline.samples),
        max(sample.current_ma for sample in candidate.samples),
        1.0,
    )
    return _svg_document(
        title="PulseBudget comparison",
        subtitle=f"{baseline.name} → {candidate.name}",
        passed=passed,
        maximum_ma=maximum_ma,
        threshold_ma=threshold_ma,
        polylines=[
            ("baseline", "#64748b", _polyline(baseline, maximum_ma)),
            ("candidate", "#2563eb", _polyline(candidate, maximum_ma)),
        ],
    )


def _svg_document(
    *,
    title: str,
    subtitle: str,
    passed: bool,
    maximum_ma: float,
    threshold_ma: float,
    polylines: list[tuple[str, str, str]],
) -> str:
    threshold_y = _chart_y(threshold_ma, maximum_ma)
    status = "PASS" if passed else "FAIL"
    status_color = "#15803d" if passed else "#b91c1c"
    line_elements = "\n".join(
        f'  <polyline points="{points}" fill="none" stroke="{color}" '
        'stroke-width="3" stroke-linejoin="round" />'
        for _, color, points in reversed(polylines)
    )
    legend_elements = "\n".join(
        f'  <text x="{570 + index * 100}" y="30" fill="{color}" '
        f'font-size="13">● {_escape_text(label)}</text>'
        for index, (label, color, _) in enumerate(polylines)
    )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="300" '
        'viewBox="0 0 800 300" role="img">\n'
        f"  <title>{_escape_text(title)}: {_escape_text(subtitle)}</title>\n"
        "  <desc>Normalized current trace, pulse threshold, and budget status.</desc>\n"
        "  <rect width=\"800\" height=\"300\" fill=\"#f8fafc\" />\n"
        f'  <text x="20" y="28" fill="#0f172a" font-size="18" '
        f'font-weight="700">{_escape_text(title)}</text>\n'
        f'  <text x="20" y="48" fill="#475569" font-size="12">'
        f"{_escape_text(subtitle)}</text>\n"
        f'  <text x="500" y="29" fill="{status_color}" font-size="14" '
        f'font-weight="700">{status}</text>\n'
        f"{legend_elements}\n"
        '  <line x1="55" y1="250" x2="780" y2="250" stroke="#94a3b8" />\n'
        '  <line x1="55" y1="70" x2="55" y2="250" stroke="#94a3b8" />\n'
        f'  <line x1="55" y1="{threshold_y:.2f}" x2="780" y2="{threshold_y:.2f}" '
        'stroke="#ea580c" stroke-width="1.5" stroke-dasharray="6 5" />\n'
        f'  <text x="60" y="{threshold_y - 5:.2f}" fill="#c2410c" font-size="11">'
        f"pulse threshold {_format_number(threshold_ma)} mA</text>\n"
        f"{line_elements}\n"
        '  <text x="13" y="75" fill="#64748b" font-size="11">'
        f"{_format_number(maximum_ma)} mA</text>\n"
        '  <text x="56" y="272" fill="#64748b" font-size="11">0%</text>\n'
        '  <text x="752" y="272" fill="#64748b" font-size="11">100%</text>\n'
        "</svg>\n"
    )


def _polyline(trace: Trace, maximum_ma: float) -> str:
    start_s = trace.samples[0].time_s
    return " ".join(
        f"{55 + 725 * (sample.time_s - start_s) / trace.duration_s:.2f},"
        f"{_chart_y(sample.current_ma, maximum_ma):.2f}"
        for sample in trace.samples
    )


def _chart_y(current_ma: float, maximum_ma: float) -> float:
    return 250 - 180 * current_ma / maximum_ma


def _status(gate: GateResult) -> str:
    return "PASS" if gate.passed else "FAIL"


def _format_number(value: float | None) -> str:
    if value is None:
        return "n/a"
    if math.isinf(value):
        return "unbounded"
    return f"{value:.6g}"


def _escape_text(value: str) -> str:
    return html.escape(value.replace("\r", " ").replace("\n", " "), quote=True)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    content = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    _write_text(path, content + "\n")


def _write_text(path: Path, content: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
