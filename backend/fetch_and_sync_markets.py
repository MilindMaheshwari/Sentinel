from lib.kalshi_fetcher import get_open_markets_for_series
from lib.match_market import MarketMatcher
from models import KalshiMarket, PolymarketMarket, MarketMatchMap
from arbitrage_utils import detect_arbitrage
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from decimal import Decimal
import datetime

def fetch_and_sync_markets(db: Session):
    matcher = MarketMatcher()
    SERIES_TICKERS = ["KXNBAGAME", "KXNFLGAME", "KXNHLGAME", "KXMLBGAME"]
    now = datetime.datetime.utcnow()

    all_kalshi = []
    for ticker in SERIES_TICKERS:
        all_kalshi.extend(get_open_markets_for_series(ticker))

    for k_market in all_kalshi:
        kalshi_ticker = k_market.get("ticker", "")
        kalshi_title = k_market.get("title", "")
        match = matcher.find_polymarket_match(k_market)
        if not match or not match.get('slug'):
            continue

        import requests, json
        resp = requests.get(f"https://gamma-api.polymarket.com/markets/slug/{match['slug']}")
        if resp.status_code != 200:
            continue
        data = resp.json()
        outcomes = json.loads(data["outcomes"]) if isinstance(data["outcomes"], str) else data["outcomes"]
        prices = json.loads(data["outcomePrices"]) if isinstance(data["outcomePrices"], str) else data["outcomePrices"]
        if len(outcomes) != 2:
            continue
        home_team, away_team = outcomes[0], outcomes[1]
        home_price, away_price = Decimal(str(prices[0])), Decimal(str(prices[1]))
        poly_market_stmt = insert(PolymarketMarket).values(
            slug=match['slug'], title=match.get('question', ''),
            home_team=home_team, away_team=away_team,
            home_price=home_price, away_price=away_price,
            last_updated=now
        ).on_conflict_do_update(
            index_elements=[PolymarketMarket.slug],
            set_={
                'title': match.get('question', ''),
                'home_team': home_team,
                'away_team': away_team,
                'home_price': home_price,
                'away_price': away_price,
                'last_updated': now
            }
        )
        db.execute(poly_market_stmt)
        db.commit()
        poly_market = db.query(PolymarketMarket).filter_by(slug=match['slug']).one()

        for i, team in enumerate([home_team, away_team]):
            yes_ask = k_market.get('yes_ask_dollars')
            no_ask = k_market.get('no_ask_dollars')
            ask_yes = Decimal(str(yes_ask)) if yes_ask is not None else None
            ask_no = Decimal(str(no_ask)) if no_ask is not None else None
            kalshi_market_stmt = insert(KalshiMarket).values(
                ticker=kalshi_ticker + f"_{team}", title=kalshi_title, team=team,
                yes_ask_dollars=ask_yes, no_ask_dollars=ask_no, last_updated=now
            ).on_conflict_do_update(
                index_elements=[KalshiMarket.ticker],
                set_={'title': kalshi_title, 'team': team,
                      'yes_ask_dollars': ask_yes,
                      'no_ask_dollars': ask_no,
                      'last_updated': now}
            )
            db.execute(kalshi_market_stmt)
            db.commit()
            kalshi_market = db.query(KalshiMarket).filter_by(ticker=kalshi_ticker + f"_{team}").one()
            # Compute arbitrage and store best profit/direction
            arbs = detect_arbitrage(kalshi_market, poly_market, Decimal('0.0'))
            if arbs:
                best_arb = max(arbs, key=lambda x: x['profit'])
                profit = Decimal(str(best_arb['profit']))
                direction = best_arb['type']
            else:
                profit = Decimal('0')
                direction = None
            map_stmt = insert(MarketMatchMap).values(
                kalshi_market_id=kalshi_market.id,
                polymarket_market_id=poly_market.id,
                league=kalshi_ticker[2:5],
                profit=profit,
                direction=direction,
                last_updated=now
            ).on_conflict_do_update(
                index_elements=[MarketMatchMap.kalshi_market_id, MarketMatchMap.polymarket_market_id],
                set_={'league': kalshi_ticker[2:5],
                      'profit': profit,
                      'direction': direction,
                      'last_updated': now}
            )
            db.execute(map_stmt)
            db.commit()
