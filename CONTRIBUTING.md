# Contributing

Thank you for improving PulseBudget. Keep changes narrow and evidence-based.

## Set up

```bash
git clone https://github.com/KanadeK/pulsebudget.git
cd pulsebudget
uv sync --all-extras --frozen
```

## Change workflow

1. Open an issue for a public-contract change or a substantial new capability.
2. Add or update a failing test before changing numerical or CLI behavior.
3. Make the smallest implementation that satisfies that test.
4. Update format/specification documentation when a public field or rule changes.
5. Run the full gate:

```bash
uv run python scripts/release_check.py
```

Pull requests should explain the user-visible problem, test evidence, and any numerical or format
tradeoff. Do not add runtime dependencies, vendor adapters, network behavior, or silent fallbacks
without prior discussion.

## Test fixtures

Synthetic fixtures should have hand-calculable expected values and a stated unit. Do not commit
private hardware captures, credentials, device serial numbers, or customer data.

## Commit style

Use short imperative subjects such as `fix: preserve exact threshold crossings`. Keep formatting
or documentation-only changes separate when practical.

By participating, you agree to follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
