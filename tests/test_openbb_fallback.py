import sys
import os
from datetime import datetime

# Mock the database part
class MockDB:
    def query(self, model): return self
    def filter(self, condition): return self
    def first(self): return None
    def add(self, item): pass
    def commit(self): pass
    def rollback(self): pass
    def close(self): pass

def test_openbb():
    try:
        from openbb import obb
        print("OpenBB SDK found.")
    except ImportError:
        print("OpenBB SDK NOT found.")
        return

    ticker = "BBRI"
    print(f"Testing OpenBB fallback for {ticker}...")
    try:
        # Check if sectors extension is available
        if hasattr(obb, "sectors"):
             print("OpenBB Sectors extension found.")
             # data = obb.sectors.insider_transactions(symbol=ticker, provider="sectors")
             # print(f"Data: {data}")
        else:
             print("OpenBB Sectors extension NOT found.")
    except Exception as e:
        print(f"Error testing OpenBB: {e}")

if __name__ == "__main__":
    test_openbb()
