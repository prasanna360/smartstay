"""
SmartStay Pricing Engine
=========================
A simplified dynamic pricing engine for vacation rentals, inspired by
PriceLabs' approach to revenue management: take a base nightly rate and
adjust it up or down based on the factors that actually drive demand for
short-term rentals — day of week, seasonality, how far out the date is,
local events, and current market occupancy.

The goal isn't to be a perfect forecasting model. It's to be *explainable*:
every price the engine outputs comes with a plain-English reason, because
in the real world a host or property manager needs to trust a
recommendation before they'll act on it.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional


# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

# A small sample of high-demand dates. In a real product this would be a
# live feed of local events, concerts, conferences, and holidays pulled
# per-market (this is essentially what PriceLabs' "Hyper Local Pulse" does
# at a much larger scale).
DEMAND_EVENTS = {
    date(2026, 10, 20): ("Diwali week", 1.45),
    date(2026, 10, 21): ("Diwali", 1.60),
    date(2026, 12, 24): ("Christmas Eve", 1.35),
    date(2026, 12, 25): ("Christmas Day", 1.30),
    date(2026, 12, 31): ("New Year's Eve", 1.60),
    date(2027, 1, 1): ("New Year's Day", 1.35),
    date(2027, 3, 4): ("Holi", 1.30),
}

MARKET_EVENTS = {
    "Manali, HP": {
        date(2026, 12, 24): ("Manali winter snow season", 1.25),
        date(2027, 1, 15): ("Manali winter snow season", 1.30),
    },
    "Jaipur, RJ": {
        date(2026, 10, 21): ("Jaipur Diwali celebrations", 1.70),
        date(2027, 1, 23): ("Jaipur Literature Festival", 1.25),
    },
    "Goa": {
        date(2026, 12, 31): ("Goa New Year's celebrations", 1.80),
    },
}

# Seasonality multiplier by month (1 = January ... 12 = December).
# Loosely modeled on a warm-weather leisure market where summer and
# major holidays are peak season and late winter is the trough.
SEASONALITY_BY_MONTH = {
    1: 0.85,
    2: 0.85,
    3: 1.05,
    4: 1.05,
    5: 1.10,
    6: 1.25,
    7: 1.30,
    8: 1.20,
    9: 1.00,
    10: 1.05,
    11: 0.95,
    12: 1.15,
}

# Market-specific demand profiles based on each destination's climate and tourism pattern.
SEASONALITY_BY_MARKET = {
    "Manali, HP": {1: 1.25, 2: 1.20, 3: 1.00, 4: 0.95, 5: 1.00, 6: 1.05, 7: 0.80, 8: 0.80, 9: 0.95, 10: 1.15, 11: 1.20, 12: 1.35},
    "Jaipur, RJ": {1: 1.25, 2: 1.20, 3: 1.10, 4: 0.95, 5: 0.75, 6: 0.70, 7: 0.80, 8: 0.85, 9: 0.95, 10: 1.10, 11: 1.25, 12: 1.30},
    "Goa": {1: 1.20, 2: 1.15, 3: 1.05, 4: 1.00, 5: 0.90, 6: 0.85, 7: 0.90, 8: 0.90, 9: 0.95, 10: 1.05, 11: 1.20, 12: 1.35},
    "Udaipur, RJ": {1: 1.20, 2: 1.15, 3: 1.05, 4: 0.95, 5: 0.75, 6: 0.70, 7: 0.80, 8: 0.85, 9: 0.95, 10: 1.10, 11: 1.25, 12: 1.30},
    "Alibaug, MH": {1: 1.10, 2: 1.10, 3: 1.05, 4: 1.05, 5: 1.00, 6: 1.10, 7: 1.15, 8: 1.10, 9: 1.05, 10: 1.05, 11: 1.10, 12: 1.20},
    "Coorg, KA": {1: 1.05, 2: 1.05, 3: 1.00, 4: 0.95, 5: 1.00, 6: 1.10, 7: 1.15, 8: 1.15, 9: 1.10, 10: 1.05, 11: 1.10, 12: 1.20},
    "Lonavala, MH": {1: 1.05, 2: 1.05, 3: 1.00, 4: 1.00, 5: 0.95, 6: 1.10, 7: 1.20, 8: 1.20, 9: 1.10, 10: 1.05, 11: 1.10, 12: 1.20},
    "Mahabaleshwar, MH": {1: 1.10, 2: 1.05, 3: 1.00, 4: 0.95, 5: 0.90, 6: 1.10, 7: 1.20, 8: 1.20, 9: 1.10, 10: 1.05, 11: 1.10, 12: 1.20},
    "Rishikesh, UK": {1: 1.00, 2: 1.05, 3: 1.15, 4: 1.20, 5: 1.10, 6: 0.95, 7: 0.75, 8: 0.75, 9: 0.90, 10: 1.15, 11: 1.20, 12: 1.00},
    "Munnar, KL": {1: 1.05, 2: 1.05, 3: 1.00, 4: 0.95, 5: 0.90, 6: 1.00, 7: 1.10, 8: 1.10, 9: 1.05, 10: 1.00, 11: 1.10, 12: 1.20},
}

# Friday/Saturday nights command a premium; Sunday-Thursday are discounted
# slightly to encourage midweek bookings and keep the calendar filled.
DAY_OF_WEEK_MULTIPLIER = {
    0: 0.95,  # Monday
    1: 0.95,  # Tuesday
    2: 0.95,  # Wednesday
    3: 1.00,  # Thursday
    4: 1.20,  # Friday
    5: 1.25,  # Saturday
    6: 1.05,  # Sunday
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class PriceBreakdown:
    """Every factor that went into a price, plus the reasons a human can read."""
    base_price: float
    final_price: float
    seasonality_multiplier: float
    day_of_week_multiplier: float
    lead_time_multiplier: float
    event_multiplier: float
    occupancy_multiplier: float
    competitor_multiplier: float
    booking_pace_multiplier: float
    reasons: list = field(default_factory=list)

    @property
    def total_multiplier(self) -> float:
        return round(self.final_price / self.base_price, 3) if self.base_price else 0

    def explain(self) -> str:
        pct_change = round((self.total_multiplier - 1) * 100)
        direction = "above" if pct_change >= 0 else "below"
        header = f"Priced {abs(pct_change)}% {direction} base rate (₹{self.base_price:.0f} -> ₹{self.final_price:.0f})."
        return header + " " + " ".join(self.reasons)


# ---------------------------------------------------------------------------
# Individual factor calculations
# ---------------------------------------------------------------------------

def seasonality_multiplier(target_date: date, market: Optional[str] = None) -> tuple[float, Optional[str]]:
    monthly_profile = SEASONALITY_BY_MARKET.get(market, SEASONALITY_BY_MONTH)
    m = monthly_profile[target_date.month]
    if m >= 1.20:
        reason = f"It's peak season ({target_date.strftime('%B')}), a high-demand month."
    elif m <= 0.90:
        reason = f"It's low season ({target_date.strftime('%B')}), so demand is typically softer."
    else:
        reason = None
    return m, reason


def day_of_week_multiplier(target_date: date) -> tuple[float, Optional[str]]:
    weekday = target_date.weekday()
    m = DAY_OF_WEEK_MULTIPLIER[weekday]
    if weekday in (4, 5):
        reason = f"{target_date.strftime('%A')} nights are in high demand."
    elif m < 1.0:
        reason = f"{target_date.strftime('%A')} is a midweek night, priced to encourage bookings."
    else:
        reason = None
    return m, reason


def lead_time_multiplier(target_date: date, today: date) -> tuple[float, Optional[str]]:
    """
    Far-out dates get a small discount to encourage early bookings and fill
    the calendar. Very last-minute dates that are still open get a small
    discount too (better to book at a lower rate than leave the night empty).
    Dates 1-3 weeks out get a slight premium since that's typically when
    demand is most price-inelastic.
    """
    days_out = (target_date - today).days

    if days_out < 0:
        return 1.0, None
    if days_out <= 2:
        return 0.90, "This date is very last-minute and still open, so it's discounted to attract a booking."
    if days_out <= 21:
        return 1.08, "This date is inside the typical booking window, where demand tends to be strongest."
    if days_out >= 180:
        return 0.92, "This date is far in advance, priced to encourage early booking."
    return 1.0, None


def event_multiplier(target_date: date, market: Optional[str] = None) -> tuple[float, Optional[str]]:
    event = MARKET_EVENTS.get(market, {}).get(target_date) or DEMAND_EVENTS.get(target_date)
    if event:
        name, mult = event
        return mult, f"{name} falls on this date, driving significant local demand."
    return 1.0, None


def occupancy_multiplier(market_occupancy_pct: float) -> tuple[float, Optional[str]]:
    """
    market_occupancy_pct: how full comparable listings in the area are for
    this date, from 0-100. This stands in for the live comp-set data
    PriceLabs pulls in production — here it's a number you pass in yourself
    (see sample_data.py for a synthetic generator).
    """
    if market_occupancy_pct >= 80:
        return 1.15, f"Comparable listings in the area are {market_occupancy_pct:.0f}% booked, signaling strong demand."
    if market_occupancy_pct <= 35:
        return 0.90, f"Comparable listings in the area are only {market_occupancy_pct:.0f}% booked, signaling soft demand."
    return 1.0, None


def competitor_multiplier(base_price: float, competitor_rate: Optional[float]) -> tuple[float, Optional[str]]:
    """Compare the host's base rate with a comparable-listing average."""
    if not competitor_rate or competitor_rate <= 0:
        return 1.0, None
    if base_price > competitor_rate * 1.10:
        return 0.95, f"Your base rate is about {((base_price / competitor_rate) - 1) * 100:.0f}% above comparable listings, so it is softened."
    if base_price < competitor_rate * 0.90:
        return 1.05, f"Your base rate is about {((competitor_rate / base_price) - 1) * 100:.0f}% below comparable listings, so there is room to increase it."
    return 1.0, "Your base rate is close to the comparable-listing average."


def booking_pace_multiplier(booking_pace_pct: Optional[float]) -> tuple[float, Optional[str]]:
    """Adjust for how quickly this date is booking versus its expected pace."""
    if booking_pace_pct is None:
        return 1.0, None
    if booking_pace_pct >= 80:
        return 1.10, f"This date is booking quickly at {booking_pace_pct:.0f}% of its expected pace."
    if booking_pace_pct <= 30:
        return 0.92, f"This date is booking slowly at {booking_pace_pct:.0f}% of its expected pace."
    return 1.0, None


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def calculate_price(
    base_price: float,
    target_date: date,
    market_occupancy_pct: float,
    today: Optional[date] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    market: Optional[str] = None,
    competitor_rate: Optional[float] = None,
    booking_pace_pct: Optional[float] = None,
) -> PriceBreakdown:
    """
    Calculate a recommended nightly rate for a single date.

    Args:
        base_price: the host's baseline nightly rate for this property.
        target_date: the date being priced.
        market_occupancy_pct: 0-100, how booked-up comparable listings are.
        today: defaults to date.today(); overridable for testing/demo.
        min_price / max_price: optional guardrails a host can set so the
            engine never prices below/above their comfort zone — mirrors
            PriceLabs' "full control over final prices" principle.
        market: optional destination name used for location-specific seasonality.
        competitor_rate: optional average rate for comparable listings.
        booking_pace_pct: optional booking speed versus the expected pace, 0-100.
    """
    today = today or date.today()

    season_m, season_reason = seasonality_multiplier(target_date, market)
    dow_m, dow_reason = day_of_week_multiplier(target_date)
    lead_m, lead_reason = lead_time_multiplier(target_date, today)
    event_m, event_reason = event_multiplier(target_date, market)
    occ_m, occ_reason = occupancy_multiplier(market_occupancy_pct)
    comp_m, comp_reason = competitor_multiplier(base_price, competitor_rate)
    pace_m, pace_reason = booking_pace_multiplier(booking_pace_pct)

    total_multiplier = season_m * dow_m * lead_m * event_m * occ_m * comp_m * pace_m
    raw_price = base_price * total_multiplier

    final_price = raw_price
    guardrail_note = None
    if min_price is not None and final_price < min_price:
        final_price = min_price
        guardrail_note = f"Capped at your minimum price of ₹{min_price:.0f}."
    if max_price is not None and final_price > max_price:
        final_price = max_price
        guardrail_note = f"Capped at your maximum price of ₹{max_price:.0f}."

    reasons = [r for r in (event_reason, dow_reason, season_reason, lead_reason, occ_reason, comp_reason, pace_reason) if r]
    if guardrail_note:
        reasons.append(guardrail_note)
    if not reasons:
        reasons.append("No major demand signals for this date — priced near your base rate.")

    return PriceBreakdown(
        base_price=base_price,
        final_price=round(final_price, 2),
        seasonality_multiplier=season_m,
        day_of_week_multiplier=dow_m,
        lead_time_multiplier=lead_m,
        event_multiplier=event_m,
        occupancy_multiplier=occ_m,
        competitor_multiplier=comp_m,
        booking_pace_multiplier=pace_m,
        reasons=reasons,
    )


def calculate_price_range(
    base_price: float,
    start_date: date,
    num_nights: int,
    market_occupancy_lookup,
    today: Optional[date] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    market: Optional[str] = None,
    competitor_rate_lookup=None,
    booking_pace_lookup=None,
) -> list[tuple[date, PriceBreakdown]]:
    """
    Convenience helper to price a stretch of nights at once — this is what
    powers the calendar view in the Streamlit app.

    market_occupancy_lookup: a callable date -> float (0-100), or a dict.
    """
    results = []
    for i in range(num_nights):
        d = start_date + timedelta(days=i)
        if callable(market_occupancy_lookup):
            occ = market_occupancy_lookup(d)
        else:
            occ = market_occupancy_lookup.get(d, 50.0)
        comp_rate = competitor_rate_lookup(d) if callable(competitor_rate_lookup) else None
        pace = booking_pace_lookup(d) if callable(booking_pace_lookup) else None
        results.append((d, calculate_price(base_price, d, occ, today, min_price, max_price, market, comp_rate, pace)))
    return results
