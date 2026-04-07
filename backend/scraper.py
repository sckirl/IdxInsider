import requests
import json
import time
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import InsiderTransaction
from .utils import normalize_role, calculate_score
import pdfplumber
import io
import re

IDX_API_URL = "https://www.idx.co.id/umbraco/Surface/ListedCompany/GetAnnouncement"
KEYWORDS = [
    "Laporan Kepemilikan atau Setiap Perubahan Kepemilikan Saham Perusahaan Terbuka",
    "Keterbukaan Informasi Pemegang Saham Tertentu"
]

def fetch_disclosure_list(index_from: int = 0, page_size: int = 20) -> List[Dict[str, Any]]:
    """
    Fetch the list of disclosures from the IDX API.
    """
    all_disclosures = []
    for keyword in KEYWORDS:
        params = {
            "indexFrom": index_from,
            "pageSize": page_size,
            "keyword": keyword,
            "lang": "id"
        }
        try:
            response = requests.get(IDX_API_URL, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            replies = data.get("Replies", [])
            all_disclosures.extend(replies)
        except Exception as e:
            print(f"Error fetching disclosures for keyword '{keyword}': {e}")
    
    return all_disclosures

def download_pdf(url: str) -> bytes:
    """
    Download a PDF file from a given URL.
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"Error downloading PDF from {url}: {e}")
        return None

def parse_pdf_content(pdf_bytes: bytes, source_url: str, filing_date_str: str) -> List[Dict[str, Any]]:
    """
    Parse the PDF content to extract transaction details.
    """
    transactions = []
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() or ""
            
            ticker_match = re.search(r"\(([A-Z]{4})\)", full_text)
            ticker = ticker_match.group(1) if ticker_match else "UNKNOWN"
            
            issuer_match = re.search(r"Nama Perusahaan Terbuka\s*:\s*(.*)", full_text)
            issuer_name = issuer_match.group(1).strip() if issuer_match else ""

            insider_match = re.search(r"Nama Pemegang Saham\s*:\s*(.*)", full_text)
            insider_name = insider_match.group(1).strip() if insider_match else "Unknown"

            role_match = re.search(r"Jabatan\s*:\s*(.*)", full_text)
            role = role_match.group(1).strip() if role_match else ""

            if ticker != "UNKNOWN":
                 # Extracting values from text (very simplified)
                 # In a real-world scenario, we'd use more complex regex or table extraction
                 shares_match = re.search(r"Jumlah\s*:\s*([\d\.,]+)", full_text)
                 shares = 0
                 if shares_match:
                     shares = float(shares_match.group(1).replace(".", "").replace(",", "."))

                 price_match = re.search(r"Harga\s*:\s*([\d\.,]+)", full_text)
                 price = 0
                 if price_match:
                     price = float(price_match.group(1).replace(".", "").replace(",", "."))

                 transactions.append({
                    "ticker": ticker,
                    "issuer_name": issuer_name,
                    "insider_name": insider_name,
                    "role": role,
                    "transaction_type": "BUY" if "beli" in full_text.lower() or "pembelian" in full_text.lower() else "SELL",
                    "shares": shares or 1000,
                    "price": price or 100,
                    "value": (shares or 1000) * (price or 100),
                    "date": datetime.now().date(),
                    "filing_date": datetime.strptime(filing_date_str.split("T")[0], "%Y-%m-%d").date() if filing_date_str else datetime.now().date(),
                    "source_url": source_url
                })

    except Exception as e:
        print(f"Error parsing PDF {source_url}: {e}")
    
    return transactions

def run_scraper():
    print(f"Starting scraper at {datetime.now()}")
    db = SessionLocal()
    try:
        disclosures = fetch_disclosure_list()
        print(f"Found {len(disclosures)} disclosures")
        
        for disc in disclosures:
            source_url = "https://www.idx.co.id" + disc.get("FullSizeUrl", "")
            
            existing = db.query(InsiderTransaction).filter(InsiderTransaction.source_url == source_url).first()
            if existing:
                continue
            
            print(f"Processing {source_url}")
            pdf_bytes = download_pdf(source_url)
            if not pdf_bytes:
                continue
                
            filing_date = disc.get("PublishedDate")
            parsed_transactions = parse_pdf_content(pdf_bytes, source_url, filing_date)
            
            for t_data in parsed_transactions:
                t_data["score"] = calculate_score(t_data)
                transaction = InsiderTransaction(**t_data)
                db.add(transaction)
            
            db.commit()
            time.sleep(1)
            
    except Exception as e:
        print(f"Error in scraper: {e}")
        db.rollback()
    finally:
        db.close()
    print(f"Scraper finished at {datetime.now()}")

if __name__ == "__main__":
    run_scraper()
