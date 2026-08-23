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

