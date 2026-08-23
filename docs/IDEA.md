# PulseBudget

## Problem statement

How might we let embedded developers see exactly why a firmware change costs battery life,
using the current traces they already capture, without requiring vendor hardware, a cloud
account, or a proprietary project format?

## Recommended direction

PulseBudget is a **Git diff for battery life**. It reads timestamp/current CSV traces,
integrates their charge, detects threshold-defined pulses, estimates runtime under an explicit
battery model, and compares a candidate trace with a baseline. The comparison partitions the
average-current delta into three exhaustive buckets: idle drift, pulse-amplitude change, and
pulse-activity/timing change.

The first release is deliberately a command-line tool with deterministic JSON, Markdown, and
SVG evidence. That makes it useful locally and in CI before any hardware adapter or dashboard
exists.

## Target user and success

The primary user is an embedded or IoT developer who can export a current trace from a power
profiler but currently compares screenshots or headline averages by hand. Success means one
command produces a reviewable report and a stable pass/fail exit code that can protect a
firmware pull request.

## Key assumptions to validate

- Developers can export monotonically increasing time/current CSV data.
- An explicit pulse threshold is sufficient for a useful first attribution model.
- Deterministic evidence and CI failure are more valuable initially than live acquisition.
- A vendor-neutral format is a meaningful wedge between current viewers and battery-life
  calculators.

## MVP scope

- Explicit CSV column and unit mapping.
- Time-aware charge, average, peak, p95, pulse, and runtime analysis.
- Baseline/candidate comparison with exact additive attribution.
- Strict JSON budget file and exit codes `0` (pass), `1` (budget failure), `2` (input error).
- Deterministic JSON, Markdown, and SVG reports.
- Dependency-free runtime, tests, CI, reproducible release assets, and real examples.

## Not doing

- **Live hardware capture** — vendor protocols would hide the core value behind integration work.
- **Battery chemistry simulation** — the first release reports a transparent upper-bound model,
  not false electrochemical precision.
- **Cloud storage or accounts** — traces remain local and CI-friendly.
- **Automatic threshold guessing** — an explicit threshold is inspectable and avoids silently
  changing the meaning of a pulse.
- **A GUI** — the release must prove the analysis engine and automation contract first.

