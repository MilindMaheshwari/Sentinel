import json
from lib.kalshi_fetcher import get_open_markets_for_series
from lib.match_market import MarketMatcher
import requests

with open('lib/dictionaries/abbreviations.json', 'r') as f:
    kalshi_poly_dict = json.load(f)

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
    """
    kalshi_market: The dict for a specific ticker (e.g., ...DETSAC-DET)
    outcomes: List of teams from Polymarket (e.g., ["Pistons", "Kings"])
    poly_prices: List of prices (e.g., [0.45, 0.55])
    """
    kalshi_ticker = kalshi_market.get("ticker", "")
    league = kalshi_ticker[2:5]
    # Extract the team code from the end of the Kalshi ticker (e.g., 'DET')
    kalshi_team_code = kalshi_ticker.split('-')[-1] 

    kalshi_yes = float(kalshi_market.get("yes_ask_dollars") or 0)
    kalshi_no = float(kalshi_market.get("no_ask_dollars") or 0)

    arbitrage_cases = []

    for i, outcome_name in enumerate(outcomes):
        # IMPORTANT: Use your matcher or a simple helper to see if 
        # 'DET' (Kalshi) matches 'Pistons' (Polymarket)
        if not is_same_team(kalshi_team_code, outcome_name, league):
            continue

        # If we are here, we are looking at the SAME team on both platforms
        poly_yes = poly_prices[i]
        poly_no = 1 - poly_yes

        # Case 1: Buy Team A 'YES' on Kalshi, 'NO' (against Team A) on Polymarket
        if kalshi_yes > 0:
            total_spent = kalshi_yes + poly_no
            if total_spent < 1: # Use 0.98 to account for slippage/fees
                arbitrage_cases.append({
                    "type": f"YES_Kalshi_{kalshi_team_code} + NO_Poly_{outcome_name}",
                    "outcome": outcome_name,
                    "cost": total_spent,
                    "profit": 1 - total_spent
                })


        # Case 2: Buy Team A 'YES' on Polymarket, 'NO' on Kalshi
        if kalshi_no > 0:
            total_spent = poly_yes + kalshi_no
            if total_spent < 1:
                arbitrage_cases.append({
                    "type": f"YES_Poly_{outcome_name} + NO_Kalshi_{kalshi_team_code}",
                    "outcome": outcome_name,
                    "cost": total_spent,
                    "profit": 1 - total_spent
                })
                
    return arbitrage_cases

def is_same_team(kalshi_team_code, outcome_name, league):
    return kalshi_poly_dict[league][kalshi_team_code]['name'] == outcome_name

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
                print(f"  Cost: {arb['cost']:.3f}, Guaranteed Profit: {arb['profit']:.3f}\n")
            print(f"==========================\n")
        else:
            print(f"No arbitrage for: {kalshi_ticker} ({kalshi_title})")

    with open("arbitrage_opportunities.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nResults saved to arbitrage_opportunities.json")

if __name__ == "__main__":
    main()

