from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from .database import get_db, engine
from .models import InsiderTransaction, Base
from . import models

from .utils import normalize_role, calculate_score

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="IDX OpenInsider API")

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to IDX OpenInsider API"}

@app.get("/insider/latest", response_model=List[Dict[str, Any]])
def get_latest_insiders(db: Session = Depends(get_db)):
    transactions = db.query(InsiderTransaction).order_by(InsiderTransaction.filing_date.desc()).limit(100).all()
    return [t.__dict__ for t in transactions]

@app.get("/insider/top-buy", response_model=List[Dict[str, Any]])
def get_top_buys(db: Session = Depends(get_db)):
    transactions = db.query(InsiderTransaction).filter(InsiderTransaction.transaction_type == "BUY").order_by(InsiderTransaction.score.desc()).limit(50).all()
    return [t.__dict__ for t in transactions]

@app.get("/insider/top-sell", response_model=List[Dict[str, Any]])
def get_top_sells(db: Session = Depends(get_db)):
    transactions = db.query(InsiderTransaction).filter(InsiderTransaction.transaction_type == "SELL").order_by(InsiderTransaction.score.asc()).limit(50).all()
    return [t.__dict__ for t in transactions]

@app.get("/insider/by-ticker/{ticker}")
def get_insider_by_ticker(ticker: str, db: Session = Depends(get_db)):
    transactions = db.query(InsiderTransaction).filter(InsiderTransaction.ticker == ticker.upper()).order_by(InsiderTransaction.date.desc()).all()
    return {"ticker": ticker, "activity": [t.__dict__ for t in transactions]}
