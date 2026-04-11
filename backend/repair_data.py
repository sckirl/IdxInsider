import os
import datetime
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models import InsiderTransaction
from backend.utils import get_price_on_date, calculate_ownership_change, calculate_score

from sqlalchemy import or_

def repair_zero_prices():
    """
    Finds transactions with price=0 OR value=0 and attempts to backfill them.
    Also removes misparsed records with reserved keywords or obviously wrong tickers.
    """
    db = SessionLocal()
    RESERVED_KEYWORDS = ["KETR", "LAPP", "LAMP", "BERI", "DATA", "INFO"]
    try:
        # 1. Cleanup misparsed
        print("Cleaning up misparsed records...")
        deleted = db.query(InsiderTransaction).filter(
            or_(
                InsiderTransaction.ticker.in_(RESERVED_KEYWORDS),
                InsiderTransaction.insider_name.contains("Keterbukaan"),
                InsiderTransaction.insider_name.contains("Informasi")
            )
        ).delete(synchronize_session=False)
        db.commit()
        print(f"Deleted {deleted} misparsed records.")

        # 2. Fix 0 values
        problematic = db.query(InsiderTransaction).filter(
            or_(
                InsiderTransaction.price == 0,
                InsiderTransaction.value == 0
            )
        ).all()
        print(f"Found {len(problematic)} transactions with price or value 0.")
        
        fixed_count = 0
        for t in problematic:
            if not t.ticker or t.ticker == "UNKNOWN": continue
            
            # Get Price
            price = get_price_on_date(t.ticker, t.date)
            if price > 0:
                t.price = price
                if not t.shares or t.shares == 0:
                    t.shares = 1.0 # Minimal fallback
                t.value = t.shares * t.price
                fixed_count += 1
                print(f"  Fixed {t.ticker} on {t.date}: Price set to {price}, Value set to {t.value}")
            
            # Recalculate Score
            t_dict = {c.name: getattr(t, c.name) for c in t.__table__.columns}
            score, reasons = calculate_score(t_dict, db=db)
            t.score = score
            import json
            t.score_reasons = json.dumps(reasons)

        db.commit()
        print(f"Repair finished. {fixed_count} transactions updated.")
        
        # Also recalculate ownership_change_pct for non-zero prices that were missing it
        missing_pct = db.query(InsiderTransaction).filter(
            InsiderTransaction.ownership_change_pct == 0,
            InsiderTransaction.ownership_before > 0,
            InsiderTransaction.ownership_after > 0
        ).all()
        
        if missing_pct:
            print(f"Backfilling {len(missing_pct)} ownership change percentages...")
            for t in missing_pct:
                t.ownership_change_pct = calculate_ownership_change(t.ownership_before, t.ownership_after)
            db.commit()
            print("Done.")

    except Exception as e:
        print(f"Repair failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    repair_zero_prices()
