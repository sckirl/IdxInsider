from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Numeric, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import datetime

Base = declarative_base()

class InsiderTransaction(Base):
    __tablename__ = "insider_transactions"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), index=True)
    issuer_name = Column(String(255))
    insider_name = Column(String(255), index=True)
    role = Column(String(100))
    transaction_type = Column(String(20)) # BUY, SELL, GIFT, EXERCISE, INHERITANCE, OTHERS
    shares = Column(Float)
    price = Column(Float)
    value = Column(Float)
    date = Column(Date, index=True) # Actual transaction date
    filing_date = Column(Date, index=True) # Date published on IDX
    ownership_before = Column(Float)
    ownership_after = Column(Float)
    ownership_change_pct = Column(Float)
    direct_ownership = Column(Boolean, default=True)
    purpose = Column(Text)
    source_url = Column(String(511), unique=True)
    score = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<InsiderTransaction(ticker={self.ticker}, name={self.insider_name}, type={self.transaction_type})>"
