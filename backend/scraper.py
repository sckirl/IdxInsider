import requests
import json
import time
import io
import re
import base64
import os
import concurrent.futures
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from playwright.sync_api import sync_playwright
import pdfplumber

from .database import SessionLocal, engine
from .models import InsiderTransaction, Base
from .utils import normalize_role, calculate_score, get_market_metadata, get_price_on_date

# Ensure DB tables are created
Base.metadata.create_all(bind=engine)

# Final correct IDX API URL
IDX_API_URL = "https://www.idx.co.id/primary/Announcement/GetAnnouncementList"
KEYWORDS = [
    "Laporan Kepemilikan",
    "Informasi Hasil Pelaksanaan Pembelian Kembali Saham"
]

# Cache for company-specific formatting
COMPANY_FORMATS_FILE = "backend/company_formats.json"

def load_company_formats() -> Dict[str, Any]:
    try:
        if os.path.exists(COMPANY_FORMATS_FILE):
            with open(COMPANY_FORMATS_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading company formats: {e}")
    return {}

def save_company_formats(formats: Dict[str, Any]):
    try:
        with open(COMPANY_FORMATS_FILE, "w") as f:
            json.dump(formats, f, indent=4)
    except Exception as e:
        print(f"Error saving company formats: {e}")

def extract_transaction_date(text: str) -> Optional[datetime.date]:
    """
    Extracts transaction date using common Indonesian and English patterns.
    """
    # Clean text for better matching
    text = text.replace("\n", " ")
    
    date_patterns = [
        # Indonesian: Tanggal Transaksi: Senin, 06 April 2026
        r"(?:Tanggal Transaksi|Date of Transaction)\s*[:]?\s*(?:[A-Za-z]+,?\s*)?(\d{1,2}[\/\-\.\s](?:Jan(?:uari)?|Feb(?:ruari)?|Mar(?:et)?|Apr(?:il)?|Mei|Jun(?:i)?|Jul(?:i)?|Agu(?:stus)?|Sep(?:tember)?|Okt(?:ober)?|Nov(?:ember)?|Des(?:ember)?)\s*\d{4})",
        # Slash format: 06/04/2026
        r"(?:Tanggal Transaksi|Date of Transaction)\s*[:]?\s*(?:[A-Za-z]+,?\s*)?(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
        # English: April 10, 2026
        r"(\d{1,2}[\/\-\.\s](?:January|February|March|April|May|June|July|August|September|October|November|December)\s*\d{4})",
        r"([A-Z]{3,10}\s+\d{1,2},\s+\d{4})"
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text, re.I)
        if match:
            date_str = match.group(1).strip()
            try:
                date_str = date_str.replace("Januari", "January").replace("Februari", "February").replace("Maret", "March")
                date_str = date_str.replace("Mei", "May").replace("Juni", "June").replace("Juli", "July")
                date_str = date_str.replace("Agustus", "August").replace("Oktober", "October").replace("Desember", "December")
                
                for fmt in ["%d %B %Y", "%d/%m/%Y", "%d-%m-%Y", "%B %d, %Y", "%d %b %Y"]:
                    try:
                        return datetime.strptime(date_str, fmt).date()
                    except: continue
            except: pass
    return None

def parse_pdf_content(pdf_bytes: bytes, source_url: str, filing_date_str: str) -> List[Dict[str, Any]]:
    """
    ULTRA-FLEXIBLE PARSER: Specifically tuned for IDX PDF patterns.
    Handles various Indonesian reporting styles and fallbacks.
    """
    transactions = []
    company_formats = load_company_formats()
    
    try:
        full_text = ""
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                full_text += page.extract_text(layout=True) or ""
        
        if not full_text.strip(): return []

        # Ticker Extraction
        ticker = "UNKNOWN"
        m_ticker = re.search(r"(?:Nama Perusahaan Tbk|Issuer|Kode Emiten|Kode Saham)\s*[:]?\s*([A-Z]{4})", full_text, re.I)
        if m_ticker: 
            ticker = m_ticker.group(1).upper().strip()
        else:
            m5 = re.search(r"\(([A-Z]{4})\)", full_text)
            if m5: ticker = m5.group(1).upper().strip()

        if ticker == "UNKNOWN" or len(ticker) != 4:
            return []

        # Transaction Date
        t_date = extract_transaction_date(full_text)
        filing_date = datetime.now().date()
        if filing_date_str:
            try:
                filing_date = datetime.strptime(filing_date_str.split("T")[0], "%Y-%m-%d").date()
            except: pass
        
        final_date = t_date if t_date else filing_date

        # Insider Name & Role
        insider_name = "Unknown"
        m_name = re.search(r"(?:Nama \(sesuai SID\)|Name \(SID\)|Nama)\s*[:]?\s*([^\n]+)", full_text, re.I)
        if m_name: insider_name = m_name.group(1).strip()

        role = ""
        if re.search(r"Anggota Direksi/Dewan Komisaris\s*:\s*Ya", full_text, re.I):
            role = "DIREKTUR"

        # Shares & Price (NLP/Pattern matching)
        shares = 0
        price = 0
        total_value = 0
        
        # Pattern 1: Nilai Transaksi Total (Common in KSEI reports)
        m_total = re.search(r"(?:Total Nilai Transaksi|Transaction Value)\s*[:]?\s*Rp?\s*([\d\.,]+)", full_text, re.I)
        if m_total:
            try:
                total_value = float(m_total.group(1).replace(".", "").replace(",", "."))
            except: pass

        # Pattern 2: Jumlah Saham Sebelum/Sesudah
        before_match = re.search(r"Jumlah Saham Sebelum Transaksi[^\d]*([\d\.,]+)", full_text, re.I)
        after_match = re.search(r"Jumlah Saham Setelah Transaksi[^\d]*([\d\.,]+)", full_text, re.I)
        if before_match and after_match:
            try:
                b_str = before_match.group(1).replace(".", "").replace(",", ".")
                a_str = after_match.group(1).replace(".", "").replace(",", ".")
                shares = abs(float(b_str) - float(a_str))
            except: pass

        if price == 0 and shares > 0:
            # Pattern 3: Price after shares
            shares_str1 = f"{shares:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            shares_str2 = f"{int(shares):,}".replace(",", ".")
            p_pattern = f"(?:{re.escape(shares_str1)}|{re.escape(shares_str2)})\\s+([\\d\\.,]+)"
            m_price = re.search(p_pattern, full_text)
            if m_price:
                try:
                    price = float(m_price.group(1).replace(".", "").replace(",", "."))
                except: pass

        if price == 0 and shares > 0:
            # Pattern 4: "Harga" followed by price
            m_price2 = re.search(r"Harga\s*[:]?\s*Rp?\s*([\d\.,]+)", full_text, re.I)
            if m_price2:
                try:
                    price = float(m_price2.group(1).replace(".", "").replace(",", "."))
                except: pass

        if price == 0 and shares > 0 and total_value > 0:
            price = total_value / shares

        if shares == 0:
            # Pattern 5: Broad search for large numbers
            clean_text = full_text.replace("Rp", "").replace(".", "").replace(",", ".")
            # Extract all numbers and sort by size
            all_nums = [float(n) for n in re.findall(r"\b\d+\.\d+\b|\b\d+\b", clean_text)]
            all_nums = [n for n in all_nums if n > 1] # Remove small values
            if all_nums:
                # Usually shares is the largest number, price is mid-size
                shares = max(all_nums)
                # Filter for common stock prices (1 - 500,000)
                potential_prices = [n for n in all_nums if 50 <= n <= 500000 and n != shares]
                if potential_prices: price = potential_prices[-1]

        # Fallback to Stock API if price is 0 or looks unrealistic
        api_price = get_price_on_date(ticker, final_date)
        
        # Sanity Check Logic:
        # 1. If doc price is 0, use API.
        # 2. If doc price is 'off by a lot' (>20% difference from API), use API.
        # 3. If total value is suspiciously low (< 1,000,000 IDR), use API to re-calculate.
        
        # Billionaire Sanity Check & Value Cap
        # No single insider buy in IDX history is likely to exceed 100 Trillion IDR.
        VALUE_CAP = 100_000_000_000_000 # 100 Trillion IDR

        use_api_price = False
        if price == 0:
            use_api_price = True
        elif api_price > 0:
            diff_pct = abs(price - api_price) / api_price
            if diff_pct > 0.20: # 20% threshold
                use_api_price = True
        
        if use_api_price and api_price > 0:
            price = api_price
            total_value = shares * price
        
        if total_value == 0:
            total_value = shares * price

        # Final Rejection Cap
        if total_value > VALUE_CAP:
            print(f"CRITICAL: Value for {ticker} (IDR {total_value}) exceeds sanity cap. Rejecting as artifact.")
            return []

        # Record company format if we found something new or it's different
        if shares > 0 and total_value < VALUE_CAP:
             current_fmt = {
                 "last_updated": datetime.now().strftime("%Y-%m-%d"),
                 "shares": shares,
                 "price": price,
                 "date_found": t_date is not None,
                 "total_value_found": total_value > 0
             }
             if ticker not in company_formats:
                company_formats[ticker] = current_fmt
                save_company_formats(company_formats)

        t_type = "SELL" if any(x in full_text.lower() for x in ["jual", "sales", "pengurangan", "pelepasan"]) else "BUY"

        transactions.append({
            "ticker": ticker,
            "issuer_name": "",
            "insider_name": insider_name,
            "role": role, 
            "transaction_type": t_type,
            "shares": float(shares),
            "price": float(price),
            "value": float(total_value),
            "date": final_date,
            "filing_date": filing_date,
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
                        date_from = (datetime.now() - timedelta(days=3)).strftime("%Y%m%d")
                        date_to = "20261231"
                        page_size = 50
                    
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

            print(f"Total Disclosures Found: {len(all_items)}")

            # Sort by published date descending
            def get_date(x):
                d = x.get("PublishedDate") or x.get("pengumuman", {}).get("TglPengumuman") or ""
                return d

            all_items.sort(key=get_date, reverse=True)
            
            futures = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                for item in all_items:
                    pub_date = item.get("PublishedDate") or item.get("pengumuman", {}).get("TglPengumuman")
                    title = item.get("Title") or item.get("pengumuman", {}).get("JudulPengumuman")
                    attachments = item.get("Attachments") or item.get("attachments") or []
                    
                    for att in attachments:
                        url = att.get("FullSizeUrl") or att.get("FullSavePath")
                        if not url: continue
                        if not url.startswith("http"): url = "https://www.idx.co.id" + url
                        
                        if db.query(InsiderTransaction).filter(InsiderTransaction.source_url == url).first(): continue
                        
                        print(f"Ingesting: {url}")
                        try:
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
                            
                            futures.append(executor.submit(process_pdf, pdf_bytes, url, pub_date, title))
                        except Exception as e:
                            print(f"  - Error fetching {url}: {e}")
                        
                        time.sleep(0.5) 
                
                for future in concurrent.futures.as_completed(futures):
                    future.result()
                    
        finally:
            browser.close()
            db.close()
    print("Scraper Finished.")

if __name__ == "__main__":
    import sys
    run_scraper(full_year="--full-year" in sys.argv)
