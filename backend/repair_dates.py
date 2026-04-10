import sys
import os
import datetime
import requests
import io
import base64
import pdfplumber
from sqlalchemy import create_engine, text

# Add current directory to path
sys.path.append(os.getcwd())

from backend.scraper import extract_transaction_date

DB_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@db:5432/openinsider")

def repair_dates():
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        print("Searching for transactions where date may be inaccurate (defaults to filing date)...")
        res = conn.execute(text("SELECT id, source_url, date, filing_date FROM insider_transactions"))
        rows = res.fetchall()
        
        fixed = 0
        for row in rows:
            t_id, url, current_date, filing_date = row
            
            try:
                # Fetch PDF content via requests (since we are in the container)
                # We use a simple fetch since these are internal or direct URLs
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    full_text = ""
                    with pdfplumber.open(io.BytesIO(resp.content)) as pdf:
                        for page in pdf.pages:
                            full_text += page.extract_text(layout=True) or ""
                    
                    new_date = extract_transaction_date(full_text)
                    if new_date and new_date != current_date:
                        conn.execute(text("UPDATE insider_transactions SET date = :d WHERE id = :id"), 
                                     {"d": new_date, "id": t_id})
                        print(f"  - Fixed Date for ID {t_id}: {current_date} -> {new_date}")
                        fixed += 1
            except Exception as e:
                pass
        
        conn.commit()
        print(f"Date repair complete. Fixed {fixed} records.")

if __name__ == "__main__":
    repair_dates()
