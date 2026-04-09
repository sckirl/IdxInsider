import json
import os
from datetime import datetime
from .database import SessionLocal
from .models import InsiderTransaction
from .utils import calculate_score

def seed_data():
    db = SessionLocal()
    # Path relative to backend directory in container
    test_cases_path = "/docs/TEST_CASES.json"
    if not os.path.exists(test_cases_path):
        # Fallback if mounted differently
        test_cases_path = "/home/sckirl/IdxInsider/docs/TEST_CASES.json"
        # Try local to backend
        if not os.path.exists(test_cases_path):
            test_cases_path = "docs/TEST_CASES.json"

    try:
        # In the container, we might need to find where docs is. 
        # Actually, let's just use the absolute path from the root of the project inside container if mapped.
        # But wait, docs is NOT copied into backend. 
        # I'll use a hardcoded small subset if I can't find it, or just copy it.
        
        # Let's try to find it
        possible_paths = [
            "/docs/TEST_CASES.json",
            "../docs/TEST_CASES.json",
            "docs/TEST_CASES.json",
            "/app/docs/TEST_CASES.json"
        ]
        
        data = None
        for p in possible_paths:
            if os.path.exists(p):
                with open(p, "r") as f:
                    data = json.load(f)
                break
        
        if data is None:
            print("Could not find TEST_CASES.json, using fallback internal data.")
            data = [
              {
                "ticker": "BBCA",
                "insider_name": "Jahja Setiaatmadja",
                "role": "DIREKTUR",
                "transaction_type": "BUY",
                "shares": 10000,
                "price": 9000,
                "value": 90000000,
                "date": "2023-10-01",
                "filing_date": "2023-10-02",
                "ownership_before": 1000000,
                "ownership_after": 1010000,
                "ownership_change_pct": 1.0,
                "direct_ownership": True,
                "purpose": "Investasi",
                "source_url": "https://www.idx.co.id/filings/12345.pdf"
              },
              {
                "ticker": "GOTO",
                "insider_name": "Patrick Sugito Walujo",
                "role": "DIREKTUR",
                "transaction_type": "BUY",
                "shares": 500000,
                "price": 60,
                "value": 30000000,
                "date": "2023-10-05",
                "filing_date": "2023-10-06",
                "ownership_before": 50000000,
                "ownership_after": 50500000,
                "ownership_change_pct": 1.0,
                "direct_ownership": True,
                "purpose": "Investasi",
                "source_url": "https://www.idx.co.id/filings/67890.pdf"
              }
            ]
            
        for entry in data:
            # Check if exists
            existing = db.query(InsiderTransaction).filter(
                InsiderTransaction.ticker == entry["ticker"],
                InsiderTransaction.insider_name == entry["insider_name"]
            ).first()
            
            if not existing:
                # Convert date strings to date objects if they are strings
                if isinstance(entry["date"], str):
                    entry["date"] = datetime.strptime(entry["date"], "%Y-%m-%d").date()
                if isinstance(entry["filing_date"], str):
                    entry["filing_date"] = datetime.strptime(entry["filing_date"], "%Y-%m-%d").date()
                
                entry["score"] = calculate_score(entry)
                
                transaction = InsiderTransaction(**entry)
                db.add(transaction)
                print(f"Seeded: {entry['ticker']} - {entry['insider_name']}")
        
        db.commit()
        print("Seeding complete.")
    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
