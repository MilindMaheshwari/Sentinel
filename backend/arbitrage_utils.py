from typing import List, Dict, Tuple, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from models import KalshiMarket, PolymarketMarket, MarketMatchMap
import json
with open('lib/dictionaries/abbreviations.json', 'r') as f:
    kalshi_poly_dict = json.load(f)

### Staleness Checker ###
def needs_update(last_updated: Optional[datetime], threshold_minutes: int = 30) -> bool:
    if not last_updated:
        return True
    return datetime.utcnow() - last_updated > timedelta(minutes=threshold_minutes)

### Arbitrage Detection (per team/side, symmetrical DB models) ###
def detect_arbitrage(
    kalshi_market: KalshiMarket,
    polymarket_market: PolymarketMarket,
    min_profit: Decimal = 0
) -> List[Dict]:
    """
    For each Kalshi <-> Polymarket team pairing:
      - Yes/No Kalshi price for given team
      - Yes Polymarket price for given team: home/away
      - No on Kalshi corresponds to Yes on opposite team
    """
    opportunities = []
    # Determine team alignment (home/away)
    if  is_same_team(kalshi_market.team, polymarket_market.home_team, kalshi_market.league):
        pm_yes_price = polymarket_market.home_price
        pm_no_price = polymarket_market.away_price
    else:
        pm_yes_price = polymarket_market.away_price
        pm_no_price = polymarket_market.home_price
    # else:
    #     # Not a matching team for this market
    #     return []


    # Arbitrage: Buy YES Kalshi + NO Poly (use price from Polymarket YES on other team)
    if kalshi_market.yes_ask_dollars is not None and pm_no_price is not None:
        cost = kalshi_market.yes_ask_dollars + pm_no_price
        profit = Decimal('1') - cost
        if profit > min_profit:
            opportunities.append({
                'type': f'YES_Kalshi_{kalshi_market.team} + NO_Poly_{kalshi_market.team}',
                'team': kalshi_market.team,
                'cost': float(cost),
                'profit': float(profit)
            })
    # Arbitrage: Buy YES Poly + NO Kalshi
    if pm_yes_price is not None and kalshi_market.no_ask_dollars is not None:
        cost = pm_yes_price + kalshi_market.no_ask_dollars
        profit = Decimal('1') - cost
        if profit > min_profit:
            opportunities.append({
                'type': f'YES_Poly_{kalshi_market.team} + NO_Kalshi_{kalshi_market.team}',
                'team': kalshi_market.team,
                'cost': float(cost),
                'profit': float(profit)
            })
    return opportunities

def is_same_team(kalshi_team_code, outcome_name, league):
    return kalshi_poly_dict[league][kalshi_team_code]['name'] == outcome_name
