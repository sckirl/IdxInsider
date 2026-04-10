from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any
import asyncio
from datetime import datetime, timezone, timedelta
import threading

from .database import get_db, engine, SessionLocal
from .models import InsiderTransaction, Base
from . import models
from .scraper import run_scraper
from .utils import normalize_role, calculate_score

import os

# Create tables
try:
    models.Base.metadata.create_all(bind=engine)
    print("Database tables created/verified.")
except Exception as e:
    print(f"Warning: Database tables could not be created during startup: {e}")

app = FastAPI(title="IDX OpenInsider API")

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

async def run_scraper_async(full_year=False):
    try:
        print(f"Background Task: Running scraper (full_year={full_year})...")
        await asyncio.to_thread(run_scraper, full_year=full_year)
        print("Background Task: Scraper finished.")
    except Exception as e:
        print(f"Background Task Error: {e}")

async def daily_scheduler():
    import random
    while True:
        now_wib = datetime.now(timezone(timedelta(hours=7)))
        # Random hour between 1 and 4 (inclusive), random minute between 0 and 59
        random_hour = random.randint(1, 4)
        random_minute = random.randint(0, 59)
        
        target_time = now_wib.replace(hour=random_hour, minute=random_minute, second=0, microsecond=0)
        if now_wib >= target_time:
            target_time += timedelta(days=1)
        
        wait_seconds = (target_time - now_wib).total_seconds()
        print(f"Scheduler: Next run at {target_time} (WIB), waiting {wait_seconds} seconds.")
        
        await asyncio.sleep(wait_seconds)
        await run_scraper_async()

@app.on_event("startup")
async def startup_event():
    print("Startup: Triggering daily scheduler...")
    asyncio.create_task(daily_scheduler())

@app.get("/health")
def health_check():
    try:
        # Check DB connection
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "healthy", "database": "connected", "timestamp": datetime.now()}
    except Exception as e:
        return {"status": "degraded", "database": str(e), "timestamp": datetime.now()}

@app.get("/")
def read_root():
    return {"message": "Welcome to IDX OpenInsider API", "status": "running"}

@app.get("/insider/scrape")
def trigger_scrape(background_tasks: BackgroundTasks, full_year: bool = False):
    background_tasks.add_task(run_scraper, full_year=full_year)
    return {"message": f"Scraper task (full_year={full_year}) added to background queue"}

@app.get("/insider/latest", response_model=List[Dict[str, Any]])
def get_latest_insiders(db: Session = Depends(get_db)):
    try:
        transactions = db.query(InsiderTransaction).order_by(InsiderTransaction.filing_date.desc()).limit(1000).all()
        result = []
        for t in transactions:
            t_dict = {c.name: getattr(t, c.name) for c in t.__table__.columns}
            result.append(t_dict)
        return result
    except Exception as e:
        print(f"Error fetching latest insiders: {e}")
        return []

@app.get("/insider/top-buy", response_model=List[Dict[str, Any]])
def get_top_buys(db: Session = Depends(get_db)):
    transactions = db.query(InsiderTransaction).filter(InsiderTransaction.transaction_type == "BUY").order_by(InsiderTransaction.score.desc()).limit(50).all()
    return [{c.name: getattr(t, c.name) for c in t.__table__.columns} for t in transactions]

@app.get("/insider/top-sell", response_model=List[Dict[str, Any]])
def get_top_sells(db: Session = Depends(get_db)):
    transactions = db.query(InsiderTransaction).filter(InsiderTransaction.transaction_type == "SELL").order_by(InsiderTransaction.score.asc()).limit(50).all()
    return [{c.name: getattr(t, c.name) for c in t.__table__.columns} for t in transactions]

@app.get("/insider/clusters")
def get_insider_clusters(
    min_insiders: int = 2, 
    max_insiders: int = 100, 
    days: int = 30, 
    db: Session = Depends(get_db)
):
    """
    Identifies 'Cluster Buys' where multiple unique insiders are buying 
    the same ticker within a rolling window.
    """
    cutoff_date = datetime.now().date() - timedelta(days=days)
    
    # 1. Fetch all buys in the window
    buys = db.query(InsiderTransaction).filter(
        InsiderTransaction.transaction_type == "BUY",
        InsiderTransaction.date >= cutoff_date
    ).all()
    
    # 2. Group by ticker
    from collections import defaultdict
    ticker_groups = defaultdict(list)
    for b in buys:
        ticker_groups[b.ticker].append(b)
        
    # 3. Analyze unique insiders per ticker
    clusters = []
    for ticker, transactions in ticker_groups.items():
        unique_insiders = set(t.insider_name for t in transactions)
        count = len(unique_insiders)
        
        if min_insiders <= count <= max_insiders:
            # Sort transactions by date
            transactions.sort(key=lambda x: x.date, reverse=True)
            
            clusters.append({
                "ticker": ticker,
                "insider_count": count,
                "transaction_count": len(transactions),
                "last_date": transactions[0].date,
                "total_value": sum(t.value for t in transactions),
                "insiders": list(unique_insiders),
                "activity": [{c.name: getattr(t, c.name) for c in t.__table__.columns} for t in transactions]
            })
            
    # Sort clusters by insider count (high to low)
    clusters.sort(key=lambda x: x["insider_count"], reverse=True)
    return clusters
