import { mkdir, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const outDir = resolve(root, "tracker");
const UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36";
const now = new Date();

async function request(url, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 20_000);
  try {
    const response = await fetch(url, { ...options, signal: controller.signal });
    if (!response.ok) throw new Error(`${response.status} ${url}`);
    return response;
  } finally {
    clearTimeout(timer);
  }
}

function number(value) {
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  if (typeof value !== "string" || value === "--") return null;
  const parsed = Number(value.replace(/[$,%+,]/g, ""));
  return Number.isFinite(parsed) ? parsed : null;
}

async function fredSeries(id) {
  const response = await request(`https://fred.stlouisfed.org/graph/fredgraph.csv?id=${encodeURIComponent(id)}`);
  const rows = (await response.text()).trim().split(/\r?\n/).slice(1);
  return rows.map((row) => {
    const [date, raw] = row.split(",");
    return { date, value: number(raw) };
  }).filter((row) => row.date && row.value !== null);
}

async function buildMacro() {
  const definitions = [
    ["DGS3MO", "3M Treasury", "3M"],
    ["DGS2", "2Y Treasury", "2Y"],
    ["DGS5", "5Y Treasury", "5Y"],
    ["DGS10", "10Y Treasury", "10Y"],
    ["DGS30", "30Y Treasury", "30Y"],
    ["DFF", "Effective fed funds", "EFFR"],
    ["VIXCLS", "VIX close", "VIX"],
  ];
  const results = await Promise.allSettled(definitions.map(async ([id, label, tenor]) => {
    const points = await fredSeries(id);
    const latest = points.at(-1);
    const previous = points.at(-2) ?? latest;
    if (!latest) throw new Error(`No FRED observations for ${id}`);
    return { id, label, tenor, value: latest.value, change: latest.value - previous.value, date: latest.date };
  }));
  const observations = results.filter((result) => result.status === "fulfilled").map((result) => result.value);
  if (!observations.length) throw new Error("No FRED macro data available");
  return { updatedAt: now.toISOString(), source: "FRED", observations };
}

function normalizeExpiry(label) {
  const candidate = new Date(`${label}, ${now.getUTCFullYear()} 12:00:00 UTC`);
  if (Number.isNaN(candidate.getTime())) return label;
  if (candidate.getTime() < now.getTime() - 21 * 86_400_000) candidate.setUTCFullYear(candidate.getUTCFullYear() + 1);
  return candidate.toISOString().slice(0, 10);
}

function optionSide(row, prefix) {
  return {
    strike: number(row.strike),
    lastPrice: number(row[`${prefix}_Last`]),
    bid: number(row[`${prefix}_Bid`]),
    ask: number(row[`${prefix}_Ask`]),
    volume: number(row[`${prefix}_Volume`]),
    openInterest: number(row[`${prefix}_Openinterest`]),
    inTheMoney: Boolean(row[`${prefix}_colour`]),
  };
}

function trimAroundSpot(rows, spot) {
  const valid = rows.filter((row) => row.strike !== null);
  if (!spot) return valid.slice(0, 28);
  return [...valid].sort((a, b) => Math.abs(a.strike - spot) - Math.abs(b.strike - spot)).slice(0, 28).sort((a, b) => a.strike - b.strike);
}

async function nasdaqOptions(symbol) {
  const assetclass = new Set(["SPY", "QQQ", "IWM"]).has(symbol) ? "etf" : "stocks";
  const url = `https://api.nasdaq.com/api/quote/${encodeURIComponent(symbol)}/option-chain?assetclass=${assetclass}&limit=2000`;
  const response = await request(url, { headers: { "User-Agent": UA, Accept: "application/json", Origin: "https://www.nasdaq.com" } });
  const data = (await response.json())?.data;
  if (!data?.table?.rows) throw new Error(`Nasdaq returned no option chain for ${symbol}`);
  const spotMatch = String(data.lastTrade ?? "").match(/\$([\d.,]+)/);
  const underlyingPrice = spotMatch ? number(spotMatch[1]) : null;
  const rows = data.table.rows.filter((row) => row.strike && row.expiryDate);
  const expiryLabels = [...new Set(rows.map((row) => row.expiryDate))].slice(0, 3);
  const expirations = expiryLabels.map((label) => {
    const expiryRows = rows.filter((row) => row.expiryDate === label);
    return {
      date: normalizeExpiry(label),
      calls: trimAroundSpot(expiryRows.map((row) => optionSide(row, "c")), underlyingPrice),
      puts: trimAroundSpot(expiryRows.map((row) => optionSide(row, "p")), underlyingPrice),
    };
  });
  if (!expirations.length) throw new Error(`Nasdaq returned no expirations for ${symbol}`);
  return { symbol, underlyingPrice, source: "Nasdaq", expirations };
}

let yahooSession;
async function yahooAuth() {
  if (yahooSession) return yahooSession;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 20_000);
  const cookieResponse = await fetch("https://fc.yahoo.com/", { headers: { "User-Agent": UA }, redirect: "manual", signal: controller.signal });
  clearTimeout(timer);
  const cookie = (cookieResponse.headers.get("set-cookie") ?? "").split(";")[0];
  if (!cookie) throw new Error("Yahoo session cookie unavailable");
  const crumbResponse = await request("https://query2.finance.yahoo.com/v1/test/getcrumb", { headers: { "User-Agent": UA, Cookie: cookie } });
  const crumb = (await crumbResponse.text()).trim();
  if (!crumb || crumb.includes("<")) throw new Error("Yahoo crumb unavailable");
  yahooSession = { cookie, crumb };
  return yahooSession;
}

async function yahooOptionRequest(symbol, date) {
  const auth = await yahooAuth();
  const params = new URLSearchParams({ crumb: auth.crumb });
  if (date) params.set("date", String(date));
  const response = await request(`https://query2.finance.yahoo.com/v7/finance/options/${encodeURIComponent(symbol)}?${params}`, { headers: { "User-Agent": UA, Accept: "application/json", Cookie: auth.cookie } });
  const result = (await response.json())?.optionChain?.result?.[0];
  if (!result) throw new Error(`Yahoo returned no option chain for ${symbol}`);
  return result;
}

function yahooSide(option) {
  return {
    strike: number(option.strike), lastPrice: number(option.lastPrice), bid: number(option.bid), ask: number(option.ask),
    volume: number(option.volume), openInterest: number(option.openInterest), impliedVolatility: number(option.impliedVolatility), inTheMoney: Boolean(option.inTheMoney),
  };
}

async function yahooOptions(symbol) {
  const first = await yahooOptionRequest(symbol);
  const dates = (first.expirationDates ?? []).slice(0, 3);
  const results = await Promise.all(dates.map((date, index) => index === 0 ? first : yahooOptionRequest(symbol, date)));
  const spot = number(first.quote?.regularMarketPrice);
  const expirations = results.map((result, index) => {
    const chain = result.options?.[0] ?? { calls: [], puts: [] };
    return {
      date: new Date((chain.expirationDate ?? dates[index]) * 1000).toISOString().slice(0, 10),
      calls: trimAroundSpot((chain.calls ?? []).map(yahooSide), spot),
      puts: trimAroundSpot((chain.puts ?? []).map(yahooSide), spot),
    };
  });
  return { symbol, underlyingPrice: spot, source: "Yahoo Finance", expirations };
}

async function buildOptions() {
  const symbols = ["SPY", "QQQ", "IWM"];
  const chains = [];
  for (const symbol of symbols) {
    try {
      chains.push(await nasdaqOptions(symbol));
    } catch (nasdaqError) {
      console.warn(`Nasdaq failed for ${symbol}; trying Yahoo Finance`, nasdaqError.message);
      chains.push(await yahooOptions(symbol));
    }
  }
  return { updatedAt: now.toISOString(), providerOrder: ["Nasdaq", "Yahoo Finance"], chains };
}

await mkdir(outDir, { recursive: true });
const [macro, options] = await Promise.all([buildMacro(), buildOptions()]);
await Promise.all([
  writeFile(resolve(outDir, "macro.json"), `${JSON.stringify(macro, null, 2)}\n`),
  writeFile(resolve(outDir, "options.json"), `${JSON.stringify(options, null, 2)}\n`),
]);
console.log(`Updated ${macro.observations.length} FRED observations and ${options.chains.length} option chains.`);
