# Failure-to-fix runbook

Start with the exit code. PulseBudget intentionally separates a measured budget regression from a
broken command or input.

## Exit `1`: valid trace, failed budget

1. Open `report.md` and find every `FAIL` row under **Budget checks**.
2. For comparisons, inspect **Exact attribution** to see whether the delta is idle drift, pulse
   amplitude, or pulse activity/timing.
3. Confirm the baseline and candidate represent the same scenario and preparation process.
4. Fix the firmware or deliberately review and update the checked-in budget.
5. Rerun the identical command. Do not delete the report to make CI green.

The report is written even when the command returns `1`.

## Exit `2`: bad command, input, or destination

Read the single `pulsebudget: error:` line on stderr, fix the named boundary, and rerun.

| Error contains | Cause | Fix |
| --- | --- | --- |
| `missing required columns` | Exporter headers do not match defaults. | Pass exact `--time-column` and `--current-column` names. |
| `must be a number` / `must be finite` | Empty, text, `NaN`, or infinity in a measurement. | Repair or re-export that row; PulseBudget does not invent a value. |
| `timestamps must be strictly increasing` | Duplicate or out-of-order samples. | Sort/deduplicate in the acquisition pipeline, then preserve the real order. |
| `current must be non-negative` | Wrong column, wrong preprocessing, or an unsupported signed measurement. | Select the correct column or prepare a non-negative consumption trace. |
| `unknown field` | A budget key is misspelled or unsupported. | Correct it against [FORMAT.md](FORMAT.md). |
| `min_estimated_runtime_hours requires a battery object` | Runtime was gated without an explicit model. | Add capacity, usable fraction, and system efficiency. |
| `cannot read` | Path is wrong or inaccessible. | Use an existing readable file and rerun. |
| `File exists` / `Access is denied` | Output points at a file or unwritable directory. | Choose a writable report directory. |

## Results are implausibly high or low

Check units first. Exporters commonly use microseconds and microamps while PulseBudget defaults to
seconds and milliamps:

```bash
pulsebudget analyze trace.csv --budget budget.json --output report \
  --time-unit us --current-unit ua
```

Then confirm `pulse_threshold_ma` is expressed in milliamps after conversion. PulseBudget never
guesses either value.

## Regression percentage is undefined

A zero-current baseline has no finite percentage denominator. If a percentage budget is
configured, PulseBudget fails that check explicitly. Use an absolute candidate limit such as
`max_average_current_ma`, or provide a representative nonzero baseline.

## Installation or development environment fails

Verify the interpreter and recreate the locked environment:

```bash
python --version
uv sync --all-extras --frozen
uv run pulsebudget --version
```

Python must be 3.11 or newer. If dependency download fails, confirm network/proxy access to PyPI
and rerun `uv sync`; do not remove `--frozen` in CI.

## Release gate fails

Run the named failing command directly, fix that failure, then rerun the one authoritative gate:

```bash
uv run python scripts/release_check.py
```

The gate does not hide failures. A formatting, type, coverage, demo, build, or packaged-smoke
failure prints the exact subprocess that failed and exits nonzero.

## Still reproducible

Open a GitHub issue with:

- `pulsebudget --version` and `python --version`;
- the exact command and stderr;
- the smallest non-sensitive CSV and budget that reproduce it;
- expected versus actual exit code or metric.

Do not attach confidential device traces or security reports to a public issue. Use
[SECURITY.md](../SECURITY.md) for vulnerabilities.
