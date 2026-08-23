# Spec: PulseBudget v0.1.0

## Objective

Build a public, dependency-free Python CLI for embedded developers who need to compare real
current-consumption traces. PulseBudget must turn CSV evidence into explainable battery metrics,
an exact baseline/candidate attribution, deterministic reports, and a CI-compatible budget gate.

## Tech stack

- Python `>=3.11`.
- Standard-library runtime only.
- Hatchling for wheel/sdist builds; pytest, coverage, Ruff, and mypy are development-only.
- GitHub Actions for CI and tag-driven Releases.

## Public command contract

```text
pulsebudget analyze TRACE.csv --budget budget.json [CSV OPTIONS] --output report-dir
pulsebudget compare BASELINE.csv CANDIDATE.csv --budget budget.json [CSV OPTIONS] --output report-dir
pulsebudget --version

CSV OPTIONS:
  --time-column NAME       default: time
  --current-column NAME    default: current
  --time-unit {s,ms,us}    default: s
  --current-unit {a,ma,ua} default: ma
```

Both analysis commands write exactly these files:

- `report.json` — stable machine-readable schema.
- `report.md` — human/PR summary.
- `trace.svg` for `analyze`, `comparison.svg` for `compare`.

Exit codes are part of the public contract:

- `0`: every applicable budget limit passed.
- `1`: valid inputs were analyzed and at least one limit failed.
- `2`: command, CSV, or budget input was invalid.

Errors go to stderr; successful summaries go to stdout. Absolute local paths are not written to
reports.

## Budget contract

```json
{
  "schema_version": 1,
  "pulse_threshold_ma": 20.0,
  "limits": {
    "max_average_current_ma": 8.0,
    "max_peak_current_ma": 140.0,
    "max_p95_current_ma": 35.0,
    "max_average_regression_percent": 10.0,
    "min_estimated_runtime_hours": 100.0
  },
  "battery": {
    "capacity_mah": 1200.0,
    "usable_fraction": 0.8,
    "system_efficiency": 0.9
  }
}
```

`schema_version` and `pulse_threshold_ma` are required. `limits` and `battery` are optional,
but unknown fields are rejected so misspelled limits cannot silently pass. Regression limits
apply only to `compare`. Runtime limits require a battery object.

## Analysis semantics

- CSV timestamps must be finite, non-negative, and strictly increasing; current must be finite
  and non-negative. At least two samples are required.
- Charge uses trapezoidal integration over real timestamps. `mA*s / 3600 = mAh`.
- Average current is integrated charge divided by duration.
- p95 is time-weighted over the piecewise-linear trace, not a percentile of row count.
- Pulse boundaries are exact linear crossings of `pulse_threshold_ma`; adjacent above-threshold
  intervals form one pulse.
- Runtime is `capacity_mAh * usable_fraction * system_efficiency / average_current_mA`. It is
  explicitly an upper-bound estimate, not a battery-chemistry model.
- Comparison normalizes each trace to progress `0..1`, merges every sample knot and threshold
  crossing, and exactly integrates candidate minus baseline. Every interval is classified as:
  both below threshold (idle drift), both above (pulse amplitude), or one above (pulse activity).
  Those three contributions must sum to the observed average-current delta within floating-point
  tolerance.

## Commands for contributors

```powershell
uv venv --python 3.12 .venv
uv pip install --python .venv\Scripts\python.exe -e ".[dev]"
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m mypy src scripts
.venv\Scripts\python.exe scripts\release_check.py
```

Release packaging:

```powershell
.venv\Scripts\python.exe scripts\package_release.py
```

## Project structure

```text
src/pulsebudget/       public package and CLI
tests/                 unit, integration, and CLI tests
tests/fixtures/        deterministic numerical fixtures
examples/              runnable baseline/candidate/budget inputs
docs/                  research, formats, decisions, troubleshooting
scripts/               release gate and deterministic packaging
tasks/                 implementation plan and checklist
.github/workflows/     CI and release automation
```

## Code style

Typed, explicit functions; validation stays at file/CLI boundaries and internal numerical code
trusts validated models.

```python
def integrate_charge_mas(samples: tuple[Sample, ...]) -> float:
    return sum(
        (left.current_ma + right.current_ma)
        * 0.5
        * (right.time_s - left.time_s)
        for left, right in pairwise(samples)
    )
```

No broad exception swallowing, silent defaults, speculative adapters, or single-use abstraction
layers.

## Testing strategy

- Unit tests: integration math, time-weighted percentile, threshold crossings, pulse metrics,
  exact attribution, and limit evaluation.
- Integration tests: strict CSV/budget parsing and deterministic report generation.
- CLI tests: real subprocess, real exit codes, and real output artifacts.
- Release check: lint, type check, full coverage suite, package build, demo run, and packaged CLI
  smoke test.
- Core analysis modules must maintain at least 90% branch coverage; no skipped tests.

## Boundaries

- Always: validate external files once, escape report text, use deterministic fixtures, run the
  release gate before publishing, and preserve exit-code semantics.
- Ask first: add runtime dependencies, change public JSON fields, weaken an existing limit, or
  add network/hardware access.
- Never: execute content from input files, fetch URLs from inputs, emit absolute paths, hide a
  failed limit, claim chemical accuracy, commit secrets, or publish from a failing commit.

## Threat model

Trust boundaries are CSV, JSON budget, CLI arguments, and output paths. Assets are developer
workstations, CI availability, and report integrity. Mitigations are strict schemas, finite-value
checks, a two-million-sample cap, no shell evaluation, escaped SVG/Markdown text, deterministic
outputs, and no network behavior.

## Success criteria

1. Known analytical fixtures produce independently calculable charge, average, p95, and pulse
   values.
2. Comparison attribution sums to the total average-current delta and distinguishes all three
   categories on a synthetic fixture.
3. Passing, failing, and invalid-input CLI paths return `0`, `1`, and `2` respectively.
4. Example inputs generate non-empty JSON, Markdown, and SVG evidence from the real CLI.
5. The release gate passes without skipped checks and builds installable wheel/sdist plus a
   standalone `.pyz` and checksums.
6. README contains copy/paste acceptance commands and a failure-to-fix runbook.
7. CI passes on supported Python versions, a public GitHub `v0.1.0` Release is verifiable, and
   Gmail notification is sent only after that online verification.

## Open questions

None block v0.1.0. Vendor-specific CSV presets and live capture remain roadmap candidates.

