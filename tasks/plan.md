# Implementation plan: PulseBudget v0.1.0

## Overview

Build the smallest release that proves the differentiated capability: real trace mathematics,
exact additive comparison, and a CI budget contract. Work proceeds contract-first and risk-first;
the numerical core is proven before reports, packaging, or publication.

## Architecture decisions

- Piecewise-linear immutable trace model; see ADR-0001.
- Standard-library runtime; development and packaging tools never enter runtime dependencies.
- CLI/file schemas are the only public interfaces in v0.1.0.
- Reports are deterministic release evidence and contain no absolute paths or generated timestamps.

## Dependency graph

```text
validated Sample/Trace/Budget models
  -> CSV and JSON boundary parsers
    -> numerical analysis and pulse detection
      -> normalized comparison attribution
        -> budget evaluation
          -> JSON/Markdown/SVG reports
            -> CLI exit codes
              -> examples, release gate, package, CI, publication
```

## Phases and checkpoints

### Phase 1: Contract and numerical core

- Task 1: package/contract scaffold and boundary fixtures.
- Task 2: trace integration, time-weighted percentile, and pulse analysis.
- Checkpoint: focused numerical tests and type check pass.

### Phase 2: Differentiated workflow

- Task 3: exact baseline/candidate attribution.
- Task 4: budgets, deterministic reports, and CLI exit codes.
- Checkpoint: real subprocess paths return `0`, `1`, and `2`; reports reconcile numerically.

### Phase 3: Release system

- Task 5: examples, bilingual documentation, and failure repair runbook.
- Task 6: CI, deterministic packaging, release gate, and security/quality review.
- Checkpoint: clean checkout release command builds and smoke-tests all assets.

### Phase 4: Publication

- Task 7: atomic commits, public repository, CI observation, annotated `v0.1.0`, GitHub Release,
  online verification, then Gmail notification.

## Risks and mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Attribution does not reconcile | High | Exact interval partition and invariant test before report work |
| Sampling density biases p95 | High | Time-weighted quantile with irregular-sampling fixture |
| Input typo silently disables a gate | High | Reject unknown budget keys |
| Reports leak local paths or render markup | Medium | Basenames only and output escaping tests |
| GitHub authentication remains invalid | High | Finish all local gates; then try existing Git credentials and re-auth paths without claiming publication |
| Scope drifts into hardware/UI work | Medium | Enforce the Not Doing list in IDEA.md |

## Open questions

None for implementation. Public GitHub authentication is an external release dependency already
identified by `gh auth status`.

