import sys
import os
from datetime import datetime, date
import unittest

# Add backend to path
sys.path.append(os.getcwd())

from backend.scraper import extract_transaction_date, parse_pdf_content
from backend.utils import get_price_on_date

class TestImprovements(unittest.TestCase):
    def test_date_extraction(self):
        text = "Tanggal Transaksi: 05 Maret 2026"
        d = extract_transaction_date(text)
        self.assertEqual(d, date(2026, 3, 5))
        
        text2 = "Date of Transaction : 10/04/2026"
        d2 = extract_transaction_date(text2)
        self.assertEqual(d2, date(2026, 4, 10))

    def test_price_fallback(self):
        # BBCA.JK is a common IDX stock
        p = get_price_on_date("BBCA", date(2026, 4, 1))
        print(f"BBCA Price on 2026-04-01: {p}")
        self.assertGreater(p, 0)

if __name__ == "__main__":
    unittest.main()
