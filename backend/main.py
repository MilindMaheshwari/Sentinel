from fastapi import FastAPI, Depends, Query
from sqlalchemy.orm import Session
from db import get_db
from models import KalshiMarket, PolymarketMarket, MarketMatchMap, Base
from typing import List
from sqlalchemy import or_
from datetime import datetime
import uvicorn
from decimal import Decimal
from fetch_and_sync_markets import fetch_and_sync_and_calculate_profit

app = FastAPI()

# Initially create all tables (in production, use migrations instead!)
from db import engine
Base.metadata.create_all(bind=engine)

@app.get("/api/refresh-arbitrage")
def refresh_arbitrage(db: Session = Depends(get_db)):
    THRESHOLD = -1
    mappings = db.query(MarketMatchMap).all()
    stale = (not mappings) or any((m.last_updated is None) or ((datetime.now() - m.last_updated).total_seconds() > THRESHOLD * 60) for m in mappings)
    if stale:
        fetch_and_sync_and_calculate_profit(db)
        # Re-load mappings to count, after update
        mappings = db.query(MarketMatchMap).all()
    return {
        "mappings": mappings,
        "refreshed": stale,
        "matched_pairs": len(mappings),
        "note": "Market data refreshed and symmetrical by team per market."
    }

@app.get("/api/markets/matches")
def get_market_matches(db: Session = Depends(get_db)):
    # Returns market matchings including profit and direction per market/team
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
            "profit": float(m.profit) if m.profit else None,
            "direction": m.direction,
            "match_score": float(m.match_score) if m.match_score else None,
            "league": m.league,
            "last_updated": m.last_updated
        })
    return result

@app.get("/api/arbitrage")
def get_arbitrage(min_profit: float = Query(0.001), db: Session = Depends(get_db)):
    # Returns all market matches with profit > min_profit
    mappings = db.query(MarketMatchMap).filter(MarketMatchMap.profit > Decimal(str(min_profit))).all()
    opportunities = []
    for m in mappings:
        k, p = m.kalshi_market, m.polymarket_market
        record = {
            "kalshi_ticker": k.ticker,
            "polymarket_slug": p.slug,
            "team": k.team,
            "profit": float(m.profit) if m.profit else None,
            "direction": m.direction,
            "kalshi": {
                "yes_ask_dollars": float(k.yes_ask_dollars),
                "no_ask_dollars": float(k.no_ask_dollars),
                "team": k.team
            },
            "polymarket": {
                "home_team": p.home_team,
                "away_team": p.away_team,
                "home_price": float(p.home_price),
                "away_price": float(p.away_price)
            },
            "league": m.league,
            "last_updated": m.last_updated
        }
        opportunities.append(record)
    return {"arbitrage_opportunities": opportunities}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
