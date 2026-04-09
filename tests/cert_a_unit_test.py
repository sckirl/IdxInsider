import unittest
import sys
import os
import datetime
from unittest.mock import MagicMock

# Add the project root to sys.path
sys.path.append('/home/sckirl/IdxInsider')

from backend.utils import normalize_role, calculate_score

class TestInsiderIntelligence(unittest.TestCase):

    def test_role_normalization(self):
        self.assertEqual(normalize_role("PRESIDEN DIREKTUR"), "DIREKTUR_UTAMA")
        self.assertEqual(normalize_role("KOMISARIS UTAMA"), "KOMISARIS_UTAMA")
        self.assertEqual(normalize_role("Pemegang Saham Pengendali"), "PENGENDALI")
        self.assertEqual(normalize_role("Unknown Position"), "OTHERS")

    def test_intelligent_scoring(self):
        # Case 1: CEO Buy with Buyback overlap
        t_high = {
            "ticker": "BBCA",
            "role": "DIREKTUR UTAMA",
            "transaction_type": "BUY",
            "value": 11_000_000_000,
            "direct_ownership": True,
            "is_buyback": True,
            "rvol": 2.5
        }
        score, reasons = calculate_score(t_high)
        
        # Base: CEO(+5) + Ultra Large(+5) + Direct(+1) + Buyback(+3) + RVOL(+2) = 16
        self.assertEqual(score, 16)
        self.assertIn("Double-Conviction: Coincides with Buyback (+3)", reasons)
        self.assertIn("High RVOL 2.5x (+2)", reasons)

    def test_cluster_bonus(self):
        # Mock DB for cluster check
        mock_db = MagicMock()
        t_cluster = {
            "ticker": "GOTO",
            "insider_name": "NEW_BUYER",
            "role": "DIREKTUR",
            "transaction_type": "BUY",
            "value": 100_000_000,
            "date": datetime.date(2026, 4, 9)
        }
        
        # Simulate 2 other insiders found in DB
        mock_db.query.return_value.filter.return_value.distinct.return_value.count.return_value = 2
        
        score, reasons = calculate_score(t_cluster, db=mock_db)
        # DIREKTUR(+3) + Value(+1) + Direct(+1) + ClusterBonus(+5) = 10
        self.assertEqual(score, 10)
        self.assertTrue(any("Strong Cluster" in r for r in reasons))

if __name__ == '__main__':
    unittest.main()
