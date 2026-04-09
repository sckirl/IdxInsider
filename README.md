# 🇮🇩 IDX OpenInsider Intelligence System

A real-time Indonesian insider trading intelligence platform that tracks and analyzes transactions of Directors and Commissioners from the Indonesia Stock Exchange (IDX).

![Project Status](https://img.shields.io/badge/Status-Production--Ready-green)
![Data Recency](https://img.shields.io/badge/Data-April%202026-blue)

## 🚀 Key Features

- **Real-Time Data Ingestion:** Automated scraping of IDX "Keterbukaan Informasi" using Playwright to bypass modern anti-bot protections.
- **Cluster Buy Engine 🔥:** Detects high-conviction accumulation signals where multiple unique insiders buy the same ticker within a configurable rolling window.
- **Smart Scoring System:** Analyzes roles (Direksi vs Komisaris), transaction values, and patterns to assign Conviction Scores.
- **Financial Terminal UI:** Modern, dark-mode dashboard built with Next.js, featuring real-time filtering and responsive design.
- **Network Agnostic:** Fully containerized with Docker and abstracted via environment variables for easy access over Tailscale, VPNs, or Public IPs.

## 🛠 Tech Stack

- **Frontend:** Next.js 15 (TypeScript, Tailwind CSS)
- **Backend:** FastAPI (Python 3.11)
- **Database:** PostgreSQL 15
- **Scraper:** Playwright (Headless Chromium), pdfplumber, Tesseract OCR
- **Orchestration:** Docker Compose

## 📦 Quick Start

### 1. Prerequisites
- Docker & Docker Compose installed.
- Tailscale (recommended) or a stable IP/Hostname.

### 2. Configuration
Create a `.env` file in the root directory:
```env
# Server Hostname/IP
SERVER_IP=pukat-master

# Backend Configuration
BACKEND_PORT=8000
API_BASE_URL=http://pukat-master:8000

# Frontend Configuration
FRONTEND_PORT=6969

# Database
DATABASE_URL=postgresql://user:password@db:5432/openinsider
```

### 3. Launch
```bash
docker compose up -d
```
The dashboard will be available at `http://pukat-master:6969`.

## 🧠 Agent Orchestration

This system is built and maintained by a coordinated team of autonomous AI agents. You can view the full communication dynamic and workflow in the [Agent Orchestration Diagram](./docs/AGENT_ORCHESTRATION.mermaid).

## ⚠️ Security Notice
- `.env` files and database volumes are ignored by Git. 
- Ensure your `SERVER_IP` is correctly set to allow CORS communication between your browser and the API.

---
*“Siapa insider di Indonesia yang sedang membeli saham secara signifikan?”*
