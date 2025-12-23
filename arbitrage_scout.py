import json
from kalshi_fetcher import get_open_markets_for_series
from match_market import MarketMatcher
import requests

SERIES_TICKERS = ["KXNBAGAME", "KXNFLGAME", "KXNHLGAME", "KXMLBGAME"]
KALSHI_SIDES = ["yes", "no"]

def fetch_polymarket_prices(slug):
    resp = requests.get(f"https://gamma-api.polymarket.com/markets/slug/{slug}")
    if resp.status_code != 200:
        return None, None
    data = resp.json()
    try:
        outcomes = json.loads(data["outcomes"]) if isinstance(data["outcomes"], str) else data["outcomes"]
        prices = json.loads(data["outcomePrices"]) if isinstance(data["outcomePrices"], str) else data["outcomePrices"]
        return outcomes, [float(p) for p in prices]
    except Exception:
        return None, None

def detect_arbitrage(kalshi_market, polymarket_slug, outcomes, poly_prices):
    # Kalshi fields
    kalshi_prices = {}
    for side in KALSHI_SIDES:
        price = kalshi_market.get(f"{side}_ask_dollars")
        try:
            kalshi_prices[side] = float(price) if price is not None else None
        except:
            kalshi_prices[side] = None

    arbitrage_cases = []
    # YES/NO mapping: outcome 0 is "away", outcome 1 is "home"
    for i, outcome in enumerate(outcomes):
        poly_yes = poly_prices[i] if i < len(poly_prices) else None
        poly_no = 1 - poly_yes if poly_yes is not None else None
        # Case 1: Buy YES on Kalshi, NO on Polymarket (i-th outcome)
        if kalshi_prices["yes"] is not None and poly_no is not None:
            total_spent = kalshi_prices["yes"] + poly_no
            if total_spent < 1:
                arbitrage_cases.append({
                    "type": "YES_Kalshi + NO_Polymarket",
                    "outcome": outcome,
                    "kalshi_yes": kalshi_prices["yes"],
                    "polymarket_no": poly_no,
                    "sum": total_spent,
                    "profit": 1 - total_spent,
                })
        # Case 2: Buy YES on Polymarket, NO on Kalshi
        if poly_yes is not None and kalshi_prices["no"] is not None:
            total_spent = poly_yes + kalshi_prices["no"]
            if total_spent < 1:
                arbitrage_cases.append({
                    "type": "YES_Polymarket + NO_Kalshi",
                    "outcome": outcome,
                    "polymarket_yes": poly_yes,
                    "kalshi_no": kalshi_prices["no"],
                    "sum": total_spent,
                    "profit": 1 - total_spent,
                })
    return arbitrage_cases

def main():
    matcher = MarketMatcher()
    all_kalshi_markets = []

    print("Fetching all open team-vs-team markets from NBA, NFL, NHL, MLB...")
    for series_ticker in SERIES_TICKERS:
        markets = get_open_markets_for_series(series_ticker)
        for market in markets:
            if matcher._exact_match_sports_slug(market.get("ticker", "")):
                all_kalshi_markets.append(market)

    print(f"Found {len(all_kalshi_markets)} team-vs-team markets.\n")
    results = []
    for kalshi_market in all_kalshi_markets:
        kalshi_ticker = kalshi_market.get("ticker", "?")
        kalshi_title = kalshi_market.get("title", "?")
        match = matcher.find_polymarket_match(kalshi_market)
        if not match:
            print(f"❌ No Polymarket match for {kalshi_ticker} - {kalshi_title}")
            continue
        polymarket_slug = match.get('slug') or (match.get('final_url', '').split('/')[-1])
        outcomes, price_list = fetch_polymarket_prices(polymarket_slug)
        if not outcomes or not price_list:
            print(f"❌ Could not fetch Polymarket prices for {polymarket_slug}")
            continue
        arb_opps = detect_arbitrage(kalshi_market, polymarket_slug, outcomes, price_list)
        item = {
            "kalshi_ticker": kalshi_ticker,
            "kalshi_title": kalshi_title,
            "polymarket_slug": polymarket_slug,
            "outcomes": outcomes,
            "polymarket_prices": price_list,
            "kalshi_yes": kalshi_market.get('yes_ask_dollars'),
            "kalshi_no": kalshi_market.get('no_ask_dollars'),
            "arbitrage_opportunities": arb_opps
        }
        results.append(item)

        # Print arbitrage opportunities
        if arb_opps:
            print(f"\n===== ARBITRAGE FOUND =====\nKalshi: {kalshi_ticker} | {kalshi_title}")
            print(f"Polymarket: {polymarket_slug}")
            for arb in arb_opps:
                print(f"Outcome: {arb['outcome']}")
                print(f"Type: {arb['type']}")
                print(f"  Kalshi YES: {item['kalshi_yes']}, Kalshi NO: {item['kalshi_no']}")
                print(f"  Polymarket YES: {price_list[outcomes.index(arb['outcome'])]}, NO: {1 - price_list[outcomes.index(arb['outcome'])]}")
                print(f"  Cost: {arb['sum']:.3f}, Guaranteed Profit: {arb['profit']:.3f}\n")
            print(f"==========================\n")
        else:
            print(f"No arbitrage for: {kalshi_ticker} ({kalshi_title})")

    with open("arbitrage_opportunities.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to arbitrage_opportunities.json")

if __name__ == "__main__":
    main()

