"""Ocean-heat projection maths (pure Python, no plotting libraries).

Grounding (all published, none invented):
* Database ID=7: roughly 85% of the excess global-warming heat goes to the oceans.
  The model uses that share as a fixed constant, so the split is always exactly 85/15.
* Ocean heat gain (upper 2000 m): about 16 ZJ in 2024 and 23 +/- 8 ZJ in 2025
  (Pan, Cheng et al., Advances in Atmospheric Sciences, January 2026).
* The heating rate is accelerating by 0.32 +/- 0.14 W/m2 per decade over 2005-2025
  (same study, which notes this is consistent with Earth's energy imbalance).
* Unit conversion: 1 W/m2 over a whole year across Earth's surface = about 16 ZJ.
* 2023 world primary energy use: about 620 EJ = 0.62 ZJ per year.

Model: the yearly heat gain starts at a base rate R0 and grows linearly by a ZJ/yr
each year, so the heat gained after t years is  R0*t + 0.5*a*t^2.
Two scenarios: "steady" (a = 0, the rate stops growing) and "trend" (a = the
observed acceleration). The "trend" band uses the low/high end of every input.
This is a transparent extrapolation, not a climate-model forecast: cutting
greenhouse-gas emissions would change it.
"""
from __future__ import annotations

from dataclasses import dataclass

OCEAN_SHARE_PCT = 85  # database ID=7
OTHER_SHARE_PCT = 100 - OCEAN_SHARE_PCT

BASE_YEAR = 2025
MIN_YEAR, MAX_YEAR = 2026, 2075

EARTH_SURFACE_M2 = 5.1e14
SECONDS_PER_YEAR = 3.156e7
ZJ_PER_W_M2_YEAR = EARTH_SURFACE_M2 * SECONDS_PER_YEAR / 1e21  # about 16.1

OCEAN_GAIN_2024_ZJ = 16.0
OCEAN_GAIN_2025_ZJ = 23.0
OCEAN_GAIN_2025_UNCERTAINTY_ZJ = 8.0
BASE_OCEAN_RATE_ZJ = (OCEAN_GAIN_2024_ZJ + OCEAN_GAIN_2025_ZJ) / 2  # 19.5, smooths year-to-year swings
BASE_RATE_LOW_ZJ = OCEAN_GAIN_2024_ZJ
BASE_RATE_HIGH_ZJ = OCEAN_GAIN_2025_ZJ

ACCEL_W_M2_PER_DECADE = {"low": 0.32 - 0.14, "central": 0.32, "high": 0.32 + 0.14}
WORLD_ENERGY_ZJ_PER_YEAR = 0.62

SCENARIOS = {
    "steady": "Steady rate (heating stops speeding up)",
    "trend": "Current trend (acceleration continues)",
}


def accel_zj_per_year2(w_m2_per_decade: float) -> float:
    """Convert an acceleration in W/m2 per decade to ZJ per year, per year."""
    return w_m2_per_decade / 10 * ZJ_PER_W_M2_YEAR


def cumulative_ocean_zj(years_ahead: float, base_rate: float, accel: float) -> float:
    """Ocean heat gained after ``years_ahead`` years (rate grows linearly)."""
    return base_rate * years_ahead + 0.5 * accel * years_ahead ** 2


def ocean_to_total(ocean_zj: float) -> float:
    """Total excess heat, given that the oceans take exactly 85% of it."""
    return ocean_zj / (OCEAN_SHARE_PCT / 100)


def _scenario_accel(scenario: str, level: str = "central") -> float:
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario}")
    return 0.0 if scenario == "steady" else accel_zj_per_year2(ACCEL_W_M2_PER_DECADE[level])


@dataclass(frozen=True)
class HeatProjection:
    year: int
    years_ahead: int
    scenario: str
    ocean_zj: float
    other_zj: float
    total_zj: float
    total_low_zj: float
    total_high_zj: float

    @property
    def world_energy_years(self) -> float:
        """The total heat expressed as years of today's world energy use."""
        return self.total_zj / WORLD_ENERGY_ZJ_PER_YEAR


def project(year: int, scenario: str = "trend") -> HeatProjection:
    """Cumulative excess heat gained from the end of 2025 until the end of ``year``."""
    year = int(max(BASE_YEAR, min(MAX_YEAR, year)))
    t = year - BASE_YEAR
    ocean = cumulative_ocean_zj(t, BASE_OCEAN_RATE_ZJ, _scenario_accel(scenario))
    low = cumulative_ocean_zj(t, BASE_RATE_LOW_ZJ, _scenario_accel(scenario, "low"))
    high = cumulative_ocean_zj(t, BASE_RATE_HIGH_ZJ, _scenario_accel(scenario, "high"))
    total = ocean_to_total(ocean)
    return HeatProjection(
        year=year, years_ahead=t, scenario=scenario,
        ocean_zj=ocean, other_zj=total - ocean, total_zj=total,
        total_low_zj=ocean_to_total(low), total_high_zj=ocean_to_total(high),
    )


def series(end_year: int, scenario: str = "trend") -> list[HeatProjection]:
    """One projection per year from the base year up to ``end_year`` (for line charts)."""
    return [project(y, scenario) for y in range(BASE_YEAR, int(end_year) + 1)]
