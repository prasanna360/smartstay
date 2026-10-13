"""
Lightweight sanity tests for the pricing engine — no pytest dependency
required, run directly with `python tests/test_pricing_engine.py`.
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from smartstay.pricing_engine import calculate_price, calculate_price_range

TODAY = date(2026, 9, 9)


def test_weekend_prices_higher_than_weekday():
    saturday = date(2026, 9, 12)
    tuesday = date(2026, 9, 15)
    sat_price = calculate_price(100, saturday, market_occupancy_pct=50, today=TODAY).final_price
    tue_price = calculate_price(100, tuesday, market_occupancy_pct=50, today=TODAY).final_price
    assert sat_price > tue_price, "Weekend price should exceed midweek price"


def test_event_date_increases_price():
    nye = date(2026, 12, 31)
    plain_date = date(2026, 12, 3)
    nye_price = calculate_price(100, nye, market_occupancy_pct=50, today=TODAY).final_price
    plain_price = calculate_price(100, plain_date, market_occupancy_pct=50, today=TODAY).final_price
    assert nye_price > plain_price, "New Year's Eve should price higher than a plain December date"


def test_guardrails_are_respected():
    high_demand_date = date(2026, 12, 31)
    result = calculate_price(100, high_demand_date, market_occupancy_pct=95, today=TODAY, max_price=150)
    assert result.final_price <= 150, "Price should never exceed the max_price guardrail"

    low_demand_date = date(2027, 1, 15)
    result2 = calculate_price(100, low_demand_date, market_occupancy_pct=10, today=TODAY, min_price=90)
    assert result2.final_price >= 90, "Price should never drop below the min_price guardrail"


def test_high_occupancy_increases_price():
    d = date(2026, 9, 22)
    high_occ = calculate_price(100, d, market_occupancy_pct=90, today=TODAY).final_price
    low_occ = calculate_price(100, d, market_occupancy_pct=20, today=TODAY).final_price
    assert high_occ > low_occ, "Higher market occupancy should push price up"


def test_seasonality_varies_by_market():
    d = date(2026, 6, 15)
    manali = calculate_price(100, d, market_occupancy_pct=50, today=TODAY, market="Manali, HP")
    jaipur = calculate_price(100, d, market_occupancy_pct=50, today=TODAY, market="Jaipur, RJ")
    assert manali.seasonality_multiplier > jaipur.seasonality_multiplier


def test_competitor_position_adjusts_price():
    d = date(2027, 2, 10)
    below_market = calculate_price(80, d, 50, today=TODAY, competitor_rate=100)
    above_market = calculate_price(120, d, 50, today=TODAY, competitor_rate=100)
    assert below_market.competitor_multiplier == 1.05
    assert above_market.competitor_multiplier == 0.95


def test_booking_pace_adjusts_price():
    d = date(2027, 2, 10)
    fast = calculate_price(100, d, 50, today=TODAY, booking_pace_pct=90)
    slow = calculate_price(100, d, 50, today=TODAY, booking_pace_pct=20)
    assert fast.booking_pace_multiplier > slow.booking_pace_multiplier


def test_market_event_can_override_shared_event():
    diwali = date(2026, 10, 21)
    manali = calculate_price(100, diwali, 50, today=TODAY, market="Manali, HP")
    jaipur = calculate_price(100, diwali, 50, today=TODAY, market="Jaipur, RJ")
    assert jaipur.event_multiplier > manali.event_multiplier


def test_calculate_price_range_returns_correct_length():
    results = calculate_price_range(100, TODAY, 30, lambda d: 50.0, today=TODAY)
    assert len(results) == 30, "Should return exactly 30 priced nights"


def test_explain_is_human_readable_string():
    result = calculate_price(150, date(2026, 12, 31), market_occupancy_pct=85, today=TODAY)
    explanation = result.explain()
    assert isinstance(explanation, str) and len(explanation) > 10


if __name__ == "__main__":
    tests = [obj for name, obj in list(globals().items()) if name.startswith("test_")]
    passed, failed = 0, 0
    for t in tests:
        try:
            t()
            print(f"PASS: {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL: {t.__name__} -> {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
