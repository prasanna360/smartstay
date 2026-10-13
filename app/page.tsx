"use client";

import { useEffect, useMemo, useState } from "react";
import {
  calculatePrice,
  getBasePrice,
  markets,
  type Market,
  type PriceResult,
} from "@/lib/pricing";

type Theme = "light" | "dark";
type Mode = "single" | "calendar";

const currency = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

function dateFromInput(value: string): Date {
  return new Date(`${value}T12:00:00`);
}

function dateInputValue(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function formatDate(date: Date, options: Intl.DateTimeFormatOptions = {}) {
  return date.toLocaleDateString("en-IN", {
    weekday: "short",
    month: "short",
    day: "numeric",
    ...options,
  });
}

function SummaryCard({
  label,
  value,
  note,
  featured = false,
}: {
  label: string;
  value: string;
  note: string;
  featured?: boolean;
}) {
  return (
    <article className={`summary-card${featured ? " featured" : ""}`}>
      <p className="summary-label">{label}</p>
      <p className="summary-value">{value}</p>
      <p className="summary-note">{note}</p>
    </article>
  );
}

function RateChart({ rows }: { rows: { date: Date; price: number }[] }) {
  const width = 900;
  const height = 250;
  const padding = { top: 20, right: 18, bottom: 44, left: 66 };
  const values = rows.map((row) => row.price);
  const low = Math.floor(Math.min(...values) / 1000) * 1000;
  const high = Math.ceil(Math.max(...values) / 1000) * 1000 || 1000;
  const range = Math.max(high - low, 1000);
  const x = (index: number) =>
    padding.left +
    (index / Math.max(rows.length - 1, 1)) * (width - padding.left - padding.right);
  const y = (value: number) =>
    padding.top +
    ((high - value) / range) * (height - padding.top - padding.bottom);
  const points = rows.map((row, index) => `${x(index)},${y(row.price)}`).join(" ");
  const tickCount = 4;

  return (
    <div className="chart-scroll">
      <svg
        className="rate-chart"
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label="Recommended nightly benchmarks over the next 30 nights"
      >
        {Array.from({ length: tickCount + 1 }, (_, index) => {
          const value = low + (range * index) / tickCount;
          const tickY = y(value);
          return (
            <g key={index}>
              <line
                x1={padding.left}
                x2={width - padding.right}
                y1={tickY}
                y2={tickY}
                className="chart-grid"
              />
              <text x={padding.left - 10} y={tickY + 4} textAnchor="end" className="chart-label">
                {Math.round(value / 1000)}k
              </text>
            </g>
          );
        })}
        <polyline points={points} className="chart-line" />
        {rows.map((row, index) => (
          <circle
            key={row.date.toISOString()}
            cx={x(index)}
            cy={y(row.price)}
            r="3.5"
            className="chart-point"
          >
            <title>{`${formatDate(row.date)}: ${currency.format(row.price)}`}</title>
          </circle>
        ))}
        {[0, 7, 14, 21, 29].map((index) => (
          <text
            key={index}
            x={x(index)}
            y={height - 12}
            textAnchor={index === 0 ? "start" : index === 29 ? "end" : "middle"}
            className="chart-label"
          >
            {formatDate(rows[index].date, { weekday: undefined, year: undefined })}
          </text>
        ))}
      </svg>
    </div>
  );
}

export default function Home() {
  const [theme, setTheme] = useState<Theme>("light");
  const [mode, setMode] = useState<Mode>("single");
  const [market, setMarket] = useState<Market>("Goa");
  const [bedrooms, setBedrooms] = useState(2);
  const [basePrice, setBasePrice] = useState(6000);
  const [todayValue, setTodayValue] = useState("");
  const [targetValue, setTargetValue] = useState("");
  const [guardrails, setGuardrails] = useState(false);
  const [minimum, setMinimum] = useState(4200);
  const [maximum, setMaximum] = useState(12000);
  const [explanationDate, setExplanationDate] = useState("");

  useEffect(() => {
    const now = new Date();
    const todayString = dateInputValue(now);
    const savedTheme = window.localStorage.getItem("smartstay-theme");
    setTheme(savedTheme === "dark" ? "dark" : "light");
    setTodayValue(todayString);
    const initialDate = new Date(now);
    initialDate.setDate(initialDate.getDate() + 14);
    setTargetValue(dateInputValue(initialDate));
    setMinimum(Math.round(getBasePrice("Goa", 2) * 0.7));
    setMaximum(Math.round(getBasePrice("Goa", 2) * 2));
  }, []);

  useEffect(() => {
    window.localStorage.setItem("smartstay-theme", theme);
  }, [theme]);

  const today = todayValue ? dateFromInput(todayValue) : new Date();
  const targetDate = targetValue ? dateFromInput(targetValue) : new Date();
  const next30 = useMemo(() => {
    if (!todayValue) return [];
    const firstNight = dateFromInput(todayValue);
    firstNight.setDate(firstNight.getDate() + 1);
    return Array.from({ length: 30 }, (_, index) => {
      const date = new Date(firstNight);
      date.setDate(firstNight.getDate() + index);
      return {
        date,
        result: calculatePrice(
          market,
          bedrooms,
          basePrice,
          date,
          today,
          guardrails ? minimum : undefined,
          guardrails ? maximum : undefined,
        ),
      };
    });
  }, [todayValue, market, bedrooms, basePrice, today, guardrails, minimum, maximum]);

  const singleResult = useMemo(
    () =>
      calculatePrice(
        market,
        bedrooms,
        basePrice,
        targetDate,
        today,
        guardrails ? minimum : undefined,
        guardrails ? maximum : undefined,
      ),
    [market, bedrooms, basePrice, targetValue, todayValue, guardrails, minimum, maximum],
  );

  const average = next30.length
    ? next30.reduce((total, row) => total + row.result.finalPrice, 0) / next30.length
    : 0;
  const lowest = next30.length
    ? next30.reduce((best, row) => (row.result.finalPrice < best.result.finalPrice ? row : best))
    : null;
  const highest = next30.length
    ? next30.reduce((best, row) => (row.result.finalPrice > best.result.finalPrice ? row : best))
    : null;
  const selectedExplanation =
    next30.find((row) => dateInputValue(row.date) === explanationDate) ?? next30[0];

  if (!todayValue || !targetValue) {
    return (
      <main className="loading-screen" aria-live="polite">
        <span className="eyebrow">SmartStay</span>
        <p>Preparing your pricing workspace…</p>
      </main>
    );
  }

  function chooseMarket(value: string) {
    const nextMarket = value as Market;
    setMarket(nextMarket);
    const suggested = getBasePrice(nextMarket, bedrooms);
    setBasePrice(suggested);
    setMinimum(Math.round(suggested * 0.7));
    setMaximum(Math.round(suggested * 2));
  }

  function chooseBedrooms(value: number) {
    setBedrooms(value);
    const suggested = getBasePrice(market, value);
    setBasePrice(suggested);
    setMinimum(Math.round(suggested * 0.7));
    setMaximum(Math.round(suggested * 2));
  }

  function toggleTheme() {
    setTheme((current) => (current === "light" ? "dark" : "light"));
  }

  return (
    <div className="app-shell" data-theme={theme}>
      <aside className="sidebar">
        <a className="wordmark" href="#top" aria-label="SmartStay home">
          SmartStay
        </a>
        <div className="sidebar-heading">
          <p className="eyebrow">Pricing workspace</p>
          <h2>Property details</h2>
          <p className="sidebar-help">
            Choose a market and property, then review one night or the next 30.
          </p>
        </div>

        <div className="form-stack">
          <label className="field">
            <span>Market</span>
            <select value={market} onChange={(event) => chooseMarket(event.target.value)}>
              {markets.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Bedrooms</span>
            <select
              value={bedrooms}
              onChange={(event) => chooseBedrooms(Number(event.target.value))}
            >
              {[1, 2, 3, 4].map((count) => (
                <option key={count} value={count}>
                  {count} {count === 1 ? "bedroom" : "bedrooms"}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Base nightly rate</span>
            <div className="number-wrap">
              <span aria-hidden="true">₹</span>
              <input
                type="number"
                min={20}
                step={100}
                value={basePrice}
                onChange={(event) => setBasePrice(Math.max(20, Number(event.target.value)))}
              />
            </div>
          </label>

          <div className="guardrail-toggle">
            <label htmlFor="guardrails">Set price guardrails</label>
            <input
              id="guardrails"
              type="checkbox"
              checked={guardrails}
              onChange={(event) => setGuardrails(event.target.checked)}
            />
          </div>

          {guardrails && (
            <div className="guardrail-fields">
              <label className="field">
                <span>Minimum (₹)</span>
                <input
                  type="number"
                  min={0}
                  value={minimum}
                  onChange={(event) => setMinimum(Number(event.target.value))}
                />
              </label>
              <label className="field">
                <span>Maximum (₹)</span>
                <input
                  type="number"
                  min={minimum}
                  value={maximum}
                  onChange={(event) => setMaximum(Number(event.target.value))}
                />
              </label>
            </div>
          )}
        </div>

        <div className="data-note">
          <strong>Demo benchmarks</strong>
          <span>Market, occupancy, competitor, and booking pace values are synthetic—not live rates.</span>
        </div>
      </aside>

      <main className="main-content" id="top">
        <header className="topbar">
          <div>
            <p className="eyebrow">Explainable short-stay pricing</p>
            <h1>SmartStay</h1>
          </div>
          <button className="theme-button" type="button" onClick={toggleTheme}>
            {theme === "light" ? "Use dark theme" : "Use light theme"}
          </button>
        </header>

        <section className="intro">
          <p>
            Explore a nightly benchmark and the demand signals behind it. Choose a date for
            a detailed breakdown, or scan the next 30 nights.
          </p>
          <span className="demo-pill">Illustrative demo · No live pricing data</span>
        </section>

        <nav className="tabs" aria-label="Pricing views">
          <button
            type="button"
            className={mode === "single" ? "active" : ""}
            onClick={() => setMode("single")}
          >
            Single date
          </button>
          <button
            type="button"
            className={mode === "calendar" ? "active" : ""}
            onClick={() => setMode("calendar")}
          >
            Next 30 nights
          </button>
        </nav>

        {mode === "single" ? (
          <section className="view-content">
            <div className="date-picker-card">
              <label className="field date-field">
                <span>Choose a stay date</span>
                <input
                  type="date"
                  min={todayValue}
                  max={todayValue ? dateInputValue(new Date(today.getFullYear() + 1, today.getMonth(), today.getDate())) : undefined}
                  value={targetValue}
                  onChange={(event) => setTargetValue(event.target.value)}
                />
              </label>
              <span className="context-label">
                {market} · {bedrooms} {bedrooms === 1 ? "bedroom" : "bedrooms"}
              </span>
            </div>

            <div className="summary-grid single-summary">
              <SummaryCard
                label="Recommended nightly benchmark"
                value={currency.format(singleResult.finalPrice)}
                note={`${Math.round((singleResult.totalMultiplier - 1) * 100) > 0 ? "+" : ""}${Math.round((singleResult.totalMultiplier - 1) * 100)}% vs. base rate`}
                featured
              />
              <SummaryCard
                label="Base rate"
                value={currency.format(basePrice)}
                note="Your starting nightly rate"
              />
              <SummaryCard
                label="Comparable benchmark"
                value={currency.format(singleResult.competitorRate)}
                note="Synthetic sample estimate"
              />
              <SummaryCard
                label="Market occupancy"
                value={`${Math.round(singleResult.occupancy)}%`}
                note="Synthetic market estimate"
              />
            </div>

            <section className="explanation-card">
              <p className="eyebrow">Why this benchmark?</p>
              <p>{singleResult.explanation}</p>
            </section>

            <section className="panel">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">Calculation details</p>
                  <h2>Pricing factors</h2>
                </div>
                <span className="small-note">Multiplier applied to base rate</span>
              </div>
              <div className="factor-grid">
                {singleResult.factors.map((factor) => (
                  <div className="factor-row" key={factor.name}>
                    <span>{factor.name}</span>
                    <strong>{factor.multiplier.toFixed(2)}×</strong>
                  </div>
                ))}
              </div>
            </section>
          </section>
        ) : (
          <section className="view-content">
            <div className="calendar-heading">
              <div>
                <p className="eyebrow">{market} · {bedrooms} bedroom{bedrooms > 1 ? "s" : ""}</p>
                <h2>Next 30 nights</h2>
                <p>Daily benchmark range with the synthetic demand signals behind each date.</p>
              </div>
            </div>

            <div className="summary-grid three-up">
              <SummaryCard label="Average nightly rate" value={currency.format(average)} note="Across the next 30 nights" featured />
              {lowest && (
                <SummaryCard
                  label="Lowest night"
                  value={currency.format(lowest.result.finalPrice)}
                  note={formatDate(lowest.date)}
                />
              )}
              {highest && (
                <SummaryCard
                  label="Highest night"
                  value={currency.format(highest.result.finalPrice)}
                  note={formatDate(highest.date)}
                />
              )}
            </div>

            <section className="panel">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">Daily movement</p>
                  <h2>Nightly rate trend</h2>
                </div>
                <span className="small-note">₹ INR · Synthetic benchmarks</span>
              </div>
              {next30.length > 0 && (
                <RateChart rows={next30.map((row) => ({ date: row.date, price: row.result.finalPrice }))} />
              )}
            </section>

            <section className="panel recommendations-panel">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">Daily recommendations</p>
                  <h2>Night-by-night benchmarks</h2>
                </div>
                <label className="explanation-select">
                  <span>Explain a date</span>
                  <select
                    value={explanationDate || (next30[0] ? dateInputValue(next30[0].date) : "")}
                    onChange={(event) => setExplanationDate(event.target.value)}
                  >
                    {next30.map((row) => (
                      <option key={dateInputValue(row.date)} value={dateInputValue(row.date)}>
                        {formatDate(row.date)}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              <div className="table-scroll">
                <table className="recommendations-table">
                  <thead>
                    <tr>
                      <th scope="col">Date</th>
                      <th scope="col">Nightly benchmark</th>
                      <th scope="col">vs. base</th>
                      <th scope="col">Occupancy</th>
                    </tr>
                  </thead>
                  <tbody>
                    {next30.map(({ date, result }) => {
                      const change = Math.round((result.totalMultiplier - 1) * 100);
                      return (
                        <tr key={dateInputValue(date)}>
                          <td>{formatDate(date)}</td>
                          <td className="table-price">{currency.format(result.finalPrice)}</td>
                          <td className={change > 0 ? "positive" : change < 0 ? "negative" : ""}>
                            {change > 0 ? "+" : ""}{change}%
                          </td>
                          <td>{Math.round(result.occupancy)}%</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              {selectedExplanation && (
                <p className="selected-explanation">
                  <strong>{formatDate(selectedExplanation.date)}:</strong>{" "}
                  {selectedExplanation.result.explanation}
                </p>
              )}
            </section>
          </section>
        )}

        <footer className="footer">
          Rates shown are benchmarks based on synthetic demo data, not live pricing.
        </footer>
      </main>
    </div>
  );
}
