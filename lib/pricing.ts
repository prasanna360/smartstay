export const markets = [
  "Goa",
  "Manali, HP",
  "Udaipur, RJ",
  "Alibaug, MH",
  "Coorg, KA",
  "Lonavala, MH",
  "Jaipur, RJ",
  "Mahabaleshwar, MH",
  "Rishikesh, UK",
  "Munnar, KL",
] as const;

export type Market = (typeof markets)[number];

const basePrices: Record<Market, Record<number, number>> = {
  Goa: { 1: 3800, 2: 6000, 3: 8700, 4: 13000 },
  "Manali, HP": { 1: 2500, 2: 4000, 3: 5800, 4: 8700 },
  "Udaipur, RJ": { 1: 3200, 2: 5000, 3: 7300, 4: 10900 },
  "Alibaug, MH": { 1: 4200, 2: 6500, 3: 9400, 4: 14200 },
  "Coorg, KA": { 1: 2700, 2: 4200, 3: 6100, 4: 9200 },
  "Lonavala, MH": { 1: 5300, 2: 8500, 3: 12300, 4: 18400 },
  "Jaipur, RJ": { 1: 2800, 2: 4500, 3: 6500, 4: 9800 },
  "Mahabaleshwar, MH": { 1: 4100, 2: 6500, 3: 9400, 4: 14100 },
  "Rishikesh, UK": { 1: 2000, 2: 3200, 3: 4600, 4: 6900 },
  "Munnar, KL": { 1: 3000, 2: 4800, 3: 7000, 4: 10400 },
};

const seasonality: Record<Market, number[]> = {
  "Manali, HP": [1.25, 1.2, 1, 0.95, 1, 1.05, 0.8, 0.8, 0.95, 1.15, 1.2, 1.35],
  "Jaipur, RJ": [1.25, 1.2, 1.1, 0.95, 0.75, 0.7, 0.8, 0.85, 0.95, 1.1, 1.25, 1.3],
  Goa: [1.2, 1.15, 1.05, 1, 0.9, 0.85, 0.9, 0.9, 0.95, 1.05, 1.2, 1.35],
  "Udaipur, RJ": [1.2, 1.15, 1.05, 0.95, 0.75, 0.7, 0.8, 0.85, 0.95, 1.1, 1.25, 1.3],
  "Alibaug, MH": [1.1, 1.1, 1.05, 1.05, 1, 1.1, 1.15, 1.1, 1.05, 1.05, 1.1, 1.2],
  "Coorg, KA": [1.05, 1.05, 1, 0.95, 1, 1.1, 1.15, 1.15, 1.1, 1.05, 1.1, 1.2],
  "Lonavala, MH": [1.05, 1.05, 1, 1, 0.95, 1.1, 1.2, 1.2, 1.1, 1.05, 1.1, 1.2],
  "Mahabaleshwar, MH": [1.1, 1.05, 1, 0.95, 0.9, 1.1, 1.2, 1.2, 1.1, 1.05, 1.1, 1.2],
  "Rishikesh, UK": [1, 1.05, 1.15, 1.2, 1.1, 0.95, 0.75, 0.75, 0.9, 1.15, 1.2, 1],
  "Munnar, KL": [1.05, 1.05, 1, 0.95, 0.9, 1, 1.1, 1.1, 1.05, 1, 1.1, 1.2],
};

const generalSeasonality = [0.85, 0.85, 1.05, 1.05, 1.1, 1.25, 1.3, 1.2, 1, 1.05, 0.95, 1.15];
const weekdayMultipliers = [0.95, 0.95, 0.95, 1, 1.2, 1.25, 1.05];
const sharedEvents: Record<string, [string, number]> = {
  "2026-10-20": ["Diwali week", 1.45],
  "2026-10-21": ["Diwali", 1.6],
  "2026-12-24": ["Christmas Eve", 1.35],
  "2026-12-25": ["Christmas Day", 1.3],
  "2026-12-31": ["New Year's Eve", 1.6],
  "2027-01-01": ["New Year's Day", 1.35],
  "2027-03-04": ["Holi", 1.3],
};
const marketEvents: Partial<Record<Market, Record<string, [string, number]>>> = {
  "Manali, HP": {
    "2026-12-24": ["Manali winter snow season", 1.25],
    "2027-01-15": ["Manali winter snow season", 1.3],
  },
  "Jaipur, RJ": {
    "2026-10-21": ["Jaipur Diwali celebrations", 1.7],
    "2027-01-23": ["Jaipur Literature Festival", 1.25],
  },
  Goa: { "2026-12-31": ["Goa New Year's celebrations", 1.8] },
};

export interface PriceResult {
  basePrice: number;
  finalPrice: number;
  totalMultiplier: number;
  occupancy: number;
  competitorRate: number;
  bookingPace: number;
  factors: { name: string; multiplier: number }[];
  explanation: string;
}

export function getBasePrice(market: Market, bedrooms: number): number {
  return basePrices[market][bedrooms] ?? basePrices.Goa[2];
}

function stableHash(value: string): number {
  let hash = 2166136261;
  for (let i = 0; i < value.length; i += 1) {
    hash ^= value.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function occupancyFor(market: Market, date: Date): number {
  const day = dateKey(date);
  const seed = stableHash(`${market}-${day}`) % 1000;
  let occupancy = 35 + (seed / 1000) * 45;
  if ([5, 6].includes(date.getDay())) occupancy += 8;
  if ([5, 6, 7, 11].includes(date.getMonth())) occupancy += 6;
  return Math.round(Math.min(Math.max(occupancy, 5), 98) * 10) / 10;
}

function competitorFor(market: Market, bedrooms: number, date: Date): number {
  const day = dateKey(date);
  const seed = stableHash(`comp-${market}-${day}`) % 21;
  let factor = 0.9 + seed / 100;
  if ([5, 6].includes(date.getDay())) factor += 0.05;
  return Math.round(getBasePrice(market, bedrooms) * factor * 100) / 100;
}

function bookingPaceFor(market: Market, date: Date): number {
  const day = dateKey(date);
  const seed = stableHash(`pace-${market}-${day}`) % 61;
  let pace = 40 + seed;
  if ([5, 6].includes(date.getDay())) pace += 10;
  return Math.min(pace, 100);
}

const dateKey = (date: Date) =>
  `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;

export function calculatePrice(
  market: Market,
  bedrooms: number,
  basePrice: number,
  date: Date,
  today: Date,
  minPrice?: number,
  maxPrice?: number,
): PriceResult {
  const monthFactor = (seasonality[market] ?? generalSeasonality)[date.getMonth()];
  const dayFactor = weekdayMultipliers[date.getDay()];
  const daysOut = Math.round((date.getTime() - today.getTime()) / 86_400_000);
  const leadFactor = daysOut <= 2 ? 0.9 : daysOut <= 21 ? 1.08 : daysOut >= 180 ? 0.92 : 1;
  const event = marketEvents[market]?.[dateKey(date)] ?? sharedEvents[dateKey(date)];
  const eventFactor = event?.[1] ?? 1;
  const occupancy = occupancyFor(market, date);
  const occupancyFactor = occupancy >= 80 ? 1.15 : occupancy <= 35 ? 0.9 : 1;
  const competitorRate = competitorFor(market, bedrooms, date);
  const competitorFactor = basePrice > competitorRate * 1.1 ? 0.95 : basePrice < competitorRate * 0.9 ? 1.05 : 1;
  const bookingPace = bookingPaceFor(market, date);
  const paceFactor = bookingPace >= 80 ? 1.1 : bookingPace <= 30 ? 0.92 : 1;

  const rawPrice =
    basePrice *
    monthFactor *
    dayFactor *
    leadFactor *
    eventFactor *
    occupancyFactor *
    competitorFactor *
    paceFactor;
  const finalPrice =
    Math.round(Math.min(maxPrice ?? Infinity, Math.max(minPrice ?? 0, rawPrice)) * 100) / 100;
  const totalMultiplier = basePrice
    ? Math.round((finalPrice / basePrice) * 1000) / 1000
    : 0;
  const reasons: string[] = [];

  if (event) reasons.push(`${event[0]} falls on this date, driving significant local demand.`);
  if ([5, 6].includes(date.getDay())) reasons.push(`${date.toLocaleDateString("en-US", { weekday: "long" })} nights are in high demand.`);
  else if (dayFactor < 1) reasons.push(`${date.toLocaleDateString("en-US", { weekday: "long" })} is a midweek night, priced to encourage bookings.`);
  if (monthFactor >= 1.2) reasons.push(`It's peak season (${date.toLocaleDateString("en-US", { month: "long" })}), a high-demand month.`);
  else if (monthFactor <= 0.9) reasons.push(`It's low season (${date.toLocaleDateString("en-US", { month: "long" })}), so demand is typically softer.`);
  if (daysOut >= 0 && daysOut <= 2) reasons.push("This date is very last-minute and still open, so it's discounted to attract a booking.");
  else if (daysOut <= 21) reasons.push("This date is inside the typical booking window, where demand tends to be strongest.");
  else if (daysOut >= 180) reasons.push("This date is far in advance, priced to encourage early booking.");
  if (occupancy >= 80) reasons.push(`Comparable listings in the area are ${Math.round(occupancy)}% booked, signaling strong demand.`);
  else if (occupancy <= 35) reasons.push(`Comparable listings in the area are only ${Math.round(occupancy)}% booked, signaling soft demand.`);
  if (basePrice > competitorRate * 1.1) reasons.push(`Your base rate is about ${Math.round((basePrice / competitorRate - 1) * 100)}% above comparable listings, so it is softened.`);
  else if (basePrice < competitorRate * 0.9) reasons.push(`Your base rate is about ${Math.round((competitorRate / basePrice - 1) * 100)}% below comparable listings, so there is room to increase it.`);
  else reasons.push("Your base rate is close to the comparable-listing average.");
  if (bookingPace >= 80) reasons.push(`This date is booking quickly at ${Math.round(bookingPace)}% of its expected pace.`);
  else if (bookingPace <= 30) reasons.push(`This date is booking slowly at ${Math.round(bookingPace)}% of its expected pace.`);
  if (minPrice !== undefined && rawPrice < minPrice) reasons.push(`Capped at your minimum price of ₹${minPrice}.`);
  if (maxPrice !== undefined && rawPrice > maxPrice) reasons.push(`Capped at your maximum price of ₹${maxPrice}.`);
  if (!reasons.length) reasons.push("No major demand signals for this date — priced near your base rate.");

  const pctChange = Math.round((totalMultiplier - 1) * 100);
  const direction = pctChange >= 0 ? "above" : "below";
  return {
    basePrice,
    finalPrice,
    totalMultiplier,
    occupancy,
    competitorRate,
    bookingPace,
    factors: [
      { name: "Seasonality", multiplier: monthFactor },
      { name: "Day of week", multiplier: dayFactor },
      { name: "Lead time", multiplier: leadFactor },
      { name: "Local event", multiplier: eventFactor },
      { name: "Market occupancy", multiplier: occupancyFactor },
      { name: "Comparable rate", multiplier: competitorFactor },
      { name: "Booking pace", multiplier: paceFactor },
    ],
    explanation: `Priced ${Math.abs(pctChange)}% ${direction} base rate (₹${basePrice.toFixed(0)} → ₹${finalPrice.toFixed(0)}). ${reasons.join(" ")}`,
  };
}
