# Research and novelty boundary

Research snapshot: **2026-08-23**.

## Decision

PulseBudget was selected after checking the local project inventory, previously discussed ideas,
and GitHub projects around current capture, energy monitoring, battery estimation, and regression
gates. The defensible wedge is not “software that graphs power.” It is this combined workflow:

> vendor-neutral embedded current CSV → time-correct metrics → normalized baseline/candidate diff
> → exact idle/amplitude/activity attribution → deterministic CI budget evidence

The search found adjacent projects, including a build-failing energy comparison for Spring Boot,
but did not find a project with this exact embedded-trace contract. That is a bounded search
finding, not a claim that no similar repository can exist.

## Existing local and prior-work boundary

| Existing or discussed work | Its center of gravity | Why PulseBudget is not a repeat |
| --- | --- | --- |
| [WattWraith](https://github.com/KanadeK/wattwraith) | Smart-plug household standby/phantom-load detection, tariffs, and appliance guidance | PulseBudget compares firmware current captures in milliamps, has no appliance/tariff/anomaly workflow, and provides an exact regression decomposition plus CI exit contract. |
| SofaPilot | Local public-transit route choice | Different user, data, algorithm, and outcome. |
| Syncuisine concept | Multi-dish kitchen scheduling | Different domain and scheduling problem; it was not reused. |
| Query Quilt / Data XRay Local / README Flightcheck / ManualCare | Query documentation, data inspection, repository and operational tooling | No current-trace or battery-regression functionality was carried over. |

The overlap with WattWraith is only the broad word “energy” and local file processing. Target
user, units, input semantics, analysis model, decision, and output contract are different.

## Closest GitHub projects reviewed

| Project | What it does | Remaining gap addressed here |
| --- | --- | --- |
| [CurrentViewer](https://github.com/MGX3D/CurrentViewer) | Captures and visualizes live CurrentRanger data; exports CSV/JSON/GIF. | Hardware acquisition/viewing rather than baseline/candidate attribution and a version-controlled budget gate. |
| [Joulescope UI](https://github.com/jetperch/pyjoulescope_ui) | Full GUI for Joulescope measurement hardware. | Instrument UI rather than a vendor-neutral post-capture CI diff. |
| [Joular Core](https://github.com/joular/joularcore) | Measures CPU/GPU/system power across operating systems and exposes streams/APIs. | Host/software monitoring rather than embedded milliamp trace comparison and pulse attribution. |
| [greener-spring-boot](https://github.com/patbaumgartner/greener-spring-boot) | Measures Spring Boot energy through JoularCore, compares a baseline, and can fail Maven/Gradle builds. | Validates demand for regression gates, but is Java/Spring workload tooling and does not consume arbitrary embedded current traces or explain idle/amplitude/activity deltas. |
| [Nordic power optimization guidance](https://github.com/nrfconnect/sdk-nrf/blob/main/doc/nrf/test_and_optimize/optimizing/power_general.rst) | Vendor documentation for measuring and optimizing Nordic-device power. | Guidance, not a cross-vendor report schema and CI gate. |
| [OracleTrace](https://github.com/KaykCaputo/oracletrace) | Python execution-time regression traces and CI failures. | A useful interaction pattern in another domain; it does not analyze electrical measurements. |

Representative search phrases included:

- `embedded current trace regression comparison CSV battery life CLI`
- `firmware power consumption regression test current trace`
- `Joulescope Otii Power Profiler regression current trace CI`
- `current consumption baseline fail firmware`
- `power budget current trace embedded CLI`

We also rejected more visibly crowded candidates—indoor sunlight simulation, ESP pin validation,
gallery-wall planning, electronic front-panel generation, and pedalboard layout—after finding
directly similar repositories or mature tools.

## Why it may earn attention

- The before/after SVG is understandable without installing the tool.
- The phrase “Git diff for battery life” explains the job in one line.
- Exit codes and Markdown/JSON artifacts make it useful in real firmware pull requests.
- It accepts profiler exports instead of competing with hardware vendors.
- Exact additive attribution is a technical demonstration, not a decorative interface.

These are product hypotheses. GitHub stars and traffic depend on distribution, timing, community
fit, and continued maintenance; the release does not claim or guarantee a number.

## Scope guard

The first release intentionally excludes a GUI, live capture, cloud accounts, vendor adapters,
automatic threshold selection, battery chemistry, and statistical multi-run inference. Adding any
of those before users validate the CSV-to-CI workflow would blur the novelty boundary and increase
maintenance without proving the core value.
