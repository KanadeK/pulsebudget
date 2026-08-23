# Security policy

## Supported versions

Security fixes are provided for the latest published release.

## Report privately

Use GitHub's **Security → Report a vulnerability** flow for
[KanadeK/pulsebudget](https://github.com/KanadeK/pulsebudget/security/advisories/new).
Do not open a public issue before a fix is available.

Include the affected version, reproduction steps, impact, and any suggested mitigation. Do not
include credentials or unrelated private traces.

## Security boundary

PulseBudget reads local CSV and JSON and writes local reports. It does not execute input content,
fetch URLs, control hardware, load plugins, or send telemetry. External trace names are escaped in
Markdown/SVG, unknown budget fields are rejected, numeric values must be finite, and input is capped
at two million samples.
