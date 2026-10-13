# SmartStay — Explainable Rental Pricing Demo

SmartStay is a small portfolio project that demonstrates how a nightly rate
for a short-term rental can be adjusted using demand signals. Choose a market,
bedroom count, base rate, and stay date to see a recommended benchmark with a
plain-language explanation.

> **Demo only:** This app does not use live pricing, occupancy, competitor, or
> booking data. Its recommendations are illustrative benchmarks generated
> from sample and synthetic data; they are not pricing advice.

## What you can try

- **Single Date:** Review a recommended nightly benchmark, compare it with
  the sample base and comparable rates, and see the pricing factors behind it.
- **30-Day Calendar:** Compare average, lowest, and highest nightly
  benchmarks; explore the rate trend, daily rates, occupancy, and the
  explanation for each date.
- **Property controls:** Choose from 10 sample markets, select 1–4 bedrooms,
  set a base nightly rate, and optionally apply minimum and maximum price
  guardrails.
- **Light and dark themes:** The interface follows the selected Streamlit
  theme.

## How the price is calculated

The engine multiplies the base nightly rate by seven factors:

| Factor | Demo behavior |
| --- | --- |
| Seasonality | Uses a month-by-month profile, with profiles for each sample market. |
| Day of week | Applies different multipliers to weekdays and weekends. |
| Lead time | Adjusts for last-minute, typical booking-window, and far-ahead dates. |
| Local events | Applies configured date-specific event multipliers. |
| Market occupancy | Adjusts for a synthetic occupancy estimate. |
| Comparable rate | Makes a small adjustment based on the sample comparable-listing rate. |
| Booking pace | Adjusts when synthetic booking pace is especially fast or slow. |

Optional minimum and maximum guardrails clamp the final recommendation.
The app also displays the contributing multipliers and a human-readable
explanation. These are simple, hand-tuned rules—not a trained forecasting
model.

## Run locally

Python 3.10 or newer is recommended.

### Windows (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Streamlit prints a local URL, usually `http://localhost:8501`, where the app
can be opened in a browser.

## Run the tests

The pricing tests use only the Python standard library:

```bash
python tests/test_pricing_engine.py
```

## Project structure

```text
smartstay/
├── app.py
├── smartstay/
│   ├── pricing_engine.py
│   └── sample_data.py
├── tests/
│   └── test_pricing_engine.py
├── requirements.txt
└── README.md
```

The pricing logic is kept separate from the Streamlit UI. The test suite
covers pricing behavior such as weekend and event adjustments, guardrails,
market seasonality, and the 30-night range.

## Data and limitations

Base rates are example reference values stored in `smartstay/sample_data.py`.
Occupancy, comparable rates, and booking pace are deterministic synthetic
values generated for the selected market and date. Events and pricing
multipliers are configured in code. There is no external data feed, booking
integration, user account, or persistent storage.

The values are intended to make the pricing flow easy to explore—not to
represent current market conditions. A production pricing tool would need
reliable, regularly updated market data and validation against actual
booking outcomes.

## Possible next steps

- Connect a legitimate market-data source and label its coverage and update
  time.
- Validate and tune the pricing factors against historical booking results.
- Add multi-night stay and minimum-stay recommendations.
- Add deployment instructions and a hosted demo link once available.

---

This is an independent project and is not affiliated with or
endorsed by any pricing platform.
