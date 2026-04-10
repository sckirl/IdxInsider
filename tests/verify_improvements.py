import sys
import os
import json
from datetime import datetime, date
import unittest
from unittest.mock import MagicMock, patch

# Ensure we use sqlite for testing
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

# Mocking the database and some dependencies to avoid compilation issues
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.binary'] = MagicMock()

# Add backend to path
sys.path.append(os.getcwd())

from backend.scraper import extract_transaction_date, parse_pdf_content
from backend.utils import get_price_on_date

class TestScraperImprovements(unittest.TestCase):
    def test_date_extraction_patterns(self):
        # Indonesian format
        text_id = "Tanggal Transaksi : 15 Maret 2026"
        self.assertEqual(extract_transaction_date(text_id), date(2026, 3, 15))
        
        # English format
        text_en = "Date of Transaction: April 10, 2026"
        self.assertEqual(extract_transaction_date(text_en), date(2026, 4, 10))
        
        # Slash format
        text_slash = "Tanggal Transaksi: 01/01/2026"
        self.assertEqual(extract_transaction_date(text_slash), date(2026, 1, 1))

    def test_price_fallback_logic(self):
        # This test actually calls yfinance if internet is available
        # or we can mock it. Let's try real call first for BBCA
        p = get_price_on_date("BBCA", date(2026, 4, 1))
        print(f"BBCA Price on 2026-04-01: {p}")
        self.assertGreaterEqual(p, 0)

    def test_company_format_caching(self):
        # Check if file exists and is readable
        if os.path.exists("backend/company_formats.json"):
            with open("backend/company_formats.json", "r") as f:
                data = json.load(f)
                self.assertIsInstance(data, dict)

if __name__ == "__main__":
    unittest.main()
