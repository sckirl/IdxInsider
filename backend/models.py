from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Numeric
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class InsiderTransaction(Base):
    __tablename__ = "insider_transactions"

    id = Column(Integer, primary_key=True, index=True)
    date_reported = Column(Date, index=True)
    trade_date = Column(Date)
    ticker = Column(String, index=True)
    insider_name = Column(String, index=True)
    role = Column(String)
    transaction_type = Column(String) # BUY / SELL
    shares = Column(Numeric)
    price = Column(Numeric)
    value = Column(Numeric)
    ownership_change = Column(Float)
    score = Column(Integer, default=0)
    source_url = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<InsiderTransaction(ticker={self.ticker}, name={self.insider_name}, type={self.transaction_type})>"
