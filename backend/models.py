from decimal import Decimal
from sqlalchemy import Column, Integer, Float, Numeric, String, ForeignKey, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy import UniqueConstraint

Base = declarative_base()

class KalshiMarket(Base):
    __tablename__ = 'kalshi_markets'
    id = Column(Integer, primary_key=True)
    ticker = Column(String, unique=True, nullable=False)
    league = Column(String)
    title = Column(String)
    team = Column(String, nullable=False)   # 'home' or 'away' or actual team code
    yes_ask_dollars = Column(Numeric)
    no_ask_dollars = Column(Numeric)
    last_updated = Column(DateTime, default=datetime.utcnow, index=True)
    match = relationship('MarketMatchMap', back_populates='kalshi_market', uselist=False)

class PolymarketMarket(Base):
    __tablename__ = 'polymarket_markets'
    id = Column(Integer, primary_key=True)
    slug = Column(String, unique=True, nullable=False)
    league = Column(String)
    title = Column(String)
    home_team = Column(String, nullable=False)
    away_team = Column(String, nullable=False)
    home_price = Column(Numeric)  # YES price for home team
    away_price = Column(Numeric)  # YES price for away team
    last_updated = Column(DateTime, default=datetime.utcnow, index=True)
    match = relationship('MarketMatchMap', back_populates='polymarket_market', uselist=False)

class MarketMatchMap(Base):
    __tablename__ = 'market_match_map'
    id = Column(Integer, primary_key=True)
    kalshi_market_id = Column(Integer, ForeignKey('kalshi_markets.id'), unique=True)
    polymarket_market_id = Column(Integer, ForeignKey('polymarket_markets.id'))
    profit = Column(Numeric, default=0)  # Max profit for this matchup
    direction = Column(String)           # e.g., 'YES_Kalshi + NO_Poly' or reverse
    match_score = Column(Numeric)  # Optional for future use
    league = Column(String)
    last_updated = Column(DateTime, default=datetime.utcnow, index=True)
    kalshi_market = relationship('KalshiMarket', back_populates='match')
    polymarket_market = relationship('PolymarketMarket', back_populates='match')
    __table_args__ = (UniqueConstraint('kalshi_market_id', 'polymarket_market_id', name='uix_kalshi_polymarket'),)
    # Optionally, add metadata, sport, etc.

