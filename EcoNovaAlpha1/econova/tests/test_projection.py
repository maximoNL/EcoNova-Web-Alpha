"""Projection maths: exact 85/15 split, sourced constants, sensible growth."""
import pytest

from src import projection as pj


def test_split_is_always_exactly_85_15():
    for year in (2026, 2030, 2050, 2075):
        for scenario in pj.SCENARIOS:
            p = pj.project(year, scenario)
            assert p.ocean_zj == pytest.approx(p.total_zj * 0.85)
            assert p.other_zj == pytest.approx(p.total_zj * 0.15)
            assert p.ocean_zj + p.other_zj == pytest.approx(p.total_zj)


def test_unit_conversion_matches_published_numbers():
    assert pj.ZJ_PER_W_M2_YEAR == pytest.approx(16.1, abs=0.1)
    # 23 ZJ is described in the source as about 37 years of 2023 world energy use
    assert 23 / pj.WORLD_ENERGY_ZJ_PER_YEAR == pytest.approx(37, abs=0.5)


def test_acceleration_range_matches_study():
    a = pj.ACCEL_W_M2_PER_DECADE
    assert a["central"] == pytest.approx(0.32)
    assert a["low"] == pytest.approx(0.18) and a["high"] == pytest.approx(0.46)


def test_heat_grows_with_the_slider_and_trend_beats_steady():
    totals = [pj.project(y, "trend").total_zj for y in range(2026, 2076)]
    assert all(b > a for a, b in zip(totals, totals[1:]))
    for year in (2030, 2050, 2075):
        assert pj.project(year, "trend").total_zj > pj.project(year, "steady").total_zj


def test_band_contains_central_value():
    for scenario in pj.SCENARIOS:
        for year in (2030, 2050, 2075):
            p = pj.project(year, scenario)
            assert p.total_low_zj <= p.total_zj <= p.total_high_zj


def test_first_year_is_close_to_observed_2025_gain():
    assert pj.project(2026, "steady").ocean_zj == pytest.approx(pj.BASE_OCEAN_RATE_ZJ)


def test_series_length_and_year_clamping():
    assert len(pj.series(2040)) == 2040 - pj.BASE_YEAR + 1
    assert pj.project(3000).year == pj.MAX_YEAR
