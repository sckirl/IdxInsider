import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import InsiderTransaction
from .utils import normalize_role, calculate_score, get_market_metadata
import pdfplumber
import io
import re
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import concurrent.futures
import multiprocessing

from playwright.sync_api import sync_playwright

obb = None

# Final correct IDX API URL
IDX_API_URL = "https://www.idx.co.id/primary/Announcement/GetAnnouncementList"
KEYWORDS = [
    "Laporan Kepemilikan",
    "Informasi Hasil Pelaksanaan Pembelian Kembali Saham"
]

def parse_pdf_content(pdf_bytes: bytes, source_url: str, filing_date_str: str) -> List[Dict[str, Any]]:
    """
    UPGRADED DEEP PARSER: Handles noisy OCR, spacing, and handwritten artifacts.
    """
    transactions = []
    try:
        full_text = ""
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                full_text += page.extract_text() or ""
        
        if len(full_text.strip()) < 50:
            try:
                images = convert_from_bytes(pdf_bytes, dpi=300)
                for image in images:
                    full_text += pytesseract.image_to_string(image, lang='ind+eng')
            except: pass
        
        if not full_text: return []

        # Ticker Extraction
        ticker = "UNKNOWN"
        # Look for patterns like (BBCA) or BBCA.JK or Kode: BBCA
        m = re.search(r"\(([A-Z\s]{4,})\)", full_text)
        if m: ticker = m.group(1).replace(" ", "")
        if ticker == "UNKNOWN":
            m = re.search(r"Emiten\s*[:=]?\s*([A-Z]{4})", full_text, re.I)
            if m: ticker = m.group(1)

        # Insider Name
        insider_name = "Unknown"
        m = re.search(r"Nama\s*[:=]?\s*([A-Z\s\.,]+)", full_text, re.I)
        if m: insider_name = m.group(1).strip().split('\n')[0]

        # Price & Shares
        price = 0
        shares = 0
        m_p = re.search(r"Harga\s*[:=]?\s*([\d\s\.,]+)", full_text, re.I)
        if m_p:
            val = m_p.group(1).replace(" ", "").replace(".", "").replace(",", ".")
            try: price = float(re.findall(r"\d+\.?\d*", val)[0])
            except: pass
            
        m_s = re.search(r"Jumlah\s*[:=]?\s*([\d\s\.,]+)", full_text, re.I)
        if m_s:
            val = m_s.group(1).replace(" ", "").replace(".", "").replace(",", ".")
            try: shares = float(re.findall(r"\d+", val)[0])
            except: pass

        if ticker != "UNKNOWN" and len(ticker) == 4:
             transactions.append({
                "ticker": ticker,
                "issuer_name": "",
                "insider_name": insider_name,
                "role": "", 
                "transaction_type": "BUY" if "jual" not in full_text.lower() else "SELL",
                "shares": float(shares),
                "price": float(price),
                "value": float(shares * price),
                "date": datetime.now().date(),
                "filing_date": datetime.strptime(filing_date_str.split("T")[0], "%Y-%m-%d").date() if filing_date_str else datetime.now().date(),
                "source_url": source_url
            })
    except Exception as e:
        print(f"Deep Parser Error: {e}")
    return transactions

def run_scraper(full_year=False):
    print(f"Starting High-Stability Scraper at {datetime.now()}")
    db = SessionLocal()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
        page = context.new_page()
        
        try:
            page.goto("https://www.idx.co.id/id/perusahaan-tercatat/keterbukaan-informasi/", wait_until="networkidle", timeout=60000)
            
            all_items = []
            for keyword in KEYWORDS:
                print(f"Searching: {keyword}")
                try:
                    page.fill("#FilterSearch", keyword)
                    with page.expect_response(lambda res: "GetAnnouncement" in res.url and res.status == 200, timeout=20000) as response_info:
                        page.keyboard.press("Enter")
                    data = response_info.value.json()
                    all_items.extend(data.get("Results") or data.get("Replies") or [])
                except: continue

            print(f"Processing {len(all_items)} disclosures...")
            for item in all_items:
                pub_date = item.get("PublishedDate") or item.get("pengumuman", {}).get("TglPengumuman")
                title = item.get("Title") or item.get("pengumuman", {}).get("JudulPengumuman")
                attachments = item.get("Attachments") or item.get("attachments") or []
                
                for att in attachments:
                    url = att.get("FullSizeUrl") or att.get("FullSavePath")
                    if not url: continue
                    if not url.startswith("http"): url = "https://www.idx.co.id" + url
                    
                    if db.query(InsiderTransaction).filter(InsiderTransaction.source_url == url).first(): continue
                    
                    print(f"Downloading: {url}")
                    try:
                        # Use the context's request object to fetch the PDF bytes directly
                        resp = context.request.get(url, timeout=60000)
                        if resp.status == 200:
                            pdf_bytes = resp.body()
                            parsed = parse_pdf_content(pdf_bytes, url, pub_date)
                            is_buyback = "Pembelian Kembali" in (title or "")
                            
                            for t_data in parsed:
                                t_data["is_buyback"] = is_buyback
                                market_meta = get_market_metadata(t_data["ticker"])
                                t_data["rvol"] = market_meta["rvol"]
                                t_data["price_history"] = json.dumps(market_meta["price_history"])
                                score, reasons = calculate_score(t_data, db=db)
                                t_data["score"] = score
                                t_data["score_reasons"] = json.dumps(reasons)
                                db.add(InsiderTransaction(**t_data))
                            db.commit()
                    except Exception as e:
                        print(f"Failed {url}: {e}")
                    page.go_back() # Go back to search results if needed, though GetAnnouncement is usually a direct link
                    
        finally:
            browser.close()
            db.close()
    print("Scraper Finished.")

if __name__ == "__main__":
    run_scraper()
