# IDX OpenInsider ROADMAP (Updated April 2026)

## Milestone 1: Data Ingestion & Recency (BA/DEV)
- [x] Research IDX Keterbukaan Informasi URLs (BA)
- [x] Implement PDF/HTML scraper for "Laporan Kepemilikan Saham" (DEV)
- [ ] **Data Recency Upgrade:** Target April 2026 filings specifically (BA/DEV)
- [ ] Clean and normalize messy Indonesian disclosure text (DEV)
- [x] Store extracted data in PostgreSQL (DEV)

## Milestone 2: Intelligence & Logic (BA/DEV)
- [x] Build FastAPI endpoints: `/insider/latest`, `/insider/top-buy` (DEV)
- [x] Implement Smart Scoring logic (BA/DEV)
- [ ] **Cluster Buy Detection:** Logic for 2+ insiders in 7 days (BA/DEV)
- [ ] API documentation (Swagger) (DEV)

## Milestone 3: Web Layer & Terminal UI (DEV)
- [x] Scaffold Next.js project with TailwindCSS (DEV)
- [x] Implement real-time table for insider transactions (DEV)
- [x] Dark-mode financial terminal UI (DEV)
- [ ] **Advanced Interactivity:** Search, Filters, and Real-time polling (DEV)

## Milestone 4: Rigorous QA & Certifications (QA)
- [ ] **Certification A: Unit Testing** (Scraper patterns, Scoring math)
- [ ] **Certification B: Integration Testing** (Backend-DB, Frontend-API)
- [ ] **Certification C: Data Recency Testing** (Verification of April 2026 data)
- [ ] **Certification D: System & Load Testing**
- [ ] **Certification E: User Acceptance Testing (UAT)**

## Milestone 5: Final Delivery
- [ ] PM Approval of all QA Certifications
- [ ] Production-ready Docker orchestration
- [ ] Deployment to pukat-master:6969
