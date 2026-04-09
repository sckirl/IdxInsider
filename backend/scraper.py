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
IDX_API_URL = "https://www.idx.co.id/primary/ListedCompany/GetAnnouncement"
KEYWORDS = [
    "Laporan Kepemilikan",
    "Informasi Hasil Pelaksanaan Pembelian Kembali Saham"
]

def parse_pdf_content(pdf_bytes: bytes, source_url: str, filing_date_str: str) -> List[Dict[str, Any]]:
    """
    CPU-Bound Task: Extract text and parse transactions.
    """
    transactions = []
    try:
        full_text = ""
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                full_text += page.extract_text() or ""
        
        # If text extraction fails, use OCR
        if len(full_text.strip()) < 50:
            try:
                images = convert_from_bytes(pdf_bytes)
                for image in images:
                    full_text += pytesseract.image_to_string(image, lang='ind+eng')
            except: pass
        
        if not full_text: return []

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
                "source_url": source_url
            })
    except Exception as e:
        print(f"Error parsing PDF {source_url}: {e}")
    
    return transactions

def process_single_disclosure(pdf_info: Tuple[str, str, str]) -> List[Dict[str, Any]]:
    """
    Worker function for ProcessPoolExecutor.
    Downloads and parses a single PDF.
    """
    pdf_url, filing_date, judul = pdf_info
    
    # Internal Download (I/O)
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(pdf_url, headers=headers, timeout=30)
        if response.status_code != 200: return []
        pdf_bytes = response.content
        
        parsed = parse_pdf_content(pdf_bytes, pdf_url, filing_date)
        is_buyback = "Pembelian Kembali" in (judul or "")
        
        for t in parsed:
            t["is_buyback"] = is_buyback
            
        return parsed
    except:
        return []

def run_scraper(full_year=False):
    print(f"Starting High-Performance Scraper at {datetime.now()} (Full Year: {full_year})")
    db = SessionLocal()
    
    # 1. Fetch List (Serial Playwright - anti-bot mitigation)
    all_disclosures = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        context = browser.new_context(user_agent="Mozilla/5.0")
        page = context.new_page()
        
        try:
            page.goto("https://www.idx.co.id/id/perusahaan-tercatat/keterbukaan-informasi/", wait_until="networkidle")
            date_to = datetime.now().strftime("%Y%m%d")
            date_from = "20260101"
            
            index_from = 0
            page_size = 50
            has_more = True
            
            while has_more:
                import urllib.parse
                params = {"kodeEmiten": "", "emitenType": "*", "indexFrom": index_from, "pageSize": page_size, 
                          "dateFrom": date_from, "dateTo": date_to, "lang": "id", "keyword": "Laporan Kepemilikan"}
                api_url = f"{IDX_API_URL}?{urllib.parse.urlencode(params)}"
                print(f"Fetching List Page {index_from // page_size + 1}")
                
                response = page.goto(api_url, wait_until="networkidle")
                if response and response.status == 200:
                    data = json.loads(page.inner_text("body"))
                    replies = data.get("Replies", [])
                    if not replies: break
                    all_disclosures.extend(replies)
                    index_from += page_size
                    if not full_year: break
                else: break
        finally:
            browser.close()

    print(f"List Fetch Complete. Total Disclosures: {len(all_disclosures)}")

    # 2. Filter for New Items
    to_process = []
    for item in all_disclosures:
        disc = item.get("pengumuman", {})
        attachments = item.get("attachments", [])
        for att in attachments:
            url = att.get("FullSavePath")
            if url:
                existing = db.query(InsiderTransaction).filter(InsiderTransaction.source_url == url).first()
                if not existing:
                    to_process.append((url, disc.get("TglPengumuman"), disc.get("JudulPengumuman")))

    print(f"Items to Parse: {len(to_process)}")

    # 3. Parallel Processing (CPU-Bound OCR & Parsing)
    # Using 75% of available cores to avoid locking the system
    num_workers = max(1, multiprocessing.cpu_count() - 1)
    results_list = []
    
    print(f"Launching ProcessPool with {num_workers} workers for OCR...")
    with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(process_single_disclosure, item) for item in to_process]
        for future in concurrent.futures.as_completed(futures):
            try:
                data_rows = future.result()
                if data_rows: results_list.extend(data_rows)
            except Exception as e:
                print(f"Worker Error: {e}")

    # 4. Sequential Enrichment & Batch DB Save (I/O Bound Metadata)
    print(f"Parsing Complete. Saving {len(results_list)} records with Market Intelligence...")
    
    for t_data in results_list:
        try:
            # Enrichment (Serial but fast per ticker)
            market_meta = get_market_metadata(t_data["ticker"])
            t_data["rvol"] = market_meta["rvol"]
            t_data["price_history"] = json.dumps(market_meta["price_history"])
            
            score, reasons = calculate_score(t_data, db=db)
            t_data["score"] = score
            t_data["score_reasons"] = json.dumps(reasons)
            
            transaction = InsiderTransaction(**t_data)
            db.add(transaction)
        except Exception as e:
            print(f"Enrichment Error for {t_data.get('ticker')}: {e}")

    db.commit()
    db.close()
    print(f"Parallel Scraper Finished at {datetime.now()}")

if __name__ == "__main__":
    run_scraper()
