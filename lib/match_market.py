import requests
import re
from rapidfuzz import fuzz
import json

with open('lib/dictionaries/abbreviations.json', 'r') as f:
    kalshi_poly_dict = json.load(f)

# --- GLOBAL CONFIGURATION ---
POLY_WEB_BASE = "https://polymarket.com/event"
POLY_SEARCH_API = "https://gamma-api.polymarket.com/public-search"
POLY_SLUG_API = "https://gamma-api.polymarket.com/markets/slug"

# Automates League Translation
# Key: The text to look for in Kalshi Ticker
# Value: The prefix Polymarket uses in its Slugs
LEAGUE_CONFIG = {
    "nfl": "nfl",
    "nba": "nba",
    "nhl": "nhl",
    "mlb": "mlb"
}

class MarketMatcher:
    def __init__(self):
        self.months = {
            "jan":"01","feb":"02","mar":"03","apr":"04","may":"05","jun":"06",
            "jul":"07","aug":"08","sep":"09","oct":"10","nov":"11","dec":"12"
        }

    def _exact_match_sports_slug(self, ticker):
        """Automates slug creation by detecting league and parsing date/teams."""
        ticker = ticker.lower()
        
        # 1. Automate League Detection
        league_prefix = next((v for k, v in LEAGUE_CONFIG.items() if k in ticker), None)
        if not league_prefix:       
            return None

        # 2. Corrected Pattern: Year(2)Month(3)Day(2)Away(3)Home(3)
        # Ticker: 25dec23bknphi -> yr=25, mon=dec, day=23
        match = re.search(r'(\d{2})([a-z]{3})(\d{2})([a-z]{3})([a-z]{3})', ticker)
        
        if match:
            # Re-mapping the groups to the correct order
            yr, mon, day, away, home = match.groups()

            away = kalshi_poly_dict[league_prefix.upper()][away.upper()]['poly_abbr'].lower()
            home = kalshi_poly_dict[league_prefix.upper()][home.upper()]['poly_abbr'].lower()
            
            # Format to ISO: 2025-12-23
            iso_date = f"20{yr}-{self.months.get(mon, '01')}-{day}"
            
            # Generate slug: nba-bkn-phi-2025-12-23
            return f"{league_prefix}-{away}-{home}-{iso_date}"
            
        return None
        

    def find_polymarket_match(self, kalshi_market):
        """Main entry point: Orchestrates deterministic check vs. fuzzy search."""
        ticker = kalshi_market.get('ticker', '')
        title = kalshi_market.get('title', '')

        # STEP 1: Attempt Automated Slug Match (Fast/Accurate)
        generated_slug = self._exact_match_sports_slug(ticker)
        if generated_slug:
            print(f"DEBUG: Testing predicted slug -> {generated_slug}")
            resp = requests.get(f"{POLY_SLUG_API}/{generated_slug}")
            if resp.status_code == 200:
                data = resp.json()
                # Ensure we have the event slug for the URL
                data['final_url'] = f"{POLY_WEB_BASE}/{data.get('slug')}"
                return data

        return None
    
# --- RUNNING THE MATCHER ---
matcher = MarketMatcher()

# Example: NBA Test (Automatic Mapping)
nba_test = {
    "ticker": "KXNBAGAME-25DEC23BKNPHI",
    "title": "Will the Philadelphia 76ers win their game against the Brooklyn Nets on Dec 23, 2025?"
}

match = matcher.find_polymarket_match(nba_test)

if match:
    print(f"\n✅ SUCCESS: Found {match.get('question')}")
    print(f"🔗 Link: {match.get('final_url')}")
else:
    print("\n❌ FAILED: No match found.")

