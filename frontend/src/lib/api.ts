import type { Opportunity } from "@/components/ArbTable";

// Use environment variable for API base (frontend proxy or external backend)
// const API_BASE = process.env.INTERNAL_BACKEND_URL;

// Fetch up-to-date arbitrage opportunities from FastAPI backend
export async function fetchOpportunities(minProfit = 0.001): Promise<Opportunity[]> {
  const resp = await fetch(`/api/arbitrage?min_profit=${minProfit}`);
  if (!resp.ok) {
    throw new Error("Failed to fetch opportunities");
  }
  const data = await resp.json();
  return (data.arbitrage_opportunities ?? []).map((item: any, idx: number) => ({
    id: idx.toString(),
    market: item.direction === "kalshi_to_poly" ? "Kalshi → Poly" : "Poly → Kalshi",
    ticker: `${item.kalshi_ticker} / ${item.polymarket_slug}`,
    price: item.profit ? `$${item.profit.toFixed(4)}` : "-",
    profit: item.profit !== undefined && item.profit !== null ? `${(100 * item.profit).toFixed(2)}%` : "-",
    direction: item.direction,
    polymarketURL: `https://polymarket.com/markets/${item.polymarket_slug}`,
    kalshiURL: `https://kalshi.com/markets/kx${item.league}game/${item.league}-game/${item.kalshi_ticker.slice(-4)}`.toLowerCase(),
    original: item,
  })) as Opportunity[];
} 

// Trigger backend data refresh; returns true if refreshed
export async function refreshArbitrage(): Promise<boolean> {
  const resp = await fetch(`/api/refresh-arbitrage`);
  if (!resp.ok) {
    throw new Error("Failed to refresh arbitrage data");
  }
  const data = await resp.json();
  return !!data.refreshed;
}
