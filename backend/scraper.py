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
import base64
import os

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
    ULTRA-FLEXIBLE PARSER: Specifically tuned for IDX PDF patterns.
    """
    transactions = []
    try:
        full_text = ""
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                # Use advanced layout parameters to preserve spatial text
                full_text += page.extract_text(layout=True) or ""
        
        if not full_text.strip(): return []

        # Ticker Extraction
        ticker = "UNKNOWN"
        m1 = re.search(r"Nama Perusahaan Tbk\s*:\s*([A-Z]{4})", full_text, re.I)
        m2 = re.search(r"Issuer\s*:\s*([A-Z]{4})", full_text, re.I)
        m3 = re.search(r"Kode Emiten\s*[:]?\s*([A-Z]{4})", full_text, re.I)
        m4 = re.search(r"Kode Saham\s*[:]?\s*([A-Z]{4})", full_text, re.I)
        m5 = re.search(r"\(([A-Z]{4})\)", full_text)
        
        if m1: ticker = m1.group(1).strip()
        elif m2: ticker = m2.group(1).strip()
        elif m3: ticker = m3.group(1).strip()
        elif m4: ticker = m4.group(1).strip()
        elif m5: ticker = m5.group(1).strip()

        # Insider Name
        insider_name = "Unknown"
        m_name1 = re.search(r"Nama \(sesuai SID\)\s*:\s*([^\n]+)", full_text, re.I)
        m_name2 = re.search(r"Name \(SID\)\s*:\s*([^\n]+)", full_text, re.I)
        m_name3 = re.search(r"Nama\s*[:]\s*([^\n]+)", full_text, re.I)
        
        if m_name1: insider_name = m_name1.group(1).strip()
        elif m_name2: insider_name = m_name2.group(1).strip()
        elif m_name3: insider_name = m_name3.group(1).strip()

        # Role
        role = ""
        if re.search(r"Anggota Direksi/Dewan Komisaris\s*:\s*Ya", full_text, re.I):
            role = "DIREKTUR"

        # Price & Shares
        before_match = re.search(r"Jumlah Saham Sebelum Transaksi[^\d]*([\d\.,]+)", full_text, re.I)
        after_match = re.search(r"Jumlah Saham Setelah Transaksi[^\d]*([\d\.,]+)", full_text, re.I)
        
        shares = 0
        if before_match and after_match:
            try:
                b_str = before_match.group(1).replace(".", "").replace(",", ".")
                a_str = after_match.group(1).replace(".", "").replace(",", ".")
                shares = abs(float(b_str) - float(a_str))
            except: pass

        price = 0
        if shares > 0:
            shares_str1 = f"{shares:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            shares_str2 = f"{int(shares):,}".replace(",", ".")
            pattern = f"(?:{re.escape(shares_str1)}|{re.escape(shares_str2)})\\s+([\\d\\.,]+)"
            m_price = re.search(pattern, full_text)
            if m_price:
                try:
                    price = float(m_price.group(1).replace(".", "").replace(",", "."))
                except: pass
                
        if shares == 0:
            clean_text = full_text.replace("Rp", "").replace(".", "").replace(",", ".")
            numbers = [float(n) for n in re.findall(r"\b\d+\.\d+\b|\b\d+\b", clean_text)]
            if numbers:
                shares = max(numbers)
                potential_prices = [n for n in numbers if 1 <= n <= 200000 and n != shares]
                if potential_prices: price = potential_prices[-1]

        t_type = "SELL" if "jual" in full_text.lower() or "sales" in full_text.lower() else "BUY"

        if ticker != "UNKNOWN" and len(ticker) == 4:
             transactions.append({
                "ticker": ticker,
                "issuer_name": "",
                "insider_name": insider_name,
                "role": role, 
                "transaction_type": t_type,
                "shares": float(shares),
                "price": float(price),
                "value": float(shares * price),
                "date": datetime.now().date(),
                "filing_date": datetime.strptime(filing_date_str.split("T")[0], "%Y-%m-%d").date() if filing_date_str else datetime.now().date(),
                "source_url": source_url
            })
    except Exception as e:
        print(f"Parser Error: {e}")
    return transactions

def process_pdf(pdf_bytes: bytes, url: str, pub_date: str, title: str):
    db = SessionLocal()
    try:
        parsed = parse_pdf_content(pdf_bytes, url, pub_date)
        is_buyback = "Pembelian Kembali" in (title or "")
        
        added = 0
        for t_data in parsed:
            t_data["is_buyback"] = is_buyback
            m_meta = get_market_metadata(t_data["ticker"])
            t_data["rvol"] = m_meta["rvol"]
            t_data["price_history"] = json.dumps(m_meta["price_history"])
            score, reasons = calculate_score(t_data, db=db)
            t_data["score"] = score
            t_data["score_reasons"] = json.dumps(reasons)
            db.add(InsiderTransaction(**t_data))
            added += 1
        
        db.commit()
        if added > 0:
            print(f"  - Successfully added {added} rows from {url}.")
        return added
    except Exception as e:
        print(f"  - Error processing {url}: {e}")
        db.rollback()
        return 0
    finally:
        db.close()

def run_scraper(full_year=False):
    print(f"Starting Scraper at {datetime.now()} (Full Year: {full_year})")
    db = SessionLocal()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
        page = context.new_page()
        
        try:
            page.goto("https://www.idx.co.id/id/perusahaan-tercatat/keterbukaan-informasi/", wait_until="networkidle")
            
            all_items = []
            
            # Using browser context fetch to bypass Cloudflare
            for keyword in KEYWORDS:
                print(f"Searching: {keyword}")
                try:
                    if full_year:
                        date_from = "20260101"
                        date_to = "20261231"
                        page_size = 1000
                    else:
                        date_from = "19010101"
                        date_to = "20261231"
                        page_size = 20
                    
                    script = f"""
                    async () => {{
                        const url = "https://www.idx.co.id/primary/ListedCompany/GetAnnouncement?kodeEmiten=&emitenType=*&indexFrom=0&pageSize={page_size}&dateFrom={date_from}&dateTo={date_to}&lang=id&keyword=" + encodeURIComponent("{keyword}");
                        const res = await fetch(url);
                        return await res.json();
                    }}
                    """
                    data = page.evaluate(script)
                    items = data.get("Results") or data.get("Replies") or []
                    all_items.extend(items)
                except Exception as e:
                    print(f"Search failed for {keyword}: {e}")

            print(f"Total Disclosures Found before limit: {len(all_items)}")

            # Sort by published date descending and limit to 100 for prototype
            def get_date(x):
                d = x.get("PublishedDate") or x.get("pengumuman", {}).get("TglPengumuman") or ""
                return d

            all_items.sort(key=get_date, reverse=True)
            all_items = all_items[:300]
            print(f"Limited to top 300 disclosures for prototype.")

            futures = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                for item in all_items:
                    pub_date = item.get("PublishedDate") or item.get("pengumuman", {}).get("TglPengumuman")
                    title = item.get("Title") or item.get("pengumuman", {}).get("JudulPengumuman")
                    attachments = item.get("Attachments") or item.get("attachments") or []
                    
                    if pub_date and "2026" not in pub_date: continue

                    for att in attachments:
                        url = att.get("FullSizeUrl") or att.get("FullSavePath")
                        if not url: continue
                        if not url.startswith("http"): url = "https://www.idx.co.id" + url
                        
                        if db.query(InsiderTransaction).filter(InsiderTransaction.source_url == url).first(): continue
                        
                        print(f"Ingesting: {url}")
                        try:
                            # THE ONLY GUARANTEED WAY: Use browser-context fetch
                            # This avoids navigation and uses internal session cookies
                            b64_script = f"""
                            fetch("{url}").then(res => res.blob()).then(blob => new Promise((resolve, reject) => {{
                                const reader = new FileReader();
                                reader.onloadend = () => resolve(reader.result.split(',')[1]);
                                reader.onerror = reject;
                                reader.readAsDataURL(blob);
                            }}))
                            """
                            b64_pdf = page.evaluate(b64_script)
                            pdf_bytes = base64.b64decode(b64_pdf)
                            
                            # Submit parsing and processing to thread pool
                            futures.append(executor.submit(process_pdf, pdf_bytes, url, pub_date, title))
                            
                        except Exception as e:
                            print(f"  - Error fetching {url}: {e}")
                        
                        time.sleep(1) 
                
                # Wait for all background tasks to complete
                for future in concurrent.futures.as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        print(f"Thread execution error: {e}")
                    
        finally:
            browser.close()
            db.close()
    print("Scraper Finished.")

if __name__ == "__main__":
    import sys
    run_scraper(full_year="--full-year" in sys.argv)
