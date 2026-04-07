# Data Schema & Extraction Strategy

This document defines the data sources, schema, and extraction logic for the Indonesian Insider Trading Intelligence System.

## 1. Data Sources

### Primary Source: IDX Keterbukaan Informasi
- **URL:** [https://www.idx.co.id/id/perusahaan-tercatat/keterbukaan-informasi/](https://www.idx.co.id/id/perusahaan-tercatat/keterbukaan-informasi/)
- **Internal API:** `https://www.idx.co.id/umbraco/Surface/ListedCompany/GetAnnouncement`
- **Method:** GET
- **Parameters:**
  - `indexFrom`: Start index (0, 20, 40...)
  - `pageSize`: Number of items per request.
  - `keyword`: Use the following keywords to filter:
    - `"Laporan Kepemilikan atau Setiap Perubahan Kepemilikan Saham Perusahaan Terbuka"` (Primary)
    - `"Keterbukaan Informasi Pemegang Saham Tertentu"`
    - `"Laporan Bulanan Registrasi Pemegang Efek"` (For aggregate data)

### Format
- **List Data:** JSON via API.
- **Detailed Data:** PDF (Links provided in the `FullSizeUrl` field of the API response).
- **Format Note:** Some PDFs are text-based, while others are scans (requiring OCR).

---

## 2. Data Schema (Normalized)

| Field | Type | Description |
| :--- | :--- | :--- |
| `ticker` | String | 4-letter stock code (e.g., "BBCA"). |
| `issuer_name` | String | Full name of the company. |
| `insider_name` | String | Name of the person or entity performing the transaction. |
| `role` | String | Position (e.g., "Direktur", "Komisaris", "Pemegang Saham Pengendali"). |
| `transaction_type` | Enum | `BUY`, `SELL`, `GIFT`, `EXERCISE`, `INHERITANCE`, `OTHERS`. |
| `shares` | Number | Number of shares transacted. |
| `price` | Number | Price per share in IDR. |
| `value` | Number | Total transaction value (`shares * price`). |
| `date` | Date | Actual transaction date (not filing date). |
| `filing_date` | Date | Date the disclosure was published on IDX. |
| `ownership_before` | Number | Number of shares held before the transaction. |
| `ownership_after` | Number | Number of shares held after the transaction. |
| `ownership_change_pct` | Number | Percentage change in ownership. |
| `direct_ownership` | Boolean | `true` if Direct, `false` if Indirect. |
| `purpose` | String | Reason for transaction (e.g., "Investasi", "Divestasi"). |
| `source_url` | String | Link to the original PDF disclosure. |

---

## 3. Normalization Rules (Indonesian to English)

The system must map inconsistent Indonesian terms to normalized values:

### Transaction Type Mapping
- `Pembelian`, `Beli`, `Penambahan` -> **BUY**
- `Penjualan`, `Jual`, `Pelepasan`, `Pengurangan` -> **SELL**
- `Hibah` -> **GIFT**
- `Waris` -> **INHERITANCE**
- `Pelaksanaan MESOP`, `Exercise` -> **EXERCISE**

### Role Mapping
- `Direktur`, `Direksi`, `Presiden Direktur`, `CEO` -> **DIREKTUR**
- `Komisaris`, `Presiden Komisaris`, `Komisaris Independen` -> **KOMISARIS**
- `Pemegang Saham Utama`, `Pengendali` -> **MAJOR_SHAREHOLDER**

---

## 4. Smart Scoring System (Proxy Signals)

To help users identify high-conviction trades, each transaction is assigned a **Score**:

| Signal | Score Adjustment |
| :--- | :--- |
| **Role: Direktur** BUY | +3 |
| **Role: Komisaris** BUY | +2 |
| **Role: Major Shareholder** BUY | +1 |
| **Transaction Value > 1B IDR** | +2 |
| **Transaction Value > 10B IDR** | +4 |
| **Multiple Insiders buying same ticker (7 days)** | +3 |
| **Ownership increase > 10%** | +2 |
| **Direct Ownership (instead of Indirect)** | +1 |

---

## 5. Extraction Strategy (PDF Parsing)

1. **Step 1: Ingestion**
   - Poll the IDX API every 15-30 minutes.
   - Filter for relevant keywords.
2. **Step 2: PDF Processing**
   - Download the PDF from `FullSizeUrl`.
   - Use `pdfplumber` for text-based PDFs.
   - Use `Tesseract OCR` or `AWS Textract` for scanned PDFs.
3. **Step 3: Pattern Matching**
   - Use RegEx to find Ticker, Name, and Role.
   - Look for table structures to extract transaction rows (Date, Shares, Price).
4. **Step 4: Deduplication**
   - Use (Ticker, Insider, Date, Shares) as a unique key to prevent duplicate entries from multiple filings.
