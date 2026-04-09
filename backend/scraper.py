import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import InsiderTransaction
from .utils import normalize_role, calculate_score
import pdfplumber
import io
import re
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image

from playwright.sync_api import sync_playwright

obb = None

# Final correct IDX API URL
IDX_API_URL = "https://www.idx.co.id/primary/ListedCompany/GetAnnouncement"
KEYWORDS = [
    "Laporan Kepemilikan"
]

def parse_pdf_content(pdf_bytes: bytes, source_url: str, filing_date_str: str) -> List[Dict[str, Any]]:
    transactions = []
    try:
        full_text = ""
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                full_text += page.extract_text() or ""
        
        if len(full_text.strip()) < 50:
            try:
                images = convert_from_bytes(pdf_bytes)
                for image in images:
                    full_text += pytesseract.image_to_string(image, lang='ind+eng')
            except: pass
        
        if not full_text: return []

        # Improved Ticker extraction
        ticker_match = re.search(r"([A-Z]{4})\.JK", full_text)
        if not ticker_match:
            ticker_match = re.search(r"\(([A-Z]{4})\)", full_text)
        ticker = ticker_match.group(1) if ticker_match else "UNKNOWN"
        
        insider_match = re.search(r"(?:Nama Pemegang Saham|Name of Shareholder)\s*[:=]?\s*(.*)", full_text, re.IGNORECASE)
        insider_name = insider_match.group(1).strip() if insider_match else "Unknown"

        role_match = re.search(r"(?:Jabatan|Position)\s*[:=]?\s*(.*)", full_text, re.IGNORECASE)
        role = role_match.group(1).strip() if role_match else ""

        shares_matches = re.findall(r"(?:Jumlah|Shares)\s*[:=]?\s*([\d\.,]+)", full_text, re.IGNORECASE)
        shares = 0
        if shares_matches:
            nums = [float(s.replace(".", "").replace(",", ".")) for s in shares_matches if s.replace(".", "").replace(",", ".").replace("0", "")]
            if nums: shares = max(nums)

        price_matches = re.findall(r"(?:Harga|Price)\s*[:=]?\s*(?:Rp)?\s*([\d\.,]+)", full_text, re.IGNORECASE)
        price = 0
        if price_matches:
            for p in price_matches:
                try:
                    num = float(p.replace(".", "").replace(",", "."))
                    if num > 1: 
                        price = num
                        break
                except: pass

        date_match = re.search(r"(?:Tanggal Transaksi|Waktu Pelaksanaan|Date of Transaction)\s*[:=]?\s*([\d\-/]+)", full_text, re.IGNORECASE)
        t_date = datetime.now().date()
        if date_match:
            try:
                date_str = date_match.group(1).replace("/", "-")
                for fmt in ["%d-%m-%Y", "%Y-%m-%d", "%d-%m-%y"]:
                    try:
                        t_date = datetime.strptime(date_str, fmt).date()
                        break
                    except: continue
            except: pass

        if ticker != "UNKNOWN":
             t_type = "BUY"
             full_text_lower = full_text.lower()
             if any(kw in full_text_lower for kw in ["jual", "penjualan", "pelepasan", "sell"]):
                 t_type = "SELL"
             elif any(kw in full_text_lower for kw in ["hibah", "waris", "gift"]):
                 t_type = "GIFT"

             transactions.append({
                "ticker": ticker,
                "issuer_name": "",
                "insider_name": insider_name,
                "role": role,
                "transaction_type": t_type,
                "shares": float(shares or 0),
                "price": float(price or 0),
                "value": float((shares or 0) * (price or 0)),
                "date": t_date,
                "filing_date": datetime.strptime(filing_date_str.split("T")[0], "%Y-%m-%d").date() if filing_date_str else datetime.now().date(),
                "ownership_before": 0,
                "ownership_after": 0,
                "ownership_change_pct": 0,
                "purpose": "",
                "source_url": source_url
            })
    except Exception as e:
        print(f"Error parsing PDF {source_url}: {e}")
    
    return transactions

def run_scraper(full_year=False):
    print(f"Starting scraper at {datetime.now()} (Full Year: {full_year})")
    db = SessionLocal()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            page.goto("https://www.idx.co.id/id/perusahaan-tercatat/keterbukaan-informasi/", wait_until="networkidle")
            
            # For 2026 full year, we start from today and go back
            date_to = datetime.now().strftime("%Y%m%d")
            date_from = "20260101"
            
            index_from = 0
            page_size = 50
            has_more = True
            
            while has_more:
                import urllib.parse
                params = {
                    "kodeEmiten": "",
                    "emitenType": "*",
                    "indexFrom": index_from,
                    "pageSize": page_size,
                    "dateFrom": date_from,
                    "dateTo": date_to,
                    "lang": "id",
                    "keyword": "Laporan Kepemilikan"
                }
                api_url = f"{IDX_API_URL}?{urllib.parse.urlencode(params)}"
                print(f"Fetching page {index_from // page_size + 1}: {api_url}")
                
                response = page.goto(api_url, wait_until="networkidle")
                if response and response.status == 200:
                    data = json.loads(page.inner_text("body"))
                    replies = data.get("Replies", [])
                    
                    if not replies:
                        has_more = False
                        break
                        
                    print(f"Processing {len(replies)} items from page...")
                    for disc_item in replies:
                        disc = disc_item.get("pengumuman", {})
                        attachments = disc_item.get("attachments", [])
                        
                        for att in attachments:
                            pdf_url = att.get("FullSavePath")
                            if not pdf_url: continue
                            
                            existing = db.query(InsiderTransaction).filter(InsiderTransaction.source_url == pdf_url).first()
                            if existing: continue
                            
                            print(f"Downloading PDF: {pdf_url}")
                            try:
                                pdf_response = context.request.get(pdf_url, timeout=60000)
                                if pdf_response.status == 200:
                                    pdf_bytes = pdf_response.body()
                                    filing_date = disc.get("TglPengumuman")
                                    parsed_transactions = parse_pdf_content(pdf_bytes, pdf_url, filing_date)
                                    
                                    for t_data in parsed_transactions:
                                        t_data["score"] = calculate_score(t_data, db=db)
                                        transaction = InsiderTransaction(**t_data)
                                        db.add(transaction)
                                    db.commit()
                                else:
                                    print(f"Failed PDF: {pdf_url} ({pdf_response.status})")
                            except Exception as pdf_err:
                                print(f"Error PDF {pdf_url}: {pdf_err}")
                            time.sleep(0.5)
                    
                    index_from += page_size
                    if not full_year: has_more = False # Only one page if not full year
                else:
                    has_more = False
                    
        except Exception as e:
            print(f"Error in scraper loop: {e}")
            db.rollback()
        finally:
            browser.close()
            db.close()
            
    print(f"Scraper finished at {datetime.now()}")

if __name__ == "__main__":
    run_scraper()
