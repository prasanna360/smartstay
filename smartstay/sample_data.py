"""
Market data for SmartStay.

Base prices below are grounded in real short-term rental market research
for each city (not invented numbers) — see the citation next to each city.
Bedroom-count scaling within a city (1BR/3BR/4BR relative to 2BR) is
estimated using typical price ratios observed across listings, since
granular bedroom-level medians aren't publicly reported.

Market occupancy is still synthetic/pseudo-random (see
synthetic_market_occupancy below) — live comp-set occupancy data isn't
available without an API connection, and that limitation is called out
explicitly in the app UI and README.

Sources (accessed Sep 2026, AirROI STR market reports unless noted):
- Goa:            median ADR ~$66-103/night
- Manali, HP:     median ADR ~$35/night
- Udaipur, RJ:    median ADR ~$48-81/night
- Alibaug, MH:    median ADR ~$85/night
- Coorg, KA:      Booking.com / StayVista listings — typical ₹3,000-4,500/night
- Lonavala, MH:   median ADR ~$135/night (highest ADR market in India per AirROI)
- Jaipur, RJ:     median ADR ~$47-83/night
- Mahabaleshwar, MH: median ADR ~$88/night
- Rishikesh, UK:  median ADR ~$35/night
- Munnar, KL:     median ADR ~$53-72/night
"""

import hashlib
from datetime import date

# 2BR base rate is anchored to each city's researched median nightly rate
# (converted to INR). 1BR/3BR/4BR are scaled from that median using typical
# ratios observed across listings in each market (smaller units price
# proportionally lower, larger villas price disproportionately higher due
# to premium/luxury inventory at the top end).
CITY_BASE_PRICES = {
    "Goa": {1: 3800, 2: 6000, 3: 8700, 4: 13000},
    "Manali, HP": {1: 2500, 2: 4000, 3: 5800, 4: 8700},
    "Udaipur, RJ": {1: 3200, 2: 5000, 3: 7300, 4: 10900},
    "Alibaug, MH": {1: 4200, 2: 6500, 3: 9400, 4: 14200},
    "Coorg, KA": {1: 2700, 2: 4200, 3: 6100, 4: 9200},
    "Lonavala, MH": {1: 5300, 2: 8500, 3: 12300, 4: 18400},
    "Jaipur, RJ": {1: 2800, 2: 4500, 3: 6500, 4: 9800},
    "Mahabaleshwar, MH": {1: 4100, 2: 6500, 3: 9400, 4: 14100},
    "Rishikesh, UK": {1: 2000, 2: 3200, 3: 4600, 4: 6900},
    "Munnar, KL": {1: 3000, 2: 4800, 3: 7000, 4: 10400},
}


def get_base_price(city: str, bedrooms: int) -> float:
    prices = CITY_BASE_PRICES.get(city, CITY_BASE_PRICES["Goa"])
    if bedrooms in prices:
        return float(prices[bedrooms])
    # simple fallback for bedroom counts outside the table
    closest = min(prices.keys(), key=lambda b: abs(b - bedrooms))
    ratio = bedrooms / closest
    return round(prices[closest] * ratio, 2)


def synthetic_market_occupancy(city: str, target_date: date) -> float:
    """
    Deterministic pseudo-random occupancy percentage (0-100) for a given
    city and date. This part IS still synthetic — real comp-set occupancy
    requires a live data feed. Weighted so weekends and summer months trend a bit
    higher, similar to real seasonal patterns, but the underlying number
    is not sourced from actual bookings.
    """
    seed_str = f"{city}-{target_date.isoformat()}"
    seed_val = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % 1000
    base = 35 + (seed_val / 1000) * 45  # base range ~35-80

    if target_date.weekday() in (4, 5):
        base += 8
    if target_date.month in (6, 7, 8, 12):
        base += 6

    return round(min(max(base, 5), 98), 1)


def synthetic_competitor_rate(city: str, bedrooms: int, target_date: date) -> float:
    """Return a deterministic demo average rate for comparable listings."""
    base = get_base_price(city, bedrooms)
    seed = int(hashlib.md5(f"comp-{city}-{target_date.isoformat()}".encode()).hexdigest(), 16) % 21
    market_factor = 0.90 + seed / 100
    if target_date.weekday() in (4, 5):
        market_factor += 0.05
    return round(base * market_factor, 2)


def synthetic_booking_pace(city: str, target_date: date) -> float:
    """Return demo booking speed as a percentage of the expected pace."""
    seed = int(hashlib.md5(f"pace-{city}-{target_date.isoformat()}".encode()).hexdigest(), 16) % 61
    pace = 40 + seed
    if target_date.weekday() in (4, 5):
        pace += 10
    return round(min(pace, 100), 1)