# SmartStay — Explainable Rental Pricing Demo

SmartStay is a small portfolio project exploring how short-term rental nightly
rates can be adjusted using demand signals. Select a market, bedroom count,
base rate, and stay date to see a benchmark recommendation and an explanation
of the factors behind it.

> **Demo only:** Recommendations use sample and synthetic data. Market
> occupancy, comparable rates, and booking pace are not live. This is an
> illustrative prototype, not pricing advice.

## Try the live app

**[Open SmartStay](YOUR_VERCEL_URL)**

Replace `YOUR_VERCEL_URL` with the deployment URL from Vercel after deploying.

## Features

- Single-night benchmark with an explanation and factor-by-factor breakdown.
- 30-night summary, rate trend, daily recommendations, occupancy, and
  selectable pricing explanations.
- Ten sample markets, one- to four-bedroom properties, editable base rate,
  and optional minimum/maximum guardrails.
- Light and dark themes with a responsive layout.

## Pricing approach

The demo multiplies the base nightly rate by seven hand-tuned factors:

| Factor | Demo behavior |
| --- | --- |
| Seasonality | Market-specific month-by-month demand profiles. |
| Day of week | Different multipliers for weekdays and weekends. |
| Lead time | Adjustments for last-minute, typical booking-window, and far-ahead dates. |
| Local events | Configured date-specific event adjustments. |
| Market occupancy | Adjustment using a synthetic occupancy estimate. |
| Comparable rate | Small adjustment against a synthetic comparable rate. |
| Booking pace | Adjustment when synthetic booking pace is especially fast or slow. |

Minimum and maximum guardrails optionally clamp the final recommendation.
These transparent rules are not a trained forecasting model.

## Deploy on Vercel

1. Push this repository to GitHub.
2. In [Vercel](https://vercel.com/), choose **Add New → Project** and import
   the GitHub repository.
3. Keep the detected **Next.js** framework preset and root directory.
4. Choose **Deploy**. The default build command is `npm run build`; no
   environment variables are required.
5. Copy the deployment URL into the **Try the live app** link above and the
   GitHub repository's **About → Website** field.

The deployed Next.js app runs the demo pricing calculations in the browser.
The Python engine remains in the repository as a standalone implementation
and reference; Vercel does not need to run a separate Python server.

## Run locally

Requirements: Node.js 20.9 or newer.

```bash
npm install
npm run dev
```

Open the local URL printed by Next.js, normally `http://localhost:3000`.

The Python reference engine can also be run as a Streamlit app with Python
dependencies installed:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Tests

The Python engine's regression tests use only the Python standard library:

```bash
python tests/test_pricing_engine.py
```

## Project structure

```text
smartstay/
├── app/                       # Next.js pages and global styles (Vercel app)
├── lib/pricing.ts             # Browser-side demo pricing calculations
├── smartstay/
│   ├── pricing_engine.py      # Python reference pricing engine
│   └── sample_data.py         # Python sample market data
├── tests/
│   └── test_pricing_engine.py
├── app.py                     # Original Streamlit demo
├── package.json
├── requirements.txt
└── README.md
```

There are no live data feeds, booking integrations, user accounts, or
persistent storage. Rates are illustrative benchmarks generated from sample
and synthetic inputs.

This is an independent project and is not affiliated with or
endorsed by any pricing platform.
