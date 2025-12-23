import requests

BASE_URL = 'https://api.elections.kalshi.com/trade-api/v2'

def fetch_tags_for_categories():
    """Fetch category-to-tags mapping to help find 'Individual Sports Games'"""
    resp = requests.get(f"{BASE_URL}/search/tags_by_categories")
    resp.raise_for_status()
    return resp.json()["tags_by_categories"]

def get_series_list(category=None, tags=None):
    """Fetch series with optional category/tag filter."""
    params = {}
    if category:
        params["category"] = category
    if tags:
        params["tags"] = tags  # Should be a comma-separated string if multiple
    resp = requests.get(f"{BASE_URL}/series", params=params)
    resp.raise_for_status()
    return resp.json()["series"]

def get_open_markets_for_series(series_ticker):
    """Fetch all open markets for a specific series ticker."""
    params = {
        "series_ticker": series_ticker,
        "status": "open",  # Only get active/open markets
        "limit": 1000      # Fetch up to 1000 per page (max allowed)
    }
    resp = requests.get(f"{BASE_URL}/markets", params=params)
    resp.raise_for_status()
    return resp.json()["markets"]

def main():
    tag_map = fetch_tags_for_categories()

    # 1. Identify the tag or category (inspect tag_map output)
    print("Available Categories and Tags:")
    for cat, tags in tag_map.items():
        print(f"- {cat}: {tags}")

    # Change 'Individual Sports Games' to the EXACT tag or category you find in tag_map
    category = "Sports"
    tag = "Football,Soccer,Basketball,Baseball,Hockey,Cricket"  # Update this value after inspecting available tags

    # 2. Find all series for Individual Sports
    series_list = get_series_list(category=category, tags=tag)
    print(f"Found {len(series_list)} series for category={category}, tag={tag}")

    # 3. Query open (active) markets from each series
    all_markets = []
    for s in series_list:
        series_ticker = s['ticker']
        markets = get_open_markets_for_series(series_ticker)
        if markets:
            print(f"Series '{s['title']}' ({series_ticker}): {len(markets)} open markets")
        all_markets.extend(markets)

    print(f"Total active 'Individual Sports Games' markets: {len(all_markets)}")
    # Uncomment to display the market tickers:
    # for m in all_markets:
    #     print(f"{m['ticker']} - {m['title']}")
    # (Or save/process as needed...)

if __name__ == "__main__":
    main()