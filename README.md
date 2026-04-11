# 🇮🇩 IDX OpenInsider: Institutional Intelligence Engine

A real-time Indonesian insider trading intelligence platform that identifies high-conviction signals from Directors and Commissioners (Direksi/Komisaris) at the Indonesia Stock Exchange (IDX).

![Project Status](https://img.shields.io/badge/Status-Institutional--Grade-blue)
![Data Recency](https://img.shields.io/badge/Data-April%202026-green)
![Intelligence](https://img.shields.io/badge/Asymmetric--Edge-Enabled-orange)

## 💎 Institutional Killer Features

### 1. Insider Accumulation Price Map
A Bloomberg-tier horizontal volume profile that plots exact price-volume clusters of insider transactions. Instantly identify the "Fundamental Floor" where the smartest money in Indonesia is accumulating shares relative to the current market price.

### 2. Supply Choke & Absorption Ratio
Calculates the **Absorption Ratio**: `(Total Insider Buys / 30-Day Average Daily Volume)`. Detects rare "Supply Choke" events where insiders absorb multiple days' worth of entire market liquidity, indicating massive conviction.

### 3. Cluster Buy Engine 🔥
Identifies high-conviction accumulation patterns where multiple unique insiders (e.g., three different Directors) buy the same ticker within a rolling window.

### 4. Stockbit "Trade" Integration
Direct deep-linking to Stockbit Insider pages for every transaction, enabling instant cross-verification and one-click trade execution.

## 🚀 Core Features

- **Real-Time Data Ingestion:** Automated scraping of IDX "Keterbukaan Informasi" using Playwright to bypass modern anti-bot protections.
- **Smart Scoring System:** Analyzes roles, transaction values, and patterns to assign 0-10+ Conviction Scores.
- **Financial Terminal UI:** Modern, dark-mode dashboard built with Next.js (16+), featuring real-time filtering and responsive design.
- **Network Agnostic:** Fully containerized with Docker for seamless access via Tailscale, Public IPs, or Private VPNs.

## 🛠 Tech Stack

- **Frontend:** Next.js 16 (TypeScript, Tailwind CSS, Recharts)
- **Backend:** FastAPI (Python 3.11), SQLAlchemy, yfinance (Liquidity Data)
- **Database:** PostgreSQL 15 (PostGIS-ready)
- **Scraper:** Playwright (Headless Chromium), pdfplumber, Tesseract OCR
- **Orchestration:** Docker Compose

## 📦 Quick Start

### 1. Prerequisites
- Docker & Docker Compose.
- Tailscale (recommended for remote access).

### 2. Launch
```bash
docker compose up -d
```
The dashboard will be available at `http://localhost:6969` (or your Server IP).

## 🧠 Agent Orchestration & Workflow

This system is built and maintained by a coordinated team of autonomous AI agents.

```mermaid
graph TD
    %% Global Styles
    classDef supervisor fill:#6a1b9a,stroke:#4a148c,color:#fff,stroke-width:4px;
    classDef pm fill:#fbc02d,stroke:#f57f17,color:#000,font-weight:bold;
    classDef ba fill:#0277bd,stroke:#01579b,color:#fff;
    classDef dev fill:#2e7d32,stroke:#1b5e20,color:#fff;
    classDef qa fill:#c62828,stroke:#b71c1c,color:#fff;
    classDef infrastructure fill:#37474f,stroke:#263238,color:#fff,stroke-dasharray: 5 5;
    classDef external fill:#4527a0,stroke:#311b92,color:#fff;

    subgraph User_Interface [Institutional Intelligence Layer]
        User((User/Owner))
        Tailscale[Tailscale / Remote Access]:::infrastructure
        ProdURL[Next.js Dashboard :6969]
        TickerDrawer[Institutional Drawer: Map/Absorption]:::pm
        Stockbit[Stockbit Verification]:::external
    end

    subgraph Control_Plane [Command & Control]
        Supervisor[Gemini CLI / Lead Architect]:::supervisor
        PM[Project Manager Agent]:::pm
    end

    subgraph Intelligence_Layer [Data & Signal Logic]
        BA[Business Analyst / Researcher]:::ba
        Scoring[Smart Scoring & Cluster Engine]
        AbsRatio[Absorption Ratio Math]:::ba
        PriceMap[Accumulation Price Map Logic]:::ba
    end

    subgraph Execution_Core [Engineering & API Delivery]
        DEV[Developer Agent]:::dev
        API[FastAPI Backend :8000]
        Scraper[Multi-threaded PDF/HTML Scraper]
        YFinance[yfinance Market Data API]:::external
        Scheduler[Randomized Scheduler 1AM-5AM]:::infrastructure
    end

    subgraph Data_Layer [Source & Storage]
        IDX_API[(IDX 2026 API / PDF)]
        DB[(PostgreSQL)]
    end

    subgraph Validation_Layer [Quality & Integrity]
        QA[QA Engineer Agent]:::qa
    end

    %% Workflow Flow
    User -->|Access via| Tailscale
    Tailscale -->|Browser| ProdURL
    ProdURL -->|Inspect Ticker| TickerDrawer
    TickerDrawer -->|Execution| Stockbit
    
    User -->|Directives| Supervisor
    Supervisor -->|Plan Mode| PM
    PM -->|Features| BA
    BA -->|Data Logic| Scoring
    BA -->|Institutional Specs| AbsRatio
    BA -->|Visual Logic| PriceMap
    
    PriceMap -->|API Schema| DEV
    AbsRatio -->|API Schema| DEV
    
    DEV -->|Implement| API
    DEV -->|Ingestion| Scraper
    
    API <-->|Fetch Price History| YFinance
    API <-->|Serve Aggregates| DB
    Scraper -->|Ingest| IDX_API
    Scraper -->|Store| DB
    
    Scheduler -->|Trigger| Scraper
    
    %% QA Loop
    QA -->|Institutional Data Tests| API
    QA -->|Visual Regression| TickerDrawer
    QA -->|Schema Integrity| DB
    QA -->|UAT Reports| Supervisor

    %% Connectivity
    ProdURL <-->|NEXT_PUBLIC_API_URL| API
```

---
*“Siapa insider di Indonesia yang sedang membeli saham secara signifikan?” — Dashboard is LIVE and cross-checked.*
