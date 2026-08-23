# ADR-0001: Use a piecewise-linear trace model

## Status

Accepted

## Date

2026-08-22

## Context

Power profilers export samples at different and sometimes irregular rates. Row-count averages and
percentiles change when the same waveform is sampled more densely, while screenshot comparisons
cannot support a deterministic CI gate.

## Decision

Treat each adjacent sample pair as a linear current segment. Integrate charge with the trapezoid
rule, compute percentiles by time spent below a current value, interpolate pulse-threshold
crossings, and compare traces after normalizing their durations to `0..1`.

Comparison uses the union of sample knots and threshold crossings. The current delta on each
resulting interval is assigned to exactly one of three states: idle/idle, pulse/pulse, or mixed.
This makes attribution exhaustive and additive rather than heuristic.

## Alternatives considered

### Row-based statistics

Simpler, but results depend on sampling density and can misrepresent irregular captures.

### Resample to a fixed frequency

Familiar, but adds interpolation error and an arbitrary frequency setting to the public contract.

### Hardware-vendor parsers and native algorithms

Could preserve proprietary semantics, but would make the initial value depend on hardware access
and several unstable integrations.

## Consequences

- Numerical behavior is deterministic and vendor-neutral.
- Threshold crossings require slightly more code, but no numerical dependency.
- Normalized comparison explains average-current change; it does not claim clock-synchronized
  event matching between traces.
- Inputs must contain at least two strictly ordered samples.

