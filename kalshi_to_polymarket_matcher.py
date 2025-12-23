from kalshi_fetcher import get_open_markets_for_series
from match_market import MarketMatcher

series_tickers = ["KXNBAGAME", "KXNFLGAME", "KXNHLGAME", "KXMLBGAME"]

matcher = MarketMatcher()
all_kalshi_markets = []

print("Fetching all open team-vs-team markets from NBA, NFL, NHL, MLB...")

for series_ticker in series_tickers:
    markets = get_open_markets_for_series(series_ticker)
    for market in markets:
        # Filter to only those that can produce a slug (team-vs-team format)
        if matcher._exact_match_sports_slug(market.get("ticker", "")):
            all_kalshi_markets.append(market)

print(f"Found {len(all_kalshi_markets)} team-vs-team markets. Attempting to match on Polymarket...\n")

results = []
for kalshi_market in all_kalshi_markets:
    poly_match = matcher.find_polymarket_match(kalshi_market)
    results.append({
        "kalshi_ticker": kalshi_market["ticker"],
        "kalshi_title": kalshi_market["title"],
        "polymarket_result": poly_match
    })
    if poly_match:
        print(f"✅ {kalshi_market['ticker']} | {kalshi_market['title']} ---> {poly_match['final_url']}")
    else:
        print(f"❌ {kalshi_market['ticker']} | {kalshi_market['title']} ---> No Polymarket match found")

# Optionally save results for further inspection
# import json
# with open("kalshi_polymarket_matches.json", "w") as f:
#     json.dump(results, f, indent=2)

