import requests
import re

# Base URLs
POLY_WEB_URL = "https://polymarket.com/event"
POLY_GAMMA_SEARCH = "https://gamma-api.polymarket.com/public-search"
POLY_SLUG_API = "https://gamma-api.polymarket.com/markets/slug"

def build_nfl_slug_from_kalshi(k_ticker):
    """
    Translates Kalshi NFL ticker to Polymarket Slug format.
    Example: kxnflgame-25dec25dalwas -> nfl-dal-was-2025-12-25
    """
    # Pattern to catch: Day(2) Month(3) Year(2) Away(3) Home(3)
    match = re.search(r'(\d{2})([a-z]{3})(\d{2})([a-z]{3})([a-z]{3})', k_ticker.lower())
    if not match:
        return None
        
    day, month_str, year_short, away, home = match.groups()
    months = {"jan":"01","feb":"02","mar":"03","apr":"04","may":"05","jun":"06",
              "jul":"07","aug":"08","sep":"09","oct":"10","nov":"11","dec":"12"}
    
    date_iso = f"20{year_short}-{months.get(month_str, '01')}-{day}"
    return f"nfl-{away}-{home}-{date_iso}"

def get_poly_match(k_market):
    k_title = k_market.get('title', "")
    k_ticker = k_market.get('ticker', "")

    # 1. Try exact NFL slug match (Deterministic)
    if "nfl" in k_ticker.lower():
        slug = build_nfl_slug_from_kalshi(k_ticker)
        resp = requests.get(f"{POLY_SLUG_API}/{slug}")
        if resp.status_code == 200:
            return resp.json()

    # 2. Keyword search fallback (Discovery)
    # Strip fluff words that confuse search engines
    fluff = r'\b(will|the|win|professional|football|game|against|on|at|by|\?)\b'
    clean_q = re.sub(fluff, '', k_title, flags=re.IGNORECASE).strip()
    clean_q = " ".join(clean_q.split())
    
    resp = requests.get(POLY_GAMMA_SEARCH, params={'q': clean_q})
    results = resp.json()

    if isinstance(results, list) and len(results) > 0:
        event = results[0]
        # Polymarket events can contain multiple markets (strikes). 
        # For a winner market, we return the first one.
        markets = event.get('markets', [])
        if markets:
            # We attach the event slug to the market object for link generation
            markets[0]['event_slug'] = event.get('slug')
            return markets[0]
    
    return None

def display_match_info(k_market, p_match):
    print("=" * 60)
    print(f"SOURCE (KALSHI): {k_market['title']}")
    
    if p_match:
        # Polymarket uses the event slug for the URL path
        slug = p_match.get('event_slug') or p_match.get('slug')
        link = f"{POLY_WEB_URL}/{slug}"
        
        print("\n✅ POLYMARKET MATCH FOUND")
        print(f"{'Question:':<12} {p_match.get('question')}")
        print(f"{'Slug:':<12} {p_match.get('slug')}")
        print(f"{'Link:':<12} {link}")
    else:
        print("\n❌ NO POLYMARKET MATCH FOUND")
    print("=" * 60)

# --- Test Case ---
test_kalshi_market = {
    "ticker": "kxnflgame-25dec25dalwas",
    "title": "Will the Dallas Cowboys win the professional football game against the Washington Commanders on December 25, 2025?"
}

match = get_poly_match(test_kalshi_market)
display_match_info(test_kalshi_market, match)