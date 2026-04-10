import sys
import os
import datetime
from sqlalchemy import create_engine, text

# Add current directory to path
sys.path.append(os.getcwd())

from backend.utils import get_price_on_date

DB_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@db:5432/openinsider")

def repair_data():
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        print("Searching for transactions with Rp 0 price/value...")
        res = conn.execute(text("SELECT id, ticker, date, shares FROM insider_transactions WHERE price = 0 OR value = 0"))
        rows = res.fetchall()
        
        print(f"Found {len(rows)} records to repair.")
        
        for row in rows:
            t_id, ticker, t_date, shares = row
            print(f"Repairing {ticker} on {t_date}...")
            
            # Fetch price from API
            price = get_price_on_date(ticker, t_date)
            if price > 0:
                value = shares * price
                conn.execute(text("UPDATE insider_transactions SET price = :p, value = :v WHERE id = :id"), 
                             {"p": price, "v": value, "id": t_id})
                print(f"  - Fixed: Price={price}, Value={value}")
            else:
                print(f"  - Failed to fetch price for {ticker}")
        
        conn.commit()
        print("Data repair complete.")

if __name__ == "__main__":
    repair_data()
