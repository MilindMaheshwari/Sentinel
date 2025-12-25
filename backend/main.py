from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from db import get_db
from models import KalshiMarket, PolymarketMarket, MarketMatchMap, Base
from arbitrage_utils import needs_update, detect_arbitrage
from typing import List
from sqlalchemy import or_
from datetime import datetime
import uvicorn
from decimal import Decimal

app = FastAPI()

# Initially create all tables (in production, use migrations instead!)
from db import engine
Base.metadata.create_all(bind=engine)

@app.get("/api/refresh-arbitrage")
def refresh_arbitrage(db: Session = Depends(get_db)):
    # Check if any mapping is older than 30 min, if so, trigger update
    THRESHOLD = 30
    mappings = db.query(MarketMatchMap).all()
    stale = (not mappings) or any(needs_update(m.last_updated, THRESHOLD) for m in mappings)
    if stale:
        from fetch_and_sync_markets import fetch_and_sync_markets
        fetch_and_sync_markets(db)
        # Re-load mappings to count, after update
        mappings = db.query(MarketMatchMap).all()
    return {
        "refreshed": stale,
        "matched_pairs": len(mappings),
        "note": "Market data refreshed and symmetrical by team per market."
    }

@app.get("/api/markets/matches")
def get_market_matches(db: Session = Depends(get_db)):
    # Now returns market matchings for BOTH teams per game
    mappings = db.query(MarketMatchMap).all()
    result = []
    for m in mappings:
        k = m.kalshi_market
        p = m.polymarket_market
        result.append({
            "kalshi": {
                "ticker": k.ticker,
                "title": k.title,
                "team": k.team,
                "yes_ask_dollars": float(k.yes_ask_dollars),
                "no_ask_dollars": float(k.no_ask_dollars),
                "last_updated": k.last_updated,
            },
            "polymarket": {
                "slug": p.slug,
                "title": p.title,
                "home_team": p.home_team,
                "away_team": p.away_team,
                "home_price": float(p.home_price),
                "away_price": float(p.away_price),
                "last_updated": p.last_updated,
            },
            "match_score": float(m.match_score) if m.match_score else None,
            "league": m.league,
            "last_updated": m.last_updated
        })
    return result

@app.get("/api/arbitrage")
def get_arbitrage(min_profit: float = Query(0.02), db: Session = Depends(get_db)):
    # Returns all possible arbitrage opps per team-market
    mappings = db.query(MarketMatchMap).all()
    opportunities = []
    for m in mappings:
        if not m.kalshi_market or not m.polymarket_market:
            continue
        arbs = detect_arbitrage(
            m.kalshi_market,
            m.polymarket_market,
            Decimal(str(min_profit))
        )
        for arb in arbs:
            record = {
                "kalshi_ticker": m.kalshi_market.ticker,
                "polymarket_slug": m.polymarket_market.slug,
                "type": arb['type'],
                "team": arb['team'],
                "cost": arb['cost'],
                "profit": arb['profit'],
                "kalshi": {
                    "yes_ask_dollars": float(m.kalshi_market.yes_ask_dollars),
                    "no_ask_dollars": float(m.kalshi_market.no_ask_dollars),
                    "team": m.kalshi_market.team
                },
                "polymarket": {
                    "home_team": m.polymarket_market.home_team,
                    "away_team": m.polymarket_market.away_team,
                    "home_price": float(m.polymarket_market.home_price),
                    "away_price": float(m.polymarket_market.away_price)
                },
                "league": m.league
            }
            opportunities.append(record)
    return {"arbitrage_opportunities": opportunities}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
