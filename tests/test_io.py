from __future__ import annotations

import json
from pathlib import Path

import pytest

from pulsebudget.errors import InputError
from pulsebudget.io import CsvOptions, load_budget, load_trace


def write_text(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_load_trace_converts_explicit_units(tmp_path: Path) -> None:
    trace_path = write_text(
        tmp_path / "trace.csv",
        "elapsed_ms,draw_ua\n0,1000\n500,3000\n1500,1000\n",
    )

    trace = load_trace(
        trace_path,
        CsvOptions(
            time_column="elapsed_ms",
            current_column="draw_ua",
            time_unit="ms",
            current_unit="ua",
        ),
    )

    assert [sample.time_s for sample in trace.samples] == [0.0, 0.5, 1.5]
    assert [sample.current_ma for sample in trace.samples] == [1.0, 3.0, 1.0]
    assert trace.name == "trace.csv"


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        ("0,1\n0,2\n", "strictly increasing"),
        ("0,1\n1,nan\n", "finite"),
        ("0,1\n1,-0.1\n", "non-negative"),
    ],
)
def test_load_trace_rejects_invalid_measurements(tmp_path: Path, rows: str, message: str) -> None:
    trace_path = write_text(tmp_path / "invalid.csv", f"time,current\n{rows}")

    with pytest.raises(InputError, match=message):
        load_trace(trace_path, CsvOptions())


def test_load_trace_rejects_missing_columns(tmp_path: Path) -> None:
    trace_path = write_text(tmp_path / "trace.csv", "timestamp,amps\n0,1\n1,2\n")

    with pytest.raises(InputError, match="required columns"):
        load_trace(trace_path, CsvOptions())


def test_load_trace_rejects_duplicate_columns(tmp_path: Path) -> None:
    trace_path = write_text(
        tmp_path / "trace.csv",
        "time,current,current\n0,1,2\n1,2,3\n",
    )

    with pytest.raises(InputError, match="duplicate column: current"):
        load_trace(trace_path, CsvOptions())


def test_load_trace_rejects_unit_conversion_overflow(tmp_path: Path) -> None:
    trace_path = write_text(
        tmp_path / "trace.csv",
        "time,current\n0,1\n1,1e308\n",
    )

    with pytest.raises(InputError, match="current must be finite"):
        load_trace(trace_path, CsvOptions(current_unit="a"))


def test_load_budget_parses_strict_contract(tmp_path: Path) -> None:
    budget_path = tmp_path / "budget.json"
    budget_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "pulse_threshold_ma": 20,
                "limits": {
                    "max_average_current_ma": 8,
                    "max_average_regression_percent": 10,
                },
                "battery": {
                    "capacity_mah": 1200,
                    "usable_fraction": 0.8,
                    "system_efficiency": 0.9,
                },
            }
        ),
        encoding="utf-8",
    )

    budget = load_budget(budget_path)

    assert budget.pulse_threshold_ma == 20.0
    assert budget.limits.max_average_current_ma == 8.0
    assert budget.limits.max_average_regression_percent == 10.0
    assert budget.battery is not None
    assert budget.battery.capacity_mah == 1200.0


def test_load_budget_rejects_unknown_limit(tmp_path: Path) -> None:
    budget_path = tmp_path / "budget.json"
    budget_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "pulse_threshold_ma": 20,
                "limits": {"max_averge_current_ma": 8},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(InputError, match="unknown field"):
        load_budget(budget_path)


def test_load_budget_rejects_duplicate_fields(tmp_path: Path) -> None:
    budget_path = write_text(
        tmp_path / "budget.json",
        '{"schema_version":1,"pulse_threshold_ma":10,"pulse_threshold_ma":20}',
    )

    with pytest.raises(InputError, match="duplicate field: pulse_threshold_ma"):
        load_budget(budget_path)


def test_load_budget_rejects_out_of_range_values(tmp_path: Path) -> None:
    budget_path = tmp_path / "budget.json"
    budget_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "pulse_threshold_ma": 20,
                "battery": {
                    "capacity_mah": 1200,
                    "usable_fraction": 1.1,
                    "system_efficiency": 0.9,
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(InputError, match="usable_fraction"):
        load_budget(budget_path)
