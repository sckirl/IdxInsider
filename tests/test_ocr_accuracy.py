import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Mock the entire database module to avoid psycopg2 dependency
sys.modules['backend.database'] = MagicMock()
sys.modules['sqlalchemy'] = MagicMock()
sys.modules['sqlalchemy.orm'] = MagicMock()
sys.modules['sqlalchemy.ext.declarative'] = MagicMock()

# Add the project root to sys.path
sys.path.append('/home/sckirl/IdxInsider')

from backend.scraper import parse_pdf_content
import io

class TestOCRAccuracy(unittest.TestCase):
    @patch('backend.scraper.pdfplumber.open')
    @patch('backend.scraper.convert_from_bytes')
    @patch('backend.scraper.pytesseract.image_to_string')
    def test_ocr_fallback_extraction(self, mock_tesseract, mock_convert, mock_pdfplumber):
        # 1. Setup mock pdfplumber to return empty text (scanned)
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "" # Empty text
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf
        
        # 2. Setup mock image conversion
        mock_convert.return_value = [MagicMock()]
        
        # 3. Setup mock OCR text (scanned)
        mock_tesseract.return_value = """
        Nama Perusahaan Terbuka (Emiten) : PT Bank Central Asia Tbk. (BBCA)
        Nama Pemegang Saham: Jahja Setiaatmadja
        Jabatan: Direktur Utama
        Jumlah: 1.000.000
        Harga: 9.000
        Tujuan: Investasi
        Beli
        Sebelum: 10.000.000
        Sesudah: 11.000.000
        """
        
        # 4. Call parse_pdf_content
        pdf_bytes = b"fake pdf content"
        source_url = "https://www.idx.co.id/filings/scanned.pdf"
        filing_date_str = "2026-04-05T00:00:00"
        
        results = parse_pdf_content(pdf_bytes, source_url, filing_date_str)
        
        # 5. Assert results
        if len(results) == 1:
            t = results[0]
            print(f"Extracted Ticker: {t['ticker']}")
            print(f"Extracted Shares: {t['shares']}")
            self.assertEqual(t['ticker'], "BBCA")
            self.assertEqual(t['shares'], 1000000.0)
            self.assertEqual(t['transaction_type'], "BUY")
            self.assertEqual(t['price'], 9000.0)
            print("Certification A: OCR Accuracy passed!")
        else:
            self.fail(f"Expected 1 transaction, got {len(results)}")

if __name__ == '__main__':
    unittest.main()
