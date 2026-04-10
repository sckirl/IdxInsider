# 🇮🇩 IDX OpenInsider Project Progress Dashboard

**Status Date:** April 9, 2026
**Project Goal:** Build a real-time Indonesian insider trading intelligence platform (IDX OpenInsider).

---

## 📊 Component Completion Dashboard

| Component | Completion | Status | Notes |
| :--- | :---: | :---: | :--- |
| **Overall Project** | **92%** | 🟡 | Core functionality live, awaiting extraction accuracy improvements. |
| **Backend API (DEV)** | 100% | 🟢 | FastAPI, PostgreSQL, Dockerized. Endpoints working (`/latest`, `/clusters`). |
| **Frontend UI (DEV)** | 100% | 🟢 | Next.js Dashboard. Real-time feed & Cluster Buys UI fully operational. |
| **Database & Schema** | 100% | 🟢 | PostgreSQL structured with automated schema definitions. |
| **Scraping Infrastructure** | 95% | 🟢 | Async Playwright successfully bypasses Cloudflare to fetch PDFs. Multi-threaded. |
| **QA / Automated Testing** | 95% | 🟢 | Playwright UI & API tests fully passing. Fixed false-positive port issues. |
| **Data Extraction (OCR/NLP)** | 60% | 🟡 | `pdfplumber` implemented. Brittle on unstructured grids (Price extraction often fails). |

---

## 📝 Agent Handover Notes & Today's Progress (April 9, 2026)

**What was achieved today:**
1. **QA & Environment Fixes:** Fixed Playwright test configurations (Frontend mapping: 6969, Backend: 8000), resolving failing test suites. Fixed DB seeding pipeline.
2. **Data Integrity Enforcement:** Enforced strict rules against hallucinating data (added to `GEMINI.md`). Purged the database of fake future transactions (e.g., 2026-10-05 data).
3. **Scraper Concurrency & Bugs:** Multi-threaded the PDF ingestion pipeline using `ThreadPoolExecutor`. Fixed `Maximum call stack size exceeded` errors by using `FileReader` instead of JS spread syntax for extracting large PDFs in Playwright.
4. **Data Sourcing:** Successfully scraped the actual IDX disclosures for 2026.
5. **UAT "Inspect Transaction" Bug:** Fixed the issue where clicking "Inspect Transaction" for older cluster buys (BBCA, GOOD, TOWR) showed blank data by increasing the `/insider/latest` endpoint memory limit from 100 to 1000 items.
6. **OCR Refactor (`plumber` branch):** Switched to a pure `pdfplumber` (layout=True) extraction on the `plumber` branch. Verified that it parses shares accurately but completely drops the ball on extracting "Price" due to unstructured IDX table layouts breaking regex bounds.

**Known Issues & Limitations:**
- `pdfplumber` + Regex is extremely fast but highly brittle. It misses the *Price* (inserting 0.0) when the IDX PDF tables use unstructured grids or unpredictable spacing.

---

## 🎯 Next Immediate Goals for the Next Agent

**1. Implement LLM-Based Vision Extraction (Hybrid Triage Pipeline)**
- **Goal:** Replace the brittle Regex/pdfplumber parsing with a multimodal LLM API (e.g., Gemini 1.5 Flash or GPT-4o-mini via Structured Outputs).
- **Why:** Deep research confirmed OCR + Regex fails on non-standard IDX layouts. A Vision-Language Model can accurately extract Shares, Prices, and Insider Names strictly into a JSON schema by "reading" the document visually, avoiding the trap of coordinates and regex.
- **Action:** Retain `PyMuPDF`/`pdfplumber` ONLY to check if a document is a valid digital PDF. Route all complex tabular extraction to the Multimodal API.

**2. Setup Deterministic Validation Layer**
- **Goal:** Add a Pydantic validation step after LLM extraction.
- **Why:** To ensure mathematical logic (Shares * Price = Value) and that dates are strictly valid before inserting into PostgreSQL, eliminating any residual hallucination risk.

**3. Production Deployment**
- **Goal:** Finalize Docker Compose memory limits, setup a robust cron scheduler for the background scraper task, and prepare for final production server deployment.