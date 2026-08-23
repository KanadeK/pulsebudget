# PulseBudget v0.1.0 tasks

## Task 1: Define models and strict input boundaries

- [x] Contract dataclasses and errors are typed and minimal.
- [x] CSV parser validates columns, units, finite values, ordering, non-negative current, and row cap.
- [x] Budget parser rejects unknown keys and invalid ranges.
- Verify: focused parser/model tests fail first, then pass.
- Files: `src/pulsebudget/models.py`, `src/pulsebudget/io.py`, parser tests/fixtures.
- Dependencies: none.

## Task 2: Analyze one trace

- [ ] Trapezoidal charge/average and time-weighted p95 match hand-calculated fixtures.
- [ ] Threshold crossings and pulse metrics work with irregular sampling.
- [ ] Battery runtime formula is transparent and tested.
- Verify: focused numerical tests plus full suite.
- Files: `src/pulsebudget/analysis.py`, analysis tests.
- Dependencies: Task 1.

## Task 3: Compare traces with exact attribution

- [ ] Normalized knot/crossing merge partitions every interval into one category.
- [ ] Idle, pulse-amplitude, and pulse-activity contributions sum to the observed delta.
- [ ] Pulse counts/rates and regression percent are reported.
- Verify: synthetic fixture activates every category and invariant passes.
- Files: `src/pulsebudget/compare.py`, comparison tests/fixtures.
- Dependencies: Task 2.

## Task 4: Gate and report through the CLI

- [ ] Applicable limits produce explicit pass/fail evidence.
- [ ] JSON, Markdown, and SVG are deterministic and escaped.
- [ ] Subprocess paths return documented exit codes and create all artifacts.
- Verify: CLI integration tests cover pass, fail, and invalid input.
- Files: budget/report/CLI modules and tests.
- Dependencies: Tasks 2-3.

## Task 5: Ship runnable examples and user documentation

- [ ] Example traces are generated/verified by the real CLI.
- [ ] English README and Chinese guide include quick start, acceptance, limitations, and repair flow.
- [ ] Research, format, security, contributing, and changelog documents are current.
- Verify: every documented command is exercised by the release gate.
- Files: `examples/`, `README*`, `docs/`, community files.
- Dependencies: Task 4.

## Task 6: Automate release quality and packaging

- [ ] CI runs lint, type check, tests/coverage, demo, and packaging on supported Python versions.
- [ ] Packaging builds wheel, sdist, standalone `.pyz`, example bundle, and one checksum manifest.
- [ ] Packaged CLI smoke test passes; final five-axis review has no required findings.
- Verify: `python scripts/release_check.py` succeeds from the project root.
- Files: `scripts/`, `.github/workflows/`, packaging config.
- Dependencies: Task 5.

## Task 7: Publish and notify

- [ ] Atomic Git history has the expected author and no secrets/co-author trailers.
- [ ] Public `KanadeK/pulsebudget` contains the exact verified commit.
- [ ] CI is green; annotated `v0.1.0` and Release assets are online and downloadable.
- [ ] Gmail message contains repository, Release, acceptance commands, and limitations.
- Verify: public API/`gh` checks and Gmail sent-message evidence.
- Dependencies: Task 6 and valid external authentication.
