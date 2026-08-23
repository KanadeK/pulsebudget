from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeAlias, cast

from pulsebudget.errors import InputError
from pulsebudget.models import Battery, Budget, BudgetLimits, Sample, Trace

TimeUnit: TypeAlias = Literal["s", "ms", "us"]
CurrentUnit: TypeAlias = Literal["a", "ma", "ua"]

MAX_SAMPLES = 2_000_000
_TIME_SCALE: dict[TimeUnit, float] = {"s": 1.0, "ms": 1e-3, "us": 1e-6}
_CURRENT_SCALE: dict[CurrentUnit, float] = {"a": 1e3, "ma": 1.0, "ua": 1e-3}
_LIMIT_FIELDS = {
    "max_average_current_ma",
    "max_peak_current_ma",
    "max_p95_current_ma",
    "max_average_regression_percent",
    "min_estimated_runtime_hours",
}
_BATTERY_FIELDS = {"capacity_mah", "usable_fraction", "system_efficiency"}


@dataclass(frozen=True, slots=True)
class CsvOptions:
    time_column: str = "time"
    current_column: str = "current"
    time_unit: TimeUnit = "s"
    current_unit: CurrentUnit = "ma"


def load_trace(path: Path, options: CsvOptions) -> Trace:
    try:
        handle = path.open("r", encoding="utf-8-sig", newline="")
    except OSError as error:
        raise InputError(f"cannot read trace {path.name}: {error.strerror}") from error

    samples: list[Sample] = []
    try:
        with handle:
            reader = csv.DictReader(handle)
            fields = set(reader.fieldnames or ())
            required = {options.time_column, options.current_column}
            if not required.issubset(fields):
                missing = ", ".join(sorted(required - fields))
                raise InputError(f"trace is missing required columns: {missing}")

            previous_time_s: float | None = None
            for row_number, row in enumerate(reader, start=2):
                if len(samples) == MAX_SAMPLES:
                    raise InputError(f"trace exceeds the {MAX_SAMPLES:,}-sample limit")
                time_s = _parse_measurement(
                    row.get(options.time_column),
                    row_number,
                    options.time_column,
                    _TIME_SCALE[options.time_unit],
                )
                current_ma = _parse_measurement(
                    row.get(options.current_column),
                    row_number,
                    options.current_column,
                    _CURRENT_SCALE[options.current_unit],
                )
                if time_s < 0:
                    raise InputError(f"row {row_number}: time must be non-negative")
                if current_ma < 0:
                    raise InputError(f"row {row_number}: current must be non-negative")
                if previous_time_s is not None and time_s <= previous_time_s:
                    raise InputError(f"row {row_number}: timestamps must be strictly increasing")
                samples.append(Sample(time_s=time_s, current_ma=current_ma))
                previous_time_s = time_s
    except UnicodeDecodeError as error:
        raise InputError(f"trace {path.name} is not valid UTF-8") from error
    except csv.Error as error:
        raise InputError(f"trace {path.name} is not valid CSV: {error}") from error

    if len(samples) < 2:
        raise InputError("trace must contain at least two samples")
    return Trace(name=path.name, samples=tuple(samples))


def load_budget(path: Path) -> Budget:
    try:
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
    except OSError as error:
        raise InputError(f"cannot read budget {path.name}: {error.strerror}") from error
    except UnicodeDecodeError as error:
        raise InputError(f"budget {path.name} is not valid UTF-8") from error
    except json.JSONDecodeError as error:
        raise InputError(f"budget {path.name} is not valid JSON: {error.msg}") from error

    root = _require_object(raw, "budget")
    _reject_unknown(root, {"schema_version", "pulse_threshold_ma", "limits", "battery"}, "budget")
    if root.get("schema_version") != 1 or type(root.get("schema_version")) is not int:
        raise InputError("schema_version must be the integer 1")

    pulse_threshold_ma = _require_number(root, "pulse_threshold_ma", "budget")
    if pulse_threshold_ma <= 0:
        raise InputError("pulse_threshold_ma must be greater than zero")

    limits_raw = _require_object(root.get("limits", {}), "limits")
    _reject_unknown(limits_raw, _LIMIT_FIELDS, "limits")
    limit_values = {
        field: _optional_non_negative_number(limits_raw, field, "limits") for field in _LIMIT_FIELDS
    }
    if (
        limit_values["min_estimated_runtime_hours"] is not None
        and limit_values["min_estimated_runtime_hours"] == 0
    ):
        raise InputError("limits.min_estimated_runtime_hours must be greater than zero")
    limits = BudgetLimits(**limit_values)

    battery: Battery | None = None
    if "battery" in root:
        battery_raw = _require_object(root["battery"], "battery")
        _reject_unknown(battery_raw, _BATTERY_FIELDS, "battery")
        capacity_mah = _require_number(battery_raw, "capacity_mah", "battery")
        usable_fraction = _require_number(battery_raw, "usable_fraction", "battery")
        system_efficiency = _require_number(battery_raw, "system_efficiency", "battery")
        if capacity_mah <= 0:
            raise InputError("battery.capacity_mah must be greater than zero")
        if not 0 < usable_fraction <= 1:
            raise InputError("battery.usable_fraction must be greater than zero and at most one")
        if not 0 < system_efficiency <= 1:
            raise InputError("battery.system_efficiency must be greater than zero and at most one")
        battery = Battery(
            capacity_mah=capacity_mah,
            usable_fraction=usable_fraction,
            system_efficiency=system_efficiency,
        )

    if limits.min_estimated_runtime_hours is not None and battery is None:
        raise InputError("min_estimated_runtime_hours requires a battery object")
    return Budget(pulse_threshold_ma=pulse_threshold_ma, limits=limits, battery=battery)


def _parse_measurement(raw: str | None, row: int, column: str, scale: float) -> float:
    if raw is None or raw.strip() == "":
        raise InputError(f"row {row}: {column} is required")
    try:
        value = float(raw)
    except ValueError as error:
        raise InputError(f"row {row}: {column} must be a number") from error
    if not math.isfinite(value):
        raise InputError(f"row {row}: {column} must be finite")
    return value * scale


def _require_object(value: object, location: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise InputError(f"{location} must be a JSON object")
    if not all(isinstance(key, str) for key in value):
        raise InputError(f"{location} keys must be strings")
    return cast(dict[str, object], value)


def _reject_unknown(value: dict[str, object], allowed: set[str], location: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise InputError(f"{location} has unknown field: {unknown[0]}")


def _require_number(value: dict[str, object], field: str, location: str) -> float:
    if field not in value:
        raise InputError(f"{location}.{field} is required")
    raw = value[field]
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise InputError(f"{location}.{field} must be a number")
    number = float(raw)
    if not math.isfinite(number):
        raise InputError(f"{location}.{field} must be finite")
    return number


def _optional_non_negative_number(
    value: dict[str, object], field: str, location: str
) -> float | None:
    if field not in value:
        return None
    number = _require_number(value, field, location)
    if number < 0:
        raise InputError(f"{location}.{field} must be non-negative")
    return number
