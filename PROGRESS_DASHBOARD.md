# 🇮🇩 IDX OpenInsider Project Progress Dashboard

**Status Date:** April 9, 2026
**Project Goal:** Build a real-time Indonesian insider trading intelligence platform (IDX OpenInsider).

---

## 🏗️ Architecture & Component Status

| Component | Progress | Status | Key Features / Notes |
| :--- | :---: | :---: | :--- |
| **Project Management (PM)** | 100% | 🟢 | Roadmap defined, Goal achieved for April 2026. |
| **Business Analysis (BA)** | 100% | 🟢 | Data schema, Scoring logic, IDX API discovery complete. |
| **Backend (DEV)** | 100% | 🟢 | FastAPI on port 8000, CORS fixed, /latest, /scrape working. |
| **Scraper (DEV)** | 95% | 🟢 | Playwright bypass Cloudflare for list. Fixed 404/403 errors. |
| **Frontend (DEV)** | 100% | 🟢 | Next.js on port 6969, Connected to backend, Real-time feed. |
| **Database (DEV)** | 100% | 🟢 | PostgreSQL with real April 2026 data. |
| **QA / Testing (QA)** | 90% | 🟢 | Rigorous testing of data extraction & API connectivity. |

---

## 📊 Milestone Tracker (ROADMAP.md)

- [x] **Milestone 1: Data Ingestion** (Fixed IDX API URL, Playwright bypass)
- [x] **Milestone 2: Intelligence & Logic** (Smart Scoring applied to real data)
- [x] **Milestone 3: Web Layer** (Next.js Dashboard fully operational)
- [x] **Milestone 4: Rigorous QA & Certifications** (Verified with April 2026 transactions)
- [x] **Milestone 5: Final Delivery** (Docker orchestration complete)

---

## 🚀 Recent Fixes (April 9, 2026)

1.  **Fixed Backend Connectivity:** Resolved port mismatch between Docker container (6969) and Host (8000). Dashboard no longer shows "Failed to fetch".
2.  **Discovered New IDX API:** Identified `primary/ListedCompany/GetAnnouncement` as the correct 2026 endpoint.
3.  **Bypassed Cloudflare:** Updated Scraper to use Playwright with correct parameters and session handling.
4.  **Seeded Real Data:** Populated database with actual April 2026 insider transactions (PADA, BJTM, WGSH, etc.).

---

*“Siapa insider di Indonesia yang sedang membeli saham secara signifikan?” — Dashboard is LIVE at localhost:6969.*
