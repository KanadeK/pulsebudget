# Input and report formats

## Trace CSV

The default header is:

```csv
time,current
0,0.12
0.002,25
0.010,25
0.012,0.12
```

Use CLI flags when an exporter uses different names or units:

| Flag | Values | Default |
| --- | --- | --- |
| `--time-column` | any exact CSV header | `time` |
| `--current-column` | any exact CSV header | `current` |
| `--time-unit` | `s`, `ms`, `us` | `s` |
| `--current-unit` | `a`, `ma`, `ua` | `ma` |

Rules at the file boundary:

- UTF-8 or UTF-8 with BOM.
- At least two and at most 2,000,000 data rows.
- Finite, non-negative time and current.
- Strictly increasing timestamps.
- Extra columns are preserved by the source file but ignored by PulseBudget.

The tool does not guess units or repair measurements.

## Budget JSON

```json
{
  "schema_version": 1,
  "pulse_threshold_ma": 10.0,
  "limits": {
    "max_average_current_ma": 0.25,
    "max_peak_current_ma": 60.0,
    "max_p95_current_ma": 0.2,
    "max_average_regression_percent": 10.0,
    "min_estimated_runtime_hours": 3000.0
  },
  "battery": {
    "capacity_mah": 1200.0,
    "usable_fraction": 0.8,
    "system_efficiency": 0.9
  }
}
```

`schema_version` and `pulse_threshold_ma` are required. `limits` and `battery` are optional.
Unknown fields are errors.

| Field | Applies to | Rule |
| --- | --- | --- |
| `max_average_current_ma` | both commands | candidate/single average must be at most the limit |
| `max_peak_current_ma` | both commands | candidate/single peak must be at most the limit |
| `max_p95_current_ma` | both commands | candidate/single time-weighted p95 must be at most the limit |
| `max_average_regression_percent` | `compare` | `(candidate - baseline) / baseline × 100` must be at most the limit |
| `min_estimated_runtime_hours` | both commands | estimated runtime must be at least the limit; requires `battery` |

If the baseline average is zero and a regression-percent limit is configured, that check fails
with `baseline average current is zero`; an infinite percentage is not serialized as a JSON
number.

## Numerical model

Each adjacent CSV pair is a line segment. Charge is trapezoidal integration:

```text
segment charge (mA·s) = (left current + right current) / 2 × elapsed seconds
charge (mAh) = sum(segment charge) / 3600
average current (mA) = sum(segment charge) / trace duration
```

Time-weighted p95 measures how long the continuous piecewise-linear signal stays at or below a
current value. Duplicating CSV rows without changing the signal therefore cannot change p95.

Pulse start/end points are exact linear crossings of `pulse_threshold_ma`. Adjacent intervals
whose midpoint is above the threshold form one pulse.

For comparison, each trace is independently normalized from start to end onto progress `0..1`.
PulseBudget merges all sample knots and threshold crossings from both traces. On each resulting
interval it exactly integrates `candidate - baseline` and assigns the interval to one category:

- both signals below threshold: `idle_drift_ma`;
- both signals above threshold: `pulse_amplitude_ma`;
- exactly one signal above threshold: `pulse_activity_ma`.

The implementation fails fast if the three contributions do not reproduce the observed
average-current delta within floating-point tolerance.

## `report.json`

All reports use `schema_version: 1`, contain no timestamp or absolute input path, use sorted JSON
keys, and reject non-standard `NaN`/`Infinity` output.

An `analyze` report has:

```text
schema_version, command, passed, pulse_threshold_ma,
analysis, budget_checks
```

A `compare` report has:

```text
schema_version, command, passed, pulse_threshold_ma,
baseline, candidate, comparison, budget_checks
```

Each analysis contains duration, charge, average/peak/p95 current, pulse count/rate/details, and
runtime. `estimated_runtime_status` is `not_requested`, `estimated`, or `unbounded`; the numeric
field is `null` unless the status is `estimated`.

Each budget check contains `name`, `actual`, `actual_status`, `operator`, `limit`, `unit`, `status`,
and `reason`. Status is `pass`, `fail`, or `not_applicable`. `not_applicable` is currently used when
an `analyze` command receives a configured comparison-only regression limit.

## Markdown and SVG

`report.md` is a compact human summary derived from the same typed results as JSON. The SVG is a
self-contained normalized timeline: `trace.svg` for analysis and `comparison.svg` for comparison.
External trace names are escaped before entering either format.
