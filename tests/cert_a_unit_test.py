import unittest
import sys
import os
import datetime
from unittest.mock import MagicMock

# Add the project root to sys.path
sys.path.append('/home/sckirl/IdxInsider')

from backend.utils import normalize_role, calculate_score

class TestUtils(unittest.TestCase):
    def test_normalize_role(self):
        self.assertEqual(normalize_role('DIREKTUR UTAMA'), 'DIREKTUR_UTAMA')
        self.assertEqual(normalize_role('PRESIDEN DIREKTUR'), 'DIREKTUR_UTAMA')
        self.assertEqual(normalize_role('CEO'), 'DIREKTUR_UTAMA')
        self.assertEqual(normalize_role('DIREKTUR'), 'DIREKTUR')
        self.assertEqual(normalize_role('KOMISARIS UTAMA'), 'KOMISARIS_UTAMA')
        self.assertEqual(normalize_role('KOMISARIS'), 'KOMISARIS')
        self.assertEqual(normalize_role('PENGENDALI'), 'PENGENDALI')
        self.assertEqual(normalize_role('UTAMA'), 'PEMEGANG_SAHAM_UTAMA')
        self.assertEqual(normalize_role(''), 'OTHERS')
        self.assertEqual(normalize_role('STAFF'), 'OTHERS')

    def test_calculate_score_buy(self):
        # Direktur Utama BUY, 11B IDR value, direct ownership
        t1 = {
            'transaction_type': 'BUY',
            'role': 'DIREKTUR UTAMA',
            'value': 11_000_000_000,
            'direct_ownership': True,
            'ownership_change_pct': 0.01,
            'ticker': 'BBCA',
            'date': datetime.date.today()
        }
        # Role: 5, Value: 5, Direct: 1 = 11
        self.assertEqual(calculate_score(t1), 11)

    def test_calculate_score_gift(self):
        # Hibah/Waris should be GIFT and score should be 0
        t_gift = {
            'transaction_type': 'GIFT',
            'role': 'DIREKTUR UTAMA',
            'value': 100_000_000_000,
            'ticker': 'TLKM',
            'date': datetime.date.today()
        }
        self.assertEqual(calculate_score(t_gift), 0)

    def test_calculate_score_sell(self):
        # Direktur Utama SELL, 6B value
        t3 = {
            'transaction_type': 'SELL',
            'role': 'DIREKTUR UTAMA',
            'value': 6_000_000_000
        }
        # SELL: -2, Dir Utama: -1, Large Value: -2 = -5
        self.assertEqual(calculate_score(t3), -5)

    def test_cluster_buy_logic(self):
        # Mock DB
        mock_db = MagicMock()
        
        t_cluster = {
            'transaction_type': 'BUY',
            'role': 'KOMISARIS',
            'value': 200_000_000,
            'direct_ownership': True,
            'ticker': 'GOTO',
            'date': datetime.date.today(),
            'insider_name': 'Insider A'
        }

        # Scenario 1: total 2 insiders (other_insiders_count = 1)
        # Base: KOMISARIS(2) + Value(1) + Direct(1) = 4
        # Bonus: 2 insiders total = +3
        # Total: 7
        
        # db.query(...).filter(...).distinct().count()
        # count() should return 1.
        mock_db.query.return_value.filter.return_value.distinct.return_value.count.return_value = 1
        self.assertEqual(calculate_score(t_cluster, db=mock_db), 7)

        # Scenario 2: total 3 insiders (other_insiders_count = 2)
        # Base: 4
        # Bonus: 3+ insiders total = +5
        # Total: 9
        mock_db.query.return_value.filter.return_value.distinct.return_value.count.return_value = 2
        self.assertEqual(calculate_score(t_cluster, db=mock_db), 9)

if __name__ == '__main__':
    unittest.main()
