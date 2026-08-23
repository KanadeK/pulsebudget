from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Sample:
    time_s: float
    current_ma: float


@dataclass(frozen=True, slots=True)
class Trace:
    name: str
    samples: tuple[Sample, ...]

    @property
    def duration_s(self) -> float:
        return self.samples[-1].time_s - self.samples[0].time_s


@dataclass(frozen=True, slots=True)
class BudgetLimits:
    max_average_current_ma: float | None = None
    max_peak_current_ma: float | None = None
    max_p95_current_ma: float | None = None
    max_average_regression_percent: float | None = None
    min_estimated_runtime_hours: float | None = None


@dataclass(frozen=True, slots=True)
class Battery:
    capacity_mah: float
    usable_fraction: float
    system_efficiency: float


@dataclass(frozen=True, slots=True)
class Budget:
    pulse_threshold_ma: float
    limits: BudgetLimits
    battery: Battery | None


@dataclass(frozen=True, slots=True)
class Pulse:
    start_s: float
    end_s: float
    duration_s: float
    charge_mah: float
    excess_charge_mah: float
    peak_current_ma: float


@dataclass(frozen=True, slots=True)
class TraceAnalysis:
    trace_name: str
    duration_s: float
    charge_mah: float
    average_current_ma: float
    peak_current_ma: float
    p95_current_ma: float
    pulses: tuple[Pulse, ...]
    pulse_rate_hz: float
    estimated_runtime_hours: float | None


@dataclass(frozen=True, slots=True)
class Attribution:
    idle_drift_ma: float
    pulse_amplitude_ma: float
    pulse_activity_ma: float


@dataclass(frozen=True, slots=True)
class TraceComparison:
    baseline: TraceAnalysis
    candidate: TraceAnalysis
    delta_average_current_ma: float
    regression_percent: float | None
    attribution: Attribution
