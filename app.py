"""
SmartStay — Dynamic Pricing Demo
==================================
Run with:  streamlit run app.py

A small interactive front end for the SmartStay pricing engine, pick a
property, see a recommended price for a date or a whole month, and read
a plain-English reason for every number.

The interface uses a minimal, focused layout so pricing and its explanation
remain the primary focus.
"""

from datetime import date, timedelta
from html import escape

import pandas as pd
import streamlit as st

from smartstay.pricing_engine import calculate_price, calculate_price_range
from smartstay.sample_data import (
    CITY_BASE_PRICES,
    get_base_price,
    synthetic_booking_pace,
    synthetic_competitor_rate,
    synthetic_market_occupancy,
)

st.set_page_config(
    page_title="SmartStay Pricing Demo",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom styling — minimal dashboard
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'DM Sans', sans-serif;
        }

        :root {
            --ink: light-dark(#202923, #e6ebe7);
            --navy: light-dark(#315b49, #244333);
            --muted: light-dark(#707b74, #a4b0a8);
            --border: light-dark(#e4e8e4, #353d38);
            --paper: light-dark(#f7f8f6, #111613);
            --white: light-dark(#ffffff, #1a211d);
            --mint: light-dark(#ffffff, #1a211d);
            --mint-ink: light-dark(#315b49, #c1dcca);
            --peach: light-dark(#ffffff, #1a211d);
            --peach-ink: light-dark(#4b5b51, #d1d8d2);
            --lavender: light-dark(#ffffff, #1a211d);
            --lavender-ink: light-dark(#4b5b51, #d1d8d2);
            --sky: light-dark(#ffffff, #1a211d);
            --sky-ink: light-dark(#4b5b51, #d1d8d2);
            --lemon: light-dark(#ffffff, #1a211d);
            --lemon-ink: light-dark(#4b5b51, #d1d8d2);
            --coral: light-dark(#63836f, #91b39a);
        }

        .stApp {
            background: var(--paper);
            color: var(--ink);
        }

        header[data-testid="stHeader"] {
            background: var(--paper);
        }

        .block-container, [data-testid="stAppViewBlockContainer"] {
            padding-top: 4.25rem !important;
            padding-bottom: 2.5rem;
            max-width: 1280px;
        }

        h1, h2, h3, h4, .brand-name, .tile-value {
            font-family: 'DM Sans', sans-serif !important;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background: light-dark(#f1f3f0, #171e1a);
            border-right: 1px solid var(--border);
            box-shadow: none;
        }
        section[data-testid="stSidebar"] > div:first-child {
            padding-top: 2.1rem;
        }
        section[data-testid="stSidebar"] [data-baseweb="select"] > div,
        section[data-testid="stSidebar"] input {
            border-radius: 10px !important;
            border: 1px solid var(--border) !important;
            box-shadow: none !important;
        }
        section[data-testid="stSidebar"] [data-baseweb="select"] > div {
            background-color: var(--white) !important;
        }
        section[data-testid="stSidebar"] [data-baseweb="select"] svg {
            fill: var(--muted) !important;
        }
        .sidebar-heading {
            display: flex;
            align-items: center;
            margin-bottom: 1.2rem;
        }
        .sidebar-heading .label {
            font-weight: 700;
            color: var(--ink);
            font-size: 1rem;
        }
        section[data-testid="stSidebar"] hr {
            border-color: var(--border) !important;
            margin: 1.6rem 0 !important;
        }
        section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
            padding: 0.8rem 0.7rem;
            background: rgba(255, 255, 255, 0.48);
            border-left: 3px solid #9bcbb5;
            border-radius: 0 6px 6px 0;
        }

        /* Top bar */
        .topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            min-height: 48px;
            margin-bottom: 0.5rem;
            padding: 0.35rem 0 0.85rem;
            border-bottom: 1px solid var(--border);
        }
        .topbar .brand {
            display: flex;
            align-items: center;
        }
        .topbar .brand-copy {
            display: flex;
            flex-direction: column;
            gap: 0.1rem;
        }
        .topbar .brand-kicker {
            color: var(--coral) !important;
            font-size: 0.62rem;
            font-weight: 700;
            letter-spacing: 0.14em;
            text-transform: uppercase;
        }

        /* Keep app-authored text readable without overriding card-specific text colors. */
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p,
        .stApp [data-testid="stMarkdownContainer"] p:not(.subhead),
        .stApp [data-testid="stCaptionContainer"] p,
        .stApp [data-testid="stWidgetLabel"] label {
            color: var(--ink) !important;
        }
        section[data-testid="stSidebar"] input,
        section[data-testid="stSidebar"] [data-baseweb="select"] span {
            color: var(--ink) !important;
            background-color: var(--white) !important;
        }
        .topbar .brand-name {
            font-weight: 800;
            font-size: 1.5rem;
            color: var(--ink);
        }
        .topbar .pill {
            background: var(--navy);
            color: white;
            padding: 0.42rem 0.85rem;
            border-radius: 5px;
            font-size: 0.78rem;
            font-weight: 600;
            letter-spacing: 0.02em;
        }
        .topbar .pill::before {
            content: "";
            display: inline-block;
            width: 6px;
            height: 6px;
            margin: 0 0.45rem 1px 0;
            border-radius: 50%;
            background: #8de0b7;
        }
        .subhead {
            color: var(--muted);
            font-size: 1rem;
            margin: 0 0 1.7rem 0;
            max-width: 680px;
            letter-spacing: 0.005em;
            line-height: 1.65;
        }

        .demo-note {
            margin: 0 0 1.25rem;
            padding: 0.7rem 0.9rem;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: light-dark(rgba(255, 255, 255, 0.72), rgba(26, 33, 29, 0.9));
            color: var(--muted);
            font-size: 0.84rem;
            line-height: 1.5;
        }
        .demo-note strong {
            color: var(--ink);
            font-weight: 700;
        }

        .dashboard-kicker {
            color: var(--muted) !important;
            font-size: 0.7rem;
            font-weight: 700;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            margin: 1.35rem 0 0.45rem;
        }

        h3, h4 {
            font-weight: 800 !important;
            color: var(--ink) !important;
        }

        /* ---- Bento tiles (pure HTML cards) ---- */
        .bento-tile {
            border-radius: 12px;
            padding: 1.25rem 1.35rem;
            height: 100%;
            box-sizing: border-box;
            position: relative;
            overflow: hidden;
            border: 1px solid var(--border);
            box-shadow: none;
        }
        .bento-tile .tile-label {
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.09em;
            opacity: 0.75;
            margin-bottom: 0.5rem;
        }
        .bento-tile .tile-value {
            font-size: 2.45rem;
            font-weight: 700;
            line-height: 1.05;
            letter-spacing: -0.035em;
        }
        .bento-tile .tile-sub {
            font-size: 0.86rem;
            font-weight: 600;
            margin-top: 0.5rem;
            opacity: 0.85;
        }
        .bento-tile.hero .tile-value { font-size: 3.45rem; }

        .tile-mint    { background: var(--mint);     color: var(--mint-ink); }
        .tile-peach   { background: var(--peach);    color: var(--peach-ink); }
        .tile-lavender{ background: var(--lavender); color: var(--lavender-ink); }
        .tile-sky     { background: var(--sky);      color: var(--sky-ink); }
        .tile-lemon   { background: var(--lemon);    color: var(--lemon-ink); }
        .tile-dark    {
            background: var(--navy);
            color: white;
            border-color: var(--navy);
            box-shadow: none;
        }
        .tile-dark::after {
            content: none;
        }

        .reason-tile {
            border-radius: 12px;
            padding: 1rem 1.2rem;
            background: var(--white);
            border: 1px solid var(--border);
            border-left: 3px solid var(--coral);
            font-size: 0.91rem;
            line-height: 1.55;
            color: var(--ink);
            margin-bottom: 1.5rem;
            box-shadow: none;
        }
        .reason-tile b { color: var(--mint-ink); }
        .reason-title {
            display: block;
            margin-bottom: 0.3rem;
            color: var(--muted);
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        /* Bordered containers used for widget-holding cards */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 12px !important;
            border: 1px solid var(--border) !important;
            background: var(--white);
            padding: 0.65rem;
            box-shadow: none;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:focus-within {
            border-color: var(--coral) !important;
            box-shadow: 0 0 0 2px rgba(71, 126, 95, 0.1);
        }

        .card-header {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-weight: 700;
            font-size: 0.93rem;
            color: var(--ink);
            margin-bottom: 0.7rem;
        }
        .card-header .dot {
            width: 7px; height: 7px; border-radius: 50%;
        }
        .dot-mint, .dot-peach, .dot-lavender, .dot-sky { background: var(--coral); }

        /* Tabs */
        button[data-baseweb="tab"] {
            font-weight: 600;
            font-size: 0.9rem;
            color: var(--muted);
            padding: 0.55rem 0.9rem !important;
            border-radius: 0;
        }
        button[data-baseweb="tab"][aria-selected="true"] { color: var(--ink) !important; }
        div[data-baseweb="tab-highlight"] { background-color: var(--coral) !important; height: 3px !important; }
        div[data-baseweb="tab-border"] { background-color: var(--border) !important; }

        div[data-baseweb="tab-list"] {
            gap: 0.3rem;
            border-bottom: 1px solid var(--border);
        }
        button[data-baseweb="tab"]:hover {
            background: rgba(99, 131, 111, 0.06);
            color: var(--ink) !important;
        }

        div[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; border: 1px solid var(--border); }

        .calendar-table-wrap {
            overflow-x: auto;
            border: 1px solid var(--border);
            border-radius: 10px;
        }
        .calendar-table {
            width: 100%;
            border-collapse: collapse;
            color: var(--ink);
            background: var(--white);
            font-size: 0.9rem;
        }
        .calendar-table th {
            padding: 0.8rem 1rem;
            border-bottom: 1px solid var(--border);
            background: light-dark(#f4f6f4, #202923);
            color: var(--muted);
            text-align: left;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            white-space: nowrap;
        }
        .calendar-table td {
            padding: 0.72rem 1rem;
            border-bottom: 1px solid var(--border);
            vertical-align: middle;
        }
        .calendar-table tbody tr:last-child td { border-bottom: 0; }
        .calendar-table tbody tr:hover { background: light-dark(#f7f9f7, #202923); }
        .calendar-table .calendar-date { font-weight: 600; white-space: nowrap; }
        .calendar-table .calendar-rate { font-weight: 700; white-space: nowrap; }
        .calendar-table .calendar-change { font-variant-numeric: tabular-nums; }
        .calendar-table .increase { color: light-dark(#26734d, #8bd0a5); }
        .calendar-table .decrease { color: light-dark(#a34d45, #e39a91); }
        .calendar-table .unchanged { color: var(--muted); }

        [data-testid="stDateInput"] input,
        [data-testid="stNumberInput"] input {
            border-radius: 8px !important;
            background: var(--white) !important;
            color: var(--ink) !important;
        }
        [data-testid="stDateInput"] input:focus,
        [data-testid="stNumberInput"] input:focus {
            border-color: var(--coral) !important;
            box-shadow: 0 0 0 2px rgba(99, 131, 111, 0.12) !important;
        }

        [data-testid="stMarkdownContainer"] p,
        [data-testid="stCaptionContainer"] p {
            line-height: 1.5;
        }

        .footer-note {
            text-align: center;
            color: var(--muted);
            font-size: 0.85rem;
            padding: 1.35rem 0 0.35rem 0;
            border-top: 1px solid var(--border);
            margin-top: 2rem;
        }

        @media (max-width: 700px) {
            .block-container, [data-testid="stAppViewBlockContainer"] {
                padding-top: 3.25rem !important;
            }
            .topbar {
                align-items: flex-start;
                gap: 0.75rem;
                flex-wrap: wrap;
            }
            .topbar .pill {
                margin-left: 48px;
            }
            .bento-tile.hero .tile-value {
                font-size: 2.7rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def tile(label, value, sub, css_class):
    return f"""
    <div class="bento-tile {css_class}">
        <div class="tile-label">{label}</div>
        <div class="tile-value">{value}</div>
        <div class="tile-sub">{sub}</div>
    </div>
    """


def card_header(dot_class, text):
    st.markdown(f'<div class="card-header"><span class="dot {dot_class}"></span>{text}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Top bar
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="topbar">
        <div class="brand">
            <div class="brand-copy">
                <span class="brand-kicker">Revenue workspace</span>
                <span class="brand-name">SmartStay</span>
            </div>
        </div>
        <div class="pill">Pricing demo</div>
    </div>
    <div class="dashboard-kicker">SmartStay / Pricing</div>
    <p class="subhead">Explore an explainable nightly price recommendation. Choose a market and property details, then select a stay date or view the next 30 days.</p>
    <div class="demo-note"><strong>Illustrative demo:</strong> Market, occupancy, and comparable-rate figures are synthetic examples—not live market data.</div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar — property inputs
# ---------------------------------------------------------------------------
st.sidebar.markdown(
    """
    <div class="sidebar-heading">
        <div class="label">Property Details</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.sidebar.caption(
    "How to use: choose a market and set your property details, then select "
    "a date or open the 30-day calendar."
)

city = st.sidebar.selectbox("Market", list(CITY_BASE_PRICES.keys()))
bedrooms = st.sidebar.selectbox("Bedrooms", [1, 2, 3, 4], index=1)

suggested_base = get_base_price(city, bedrooms)
base_price = st.sidebar.number_input(
    "Your base nightly rate (₹)",
    min_value=20.0,
    value=float(suggested_base),
    step=5.0,
    help="What you'd normally charge before any demand-based adjustment.",
)

use_guardrails = st.sidebar.checkbox("Set min/max price guardrails", value=False)
min_price = max_price = None
if use_guardrails:
    min_price = st.sidebar.number_input("Minimum price (₹)", value=round(base_price * 0.7, 0))
    max_price = st.sidebar.number_input("Maximum price (₹)", value=round(base_price * 2.0, 0))

st.sidebar.divider()
st.sidebar.caption(
    "Demo only: market rates, occupancy, booking pace, and comparable prices "
    "are synthetic and are not live market data."
)

today = date.today()

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab1, tab2 = st.tabs(["Single Date", "30-Day Calendar"])

with tab1:
    # --- date picker card ---
    with st.container(border=True):
        card_header("dot-sky", "Date to price")
        target_date = st.date_input(
            "Date",
            value=today + timedelta(days=14),
            min_value=today,
            max_value=today + timedelta(days=365),
            label_visibility="collapsed",
        )

    st.write("")

    occ = synthetic_market_occupancy(city, target_date)
    competitor_rate = synthetic_competitor_rate(city, bedrooms, target_date)
    booking_pace = synthetic_booking_pace(city, target_date)
    result = calculate_price(
        base_price, target_date, occ, today=today,
        min_price=min_price, max_price=max_price, market=city,
        competitor_rate=competitor_rate, booking_pace_pct=booking_pace,
    )
    pct = round((result.total_multiplier - 1) * 100)
    pct_str = f"{'+' if pct >= 0 else ''}{pct}% vs base"
    if base_price > competitor_rate * 1.10:
        market_position = "Above comparable market"
    elif base_price < competitor_rate * 0.90:
        market_position = "Below comparable market"
    else:
        market_position = "Near comparable market"

    # --- bento row: hero price tile (wide) + two stacked tiles ---
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown(
            tile("Recommended Price", f"₹{result.final_price:,.0f}", pct_str, "tile-dark hero"),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(tile("Base Price", f"₹{result.base_price:,.0f}", city, "tile-mint"), unsafe_allow_html=True)
        st.write("")
        st.markdown(
            tile("Comparable Rate", f"₹{competitor_rate:,.0f}", market_position, "tile-lemon"),
            unsafe_allow_html=True,
        )
        st.write("")
        st.markdown(tile("Market Occupancy", f"{occ:.0f}%", "comparable listings booked", "tile-peach"), unsafe_allow_html=True)

    st.write("")

    st.markdown(
        f'<div class="reason-tile"><span class="reason-title">Why this price</span>{result.explain()}</div>',
        unsafe_allow_html=True,
    )

    # --- bento row: breakdown table + quick facts ---
    c3, c4 = st.columns([2, 1])
    with c3:
        with st.container(border=True):
            card_header("dot-lavender", "Price factor breakdown")
            breakdown_df = pd.DataFrame(
                {
                    "Factor": ["Seasonality", "Day of Week", "Lead Time", "Local Event", "Market Occupancy", "Competitor Position", "Booking Pace"],
                    "Multiplier": [
                        result.seasonality_multiplier,
                        result.day_of_week_multiplier,
                        result.lead_time_multiplier,
                        result.event_multiplier,
                        result.occupancy_multiplier,
                        result.competitor_multiplier,
                        result.booking_pace_multiplier,
                    ],
                }
            )
            st.dataframe(breakdown_df, hide_index=True, use_container_width=True)
    with c4:
        st.markdown(
            tile("Day of Week", target_date.strftime("%A"), target_date.strftime("%b %d, %Y"), "tile-lavender"),
            unsafe_allow_html=True,
        )
        st.write("")
        st.markdown(
            tile("Bedrooms", f"{bedrooms} BR", f"{city}", "tile-sky"),
            unsafe_allow_html=True,
        )
        st.write("")
        st.markdown(
            tile("Booking Pace", f"{booking_pace:.0f}%", "of expected bookings", "tile-peach"),
            unsafe_allow_html=True,
        )

with tab2:
    start = today + timedelta(days=1)
    priced = calculate_price_range(
        base_price, start, 30, lambda d: synthetic_market_occupancy(city, d),
        today=today, min_price=min_price, max_price=max_price, market=city,
        competitor_rate_lookup=lambda d: synthetic_competitor_rate(city, bedrooms, d),
        booking_pace_lookup=lambda d: synthetic_booking_pace(city, d),
    )
    prices_only = [result.final_price for _, result in priced]
    avg_price = sum(prices_only) / len(prices_only)
    lowest_day, lowest_result = min(priced, key=lambda item: item[1].final_price)
    highest_day, highest_result = max(priced, key=lambda item: item[1].final_price)

    st.markdown(
        f'<div class="dashboard-kicker">{city} / Next 30 nights</div>'
        '<p class="subhead">A day-by-day view of recommended nightly benchmarks for this property.</p>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            tile("Average nightly rate", f"₹{avg_price:,.0f}", "across 30 nights", "tile-dark"),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            tile("Lowest night", f"₹{lowest_result.final_price:,.0f}", lowest_day.strftime("%a, %b %d"), "tile-mint"),
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            tile("Highest night", f"₹{highest_result.final_price:,.0f}", highest_day.strftime("%a, %b %d"), "tile-peach"),
            unsafe_allow_html=True,
        )

    st.write("")

    with st.container(border=True):
        card_header("dot-sky", "Nightly rate trend")
        date_labels = [day.strftime("%b %d") for day, _ in priced]
        chart_df = pd.DataFrame(
            {
                "Date": pd.Categorical(date_labels, categories=date_labels, ordered=True),
                "Recommended rate (₹)": prices_only,
            }
        )
        st.vega_lite_chart(
            chart_df,
            {
                "mark": {
                    "type": "line",
                    "color": "#63836f",
                    "interpolate": "monotone",
                    "point": {"filled": True, "size": 35},
                },
                "encoding": {
                    "x": {
                        "field": "Date",
                        "type": "ordinal",
                        "sort": date_labels,
                        "axis": {
                            "title": None,
                            "labelAngle": -35,
                            "labelOverlap": True,
                            "labelLimit": 80,
                        },
                    },
                    "y": {
                        "field": "Recommended rate (₹)",
                        "type": "quantitative",
                        "scale": {"zero": False, "nice": True},
                        "axis": {"title": "Recommended rate (₹)", "format": ",.0f"},
                    },
                    "tooltip": [
                        {"field": "Date", "type": "ordinal"},
                        {
                            "field": "Recommended rate (₹)",
                            "type": "quantitative",
                            "format": ",.0f",
                        },
                    ],
                },
                "height": 280,
                "width": "container",
            },
            use_container_width=True,
        )

    st.write("")

    card_header("dot-lavender", "Daily recommendations")
    table_rows = []
    for day, price_result in priced:
        change = round((price_result.total_multiplier - 1) * 100)
        change_class = "increase" if change > 0 else "decrease" if change < 0 else "unchanged"
        table_rows.append(
            "<tr>"
            f'<td class="calendar-date">{escape(day.strftime("%a, %b %d"))}</td>'
            f'<td class="calendar-rate">₹{price_result.final_price:,.0f}</td>'
            f'<td class="calendar-change {change_class}">{change:+d}%</td>'
            f"<td>{synthetic_market_occupancy(city, day):.0f}%</td>"
            "</tr>"
        )

    st.markdown(
        '<div class="calendar-table-wrap"><table class="calendar-table">'
        "<thead><tr><th>Date</th><th>Nightly benchmark</th>"
        "<th>Change vs. base</th><th>Market occupancy</th></tr></thead>"
        f"<tbody>{''.join(table_rows)}</tbody></table></div>",
        unsafe_allow_html=True,
    )

    explanation_dates = [day for day, _ in priced]
    explanation_day = st.selectbox(
        "View pricing explanation",
        explanation_dates,
        format_func=lambda day: day.strftime("%a, %b %d"),
    )
    explanation_result = next(result for day, result in priced if day == explanation_day)
    st.caption(explanation_result.explain())

st.markdown(
    '<div class="footer-note">Rates shown are benchmarks based on synthetic demo data, not live pricing.</div>',
    unsafe_allow_html=True,
)