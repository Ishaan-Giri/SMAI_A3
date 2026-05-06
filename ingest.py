"""
ingest.py - SEBI PDF Ingestion Pipeline

Downloads SEBI PDFs, chunks them, embeds them with sentence-transformers,
and stores in a persistent ChromaDB vector store.
"""

import os
import sys
import json
import hashlib
import chromadb
from pathlib import Path
from pypdf import PdfReader
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
PDF_DIR    = BASE_DIR / "data" / "pdfs"
CHROMA_DIR = BASE_DIR / "chroma_db"

COLLECTION_NAME = "sebi_docs"

# ── PDF metadata ───────────────────────────────────────────────────────────────
# Keys are the exact filenames present in data/pdfs/
PDF_METADATA = {
    # Core investor basics
    "ipo_guide.pdf": {
        "title": "How to Invest in an IPO (Initial Public Offering)",
        "topic": "IPO",
        "source_url": "https://investor.sebi.gov.in/pdf/reference-material/ppt/PPT-3%20How%20to%20invest%20in%20Intial%20Public%20Offer%20Updated%2030%20Sep%202022.pdf",
    },
    "mutual_funds_intro.pdf": {
        "title": "Introduction to Mutual Funds Investing",
        "topic": "Mutual Funds",
        "source_url": "https://investor.sebi.gov.in/pdf/reference-material/ppt/PPT-8-Introduction_to_Mutual_Funds_Investing_Jan24.pdf",
    },
    "scores_grievance.pdf": {
        "title": "Investor Grievance Redressal – SEBI SCORES",
        "topic": "SCORES / Grievance",
        "source_url": "https://investor.sebi.gov.in/pdf/reference-material/ppt/PPT-9%20Investor%20Grievance%20Redressal%20Mechanism-SEBI%20Scores,%20NSE,BSE,%20NSDL,%20CDSL%2030%20Sep%202022.pdf",
    },
    "securities_market_booklet.pdf": {
        "title": "Securities Market Booklet",
        "topic": "Securities Market",
        "source_url": "https://investor.sebi.gov.in/pdf/reference-material/languages/english/SM%20Booklet_English%20-%20Final%20(Low).pdf",
    },
    "Financial Education Booklet - English.pdf": {
        "title": "Financial Education Booklet",
        "topic": "Financial Education",
        "source_url": "https://investor.sebi.gov.in/pdf/downloadable-documents/Financial%20Education%20Booklet%20-%20English.pdf",
    },
    "mutual_funds_dos_donts.pdf": {
        "title": "Mutual Funds – Dos and Don'ts",
        "topic": "Mutual Funds",
        "source_url": "https://investor.sebi.gov.in/pdf/reference-material/MFunds.pdf",
    },
    "intro_securities_markets.pdf": {
        "title": "Introduction to Securities Markets",
        "topic": "Securities Market",
        "source_url": "https://investor.sebi.gov.in/pdf/reference-material/ppt/PPT-1%20Introduction%20to%20Securities%20Markets%20Updated%2030%20Sep2022.pdf",
    },
    "investor_charter_stock_exchange.pdf": {
        "title": "Investor Charter for Stock Exchange",
        "topic": "Investor Rights / Charter",
        "source_url": "https://investor.sebi.gov.in/pdf/Investor%20charter%20for%20Stock%20Exchange.pdf",
    },
    "FAQ_on_kyc_norms.pdf": {
        "title": "KYC and Demat Account Opening Guide",
        "topic": "KYC / Account Opening",
        "source_url": "https://investor.sebi.gov.in/pdf/reference-material/ppt/PPT-2%20KYC%20and%20Account%20Opening%20Updated%2030%20Sep%202022.pdf",
    },
    "nri_investments.pdf": {
        "title": "Investments by Non-Resident Indians (NRIs)",
        "topic": "NRI Investments",
        "source_url": "https://investor.sebi.gov.in/pdf/reference-material/ppt/PPT-14-Investments_by_NRIs-English.pdf",
    },
    # Corporate actions & financial deep dive
    "PPT-5 Corporate Actions - Dividends, Bonus, Splits, etc_.pdf": {
        "title": "Corporate Actions – Dividends, Bonus, Splits",
        "topic": "Corporate Actions",
        "source_url": "https://investor.sebi.gov.in/pdf/reference-material/ppt/PPT-5%20Corporate%20Actions%20-%20Dividends,%20Bonus,%20Splits,%20etc_.pdf",
    },
    "sharedebentureholder.pdf": {
        "title": "Beginner's Guide – Share and Debenture Holders",
        "topic": "Shares and Debentures",
        "source_url": "https://investor.sebi.gov.in/pdf/reference-material/sharedebentureholder.pdf",
    },
    "MCQ on Commodity Derivatives - English-Options.pdf": {
        "title": "MCQs on Commodity Derivatives – Options",
        "topic": "Derivatives / Options",
        "source_url": "https://investor.sebi.gov.in/pdf/reference-material/MCQs%20on%20Commodity%20Derivatives%20-%20CDMRD/MCQ%20on%20English/MCQ%20on%20Commodity%20Derivatives%20-%20English-Options.pdf",
    },
    "PPT-21-ISM.pdf": {
        "title": "Introduction to Indian Securities Market (Detailed)",
        "topic": "Securities Market Overview",
        "source_url": "https://investor.sebi.gov.in/pdf/reference-material/ppt/PPT-21-ISM.pdf",
    },
    "executivesmodule.pdf": {
        "title": "Financial Education – Executives Module",
        "topic": "Financial Planning & Fraud Prevention",
        "source_url": "https://investor.sebi.gov.in/pdf/reference-material/executivesmodule.pdf",
    },
    # Secondary market & trading
    "PPT-6 How to buy and sell shares in Stock Exchanges.pdf": {
        "title": "Secondary Market – How to Buy & Sell Shares",
        "topic": "Secondary Market / Trading",
        "source_url": "https://investor.sebi.gov.in/pdf/reference-material/ppt/PPT-6%20How%20to%20buy%20and%20sell%20shares%20in%20Stock%20Exchanges.pdf",
    },
    "beginners.pdf": {
        "title": "Beginner's Guide to the Capital Markets",
        "topic": "Capital Markets Overview",
        "source_url": "https://investor.sebi.gov.in/pdf/reference-material/beginners.pdf",
    },
    # Advanced assets & infrastructure
    "PPT-10 Updated PPT on REITs_approved 30 Sep 2022.pdf": {
        "title": "Introduction to Real Estate Investment Trusts (REITs)",
        "topic": "REITs",
        "source_url": "https://investor.sebi.gov.in/pdf/reference-material/ppt/PPT-10%20Updated%20PPT%20on%20REITs_approved%2030%20Sep%202022.pdf",
    },
    "PPT-11 Updated PPT on InvITs _approved 30 Sep 2022.pdf": {
        "title": "Introduction to Infrastructure Investment Trusts (InvITs)",
        "topic": "InvITs / Infrastructure",
        "source_url": "https://investor.sebi.gov.in/pdf/reference-material/ppt/PPT-11%20Updated%20PPT%20on%20InvITs%20_approved%2030%20Sep%202022.pdf",
    },
    "PPT-4 How to Invest in Rights Issue.pdf": {
        "title": "Primary Market – Rights Issue",
        "topic": "Rights Issue",
        "source_url": "https://investor.sebi.gov.in/pdf/reference-material/ppt/PPT-4%20How%20to%20Invest%20in%20Rights%20Issue.pdf",
    },
    "PPT-7 Depository Services updated 30 Sep 2022.pdf": {
        "title": "Depository Services",
        "topic": "Depository / Demat Operations",
        "source_url": "https://investor.sebi.gov.in/pdf/reference-material/ppt/PPT-7%20Depository%20Services%20updated%2030%20Sep%202022.pdf",
    },
    "corporatebonds.pdf": {
        "title": "Investor Guide for Corporate Bonds Market",
        "topic": "Corporate Bonds / Debt",
        "source_url": "https://investor.sebi.gov.in/pdf/reference-material/corporatebonds.pdf",
    },
    "primarymarkets.pdf": {
        "title": "Introduction to Primary Markets",
        "topic": "Primary Market / Public Issues",
        "source_url": "https://investor.sebi.gov.in/pdf/reference-material/primarymarkets.pdf",
    },
}

# ── Chunking config ─────────────────────────────────────────────────────────────
CHUNK_SIZE    = 800
CHUNK_OVERLAP = 150


def extract_text_from_pdf(pdf_path: Path) -> list[dict]:
    """Extract text page-by-page from a PDF file."""
    pages = []
    try:
        reader = PdfReader(str(pdf_path))
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = text.strip()
            if len(text) > 50:   # skip near-empty pages
                pages.append({"page": page_num, "text": text})
    except Exception as e:
        print(f"  ⚠  Could not read {pdf_path.name}: {e}")
    return pages


def chunk_pages(pages: list[dict], pdf_name: str, meta: dict) -> list[dict]:
    """Split page texts into overlapping chunks with metadata."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = []
    for page_info in pages:
        sub_chunks = splitter.split_text(page_info["text"])
        for idx, chunk_text in enumerate(sub_chunks):
            chunk_id = hashlib.md5(
                f"{pdf_name}|{page_info['page']}|{idx}|{chunk_text[:40]}".encode()
            ).hexdigest()
            chunks.append({
                "id": chunk_id,
                "text": chunk_text,
                "metadata": {
                    "source_pdf": pdf_name,
                    "title": meta["title"],
                    "topic": meta["topic"],
                    "page": page_info["page"],
                    "source_url": meta["source_url"],
                },
            })
    return chunks


def ingest():
    """Main ingestion pipeline."""
    # ── Embedding function ──────────────────────────────────────────────────────
    print("🔧  Loading sentence-transformer embeddings (all-MiniLM-L6-v2)…")
    embed_fn = SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    # ── ChromaDB ────────────────────────────────────────────────────────────────
    print(f"📂  Opening ChromaDB at: {CHROMA_DIR}")
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # Delete & recreate collection for a clean ingest
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"   ↪  Dropped existing collection '{COLLECTION_NAME}'")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"},
    )

    # ── Process PDFs ─────────────────────────────────────────────────────────────
    pdf_files = sorted(PDF_DIR.glob("*.pdf"))
    if not pdf_files:
        print("❌  No PDFs found in data/pdfs/. Run the download step first.")
        sys.exit(1)

    total_chunks = 0
    for pdf_path in pdf_files:
        pdf_name = pdf_path.name
        meta = PDF_METADATA.get(pdf_name, {
            "title": pdf_name.replace("_", " ").replace(".pdf", "").title(),
            "topic": "General",
            "source_url": "",
        })
        print(f"\n📄  Processing: {meta['title']}")

        pages = extract_text_from_pdf(pdf_path)
        print(f"   → {len(pages)} pages with text")

        if not pages:
            print(f"   ⚠  Skipping (no extractable text)")
            continue

        chunks = chunk_pages(pages, pdf_name, meta)
        print(f"   → {len(chunks)} chunks")

        # Upsert in batches of 100
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            collection.upsert(
                ids=[c["id"] for c in batch],
                documents=[c["text"] for c in batch],
                metadatas=[c["metadata"] for c in batch],
            )

        total_chunks += len(chunks)

    print(f"\n✅  Ingestion complete! Total chunks stored: {total_chunks}")
    print(f"   Collection: '{COLLECTION_NAME}' in {CHROMA_DIR}")


if __name__ == "__main__":
    ingest()
