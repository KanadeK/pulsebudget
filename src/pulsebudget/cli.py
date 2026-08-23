from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from pulsebudget import __version__
from pulsebudget.analysis import analyze_trace
from pulsebudget.compare import compare_traces
from pulsebudget.errors import InputError
from pulsebudget.gate import evaluate_analysis, evaluate_comparison
from pulsebudget.io import CsvOptions, CurrentUnit, TimeUnit, load_budget, load_trace
from pulsebudget.report import write_analysis_report, write_comparison_report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pulsebudget",
        description="Explain and gate embedded current-trace regressions.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze", help="analyze one current trace")
    analyze_parser.add_argument("trace")
    _add_common_options(analyze_parser)

    compare_parser = subparsers.add_parser("compare", help="compare baseline and candidate traces")
    compare_parser.add_argument("baseline")
    compare_parser.add_argument("candidate")
    _add_common_options(compare_parser)

    arguments = parser.parse_args(argv)
    try:
        budget = load_budget(Path(cast(str, arguments.budget)))
        options = CsvOptions(
            time_column=cast(str, arguments.time_column),
            current_column=cast(str, arguments.current_column),
            time_unit=cast(TimeUnit, arguments.time_unit),
            current_unit=cast(CurrentUnit, arguments.current_unit),
        )
        output_dir = Path(cast(str, arguments.output))
        command = cast(str, arguments.command)
        if command == "analyze":
            trace = load_trace(Path(cast(str, arguments.trace)), options)
            analysis = analyze_trace(trace, budget.pulse_threshold_ma, budget.battery)
            gate = evaluate_analysis(analysis, budget)
            write_analysis_report(output_dir, trace, analysis, gate, budget)
        else:
            baseline = load_trace(Path(cast(str, arguments.baseline)), options)
            candidate = load_trace(Path(cast(str, arguments.candidate)), options)
            comparison = compare_traces(
                baseline,
                candidate,
                budget.pulse_threshold_ma,
                budget.battery,
            )
            gate = evaluate_comparison(comparison, budget)
            write_comparison_report(
                output_dir,
                baseline,
                candidate,
                comparison,
                gate,
                budget,
            )
    except (InputError, OSError) as error:
        print(f"pulsebudget: error: {error}", file=sys.stderr)
        return 2

    if gate.passed:
        print("PASS: all applicable budget limits passed")
        return 0
    print("FAIL: one or more budget limits failed")
    return 1


def _add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--budget", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--time-column", default="time")
    parser.add_argument("--current-column", default="current")
    parser.add_argument("--time-unit", choices=("s", "ms", "us"), default="s")
    parser.add_argument("--current-unit", choices=("a", "ma", "ua"), default="ma")
