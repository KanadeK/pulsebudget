# PulseBudget comparison

**PASS** — <code>baseline.csv</code> → <code>candidate.csv</code>

## Summary

| Metric | Baseline | Candidate |
| --- | ---: | ---: |
| Average current | 0.156839 mA | 0.206723 mA |
| Peak current | 45 mA | 52 mA |
| Time-weighted p95 | 0.12 mA | 0.15 mA |
| Pulse count | 3 | 3 |

Average-current delta: **0.0498847 mA**  
Regression: **31.8064%**

## Exact attribution

| Category | Contribution |
| --- | ---: |
| Idle drift | 0.0301363 mA |
| Pulse amplitude | 0.00868511 mA |
| Pulse activity/timing | 0.0110633 mA |

## Budget checks

| Limit | Actual | Rule | Status |
| --- | ---: | ---: | --- |
| `max_average_current_ma` | 0.206723 mA | <= 0.25 mA | PASS |
| `max_peak_current_ma` | 52 mA | <= 60 mA | PASS |
| `max_p95_current_ma` | 0.15 mA | <= 0.2 mA | PASS |
| `min_estimated_runtime_hours` | 4179.5 hours | >= 3000 hours | PASS |
| `max_average_regression_percent` | 31.8064 % | <= 50 % | PASS |
