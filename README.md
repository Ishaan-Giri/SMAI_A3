# SEBI Retail Investor Assistant — Project README

> A Retrieval-Augmented Generation (RAG) chatbot that answers retail investor questions using 23 official SEBI educational documents, powered by Google Gemini and deployed on Streamlit.

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Repository Structure](#repository-structure)
5. [Quick Start](#quick-start)
6. [Streamlit Cloud Deployment](#streamlit-cloud-deployment)
7. [Configuration](#configuration)
8. [Knowledge Base](#knowledge-base)
9. [Limitations](#limitations)

---

## Overview

The SEBI Retail Investor Assistant helps everyday Indian investors navigate SEBI regulations, rights, and processes. Every response is grounded in official SEBI-published PDFs and includes inline citations with document title, topic, and page number.

---

## Features

| Feature | Detail |
|---|---|
| **RAG Pipeline** | ChromaDB vector store + `all-MiniLM-L6-v2` embeddings + Gemini generation |
| **23 SEBI Documents** | IPOs, Mutual Funds, KYC, SCORES, REITs, InvITs, Corporate Bonds, and more |
| **Multi-model Fallback** | Tries `gemini-1.5-flash` → `gemini-2.0-flash-lite` → `gemini-2.0-flash` → `gemini-2.5-flash` |
| **Quota Resilience** | Exponential back-off on 429 errors; 404 model errors skipped silently |
| **Hindi Support** | Toggle for full Devanagari-script responses with hard language override |
| **Citation Cards** | Every answer shows source document, topic badge, page, and relevance % |
| **Chat History** | Last 3 conversation turns sent as context for follow-up questions |
| **Auto-ingestion** | `chroma_db` is built automatically on first launch if not present |
| **Dark UI** | Permanent dark navy theme (forced even if user switches Streamlit to light mode) |

---

## Architecture

```
User Query
    │
    ▼
┌─────────────────────────────┐
│   Streamlit Frontend        │  app.py
│   (chat UI + citations)     │
└────────────┬────────────────┘
             │ query + chat history
             ▼
┌─────────────────────────────┐
│   RAG Pipeline              │  rag.py
│                             │
│  1. Embed query             │◄─── all-MiniLM-L6-v2
│  2. Retrieve top-8 chunks   │◄─── ChromaDB (cosine similarity)
│  3. Build context prompt    │
│  4. Call Gemini API         │◄─── gemini-1.5-flash (with fallback)
│  5. Return answer + cites   │
└─────────────────────────────┘
             ▲
             │ indexed at startup
┌─────────────────────────────┐
│   Vector Store              │  chroma_db/
│   ChromaDB (persistent)     │  1,367 chunks from 23 PDFs
└─────────────────────────────┘
             ▲
             │ built by
┌─────────────────────────────┐
│   Ingestion Pipeline        │  ingest.py
│   PDF → pages → chunks      │
│   → embed → upsert          │
└─────────────────────────────┘
```

---

## Repository Structure

```
sebi_chatbot/
├── app.py              # Streamlit UI + session management
├── rag.py              # RAG pipeline (retrieval + generation)
├── ingest.py           # PDF ingestion pipeline
├── requirements.txt    # Python dependencies
├── .env.example        # API key template
├── .gitignore
├── .streamlit/
│   └── config.toml     # Theme + server settings
└── data/
    └── pdfs/           # 23 SEBI PDF documents (git-tracked)
```

> `chroma_db/` is **not** committed to git. It is built automatically on first run.

---

## Quick Start

### 1. Clone and install

```bash
git clone <your-repo-url>
cd sebi_chatbot
pip install -r requirements.txt
```

### 2. Set your API key

```bash
cp .env.example .env
# Edit .env and add your Google AI Studio key:
# GOOGLE_API_KEY=your_key_here
```

Get a free key at [aistudio.google.com](https://aistudio.google.com).

### 3. Build the knowledge base (first run only)

```bash
python ingest.py
```

This reads all PDFs in `data/pdfs/`, chunks them (800 chars, 150 overlap), embeds them with `all-MiniLM-L6-v2`, and stores 1,367 vectors in ChromaDB.

### 4. Run

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501).

> **Note:** On Streamlit Cloud the knowledge base is built automatically at startup if `chroma_db/` is missing — no manual ingestion needed.

---

## Streamlit Cloud Deployment

1. Push all files to a public GitHub repository (ensure `data/pdfs/` is committed; `chroma_db/` and `.env` should NOT be committed).
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your repo.
3. Set **Main file path** to `app.py`.
4. Under **Settings → Secrets**, add:
   ```toml
   GOOGLE_API_KEY = "your-key-here"
   ```
5. Deploy. The app will auto-ingest the PDFs on first boot (~1–2 min).

---

## Configuration

| Variable | Location | Default | Description |
|---|---|---|---|
| `GOOGLE_API_KEY` | `.env` / Streamlit Secrets | — | Google AI Studio API key |
| `TOP_K` | `rag.py` | `8` | Number of chunks retrieved per query |
| `CHUNK_SIZE` | `ingest.py` | `800` | Characters per text chunk |
| `CHUNK_OVERLAP` | `ingest.py` | `150` | Overlap between consecutive chunks |
| `MAX_RETRIES` | `rag.py` | `3` | Retries per model on quota errors |

---

## Knowledge Base

| # | Document | Topic |
|---|---|---|
| 1 | How to Invest in an IPO | IPO |
| 2 | Introduction to Mutual Funds | Mutual Funds |
| 3 | Mutual Funds – Dos and Don'ts | Mutual Funds |
| 4 | Investor Grievance – SEBI SCORES | SCORES / Grievance |
| 5 | KYC and Demat Account Opening | KYC |
| 6 | Securities Market Booklet | Securities Market |
| 7 | Introduction to Securities Markets | Securities Market |
| 8 | Introduction to Indian Securities Market | Securities Market |
| 9 | Financial Education Booklet | Financial Education |
| 10 | Investor Charter – Stock Exchange | Investor Rights |
| 11 | Investments by NRIs | NRI Investments |
| 12 | Corporate Actions (Dividends, Bonus, Splits) | Corporate Actions |
| 13 | Share and Debenture Holder Guide | Shares & Debentures |
| 14 | MCQs on Commodity Derivatives – Options | Derivatives |
| 15 | Financial Education – Executives Module | Financial Planning |
| 16 | How to Buy & Sell Shares | Secondary Market |
| 17 | Beginner's Guide to Capital Markets | Capital Markets |
| 18 | Introduction to REITs | REITs |
| 19 | Introduction to InvITs | InvITs |
| 20 | Primary Market – Rights Issue | Rights Issue |
| 21 | Depository Services | Depository |
| 22 | Corporate Bonds Market Guide | Corporate Bonds |
| 23 | Introduction to Primary Markets | Primary Market |

---

## Limitations

- **Free-tier quota:** The Gemini free tier allows ~200–1500 requests/day depending on model. Heavy use will exhaust quota; billing must be enabled for production use.
- **PDF text extraction:** Scanned/image-based PDFs yield no text. All 23 documents are text-extractable.
- **Ephemeral storage on Cloud:** Streamlit Cloud's filesystem resets on each boot, so `chroma_db/` is rebuilt every deployment (~1–2 min overhead).
- **No real-time data:** The knowledge base is static; SEBI regulatory updates after the PDF publication dates are not reflected.
- **Language:** Hindi support is best-effort via prompt instruction; translation quality depends on the underlying model.

---

*For educational use only. Always verify final regulatory details on [sebi.gov.in](https://www.sebi.gov.in) or [investor.sebi.gov.in](https://investor.sebi.gov.in).*
