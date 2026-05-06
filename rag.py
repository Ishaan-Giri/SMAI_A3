"""
rag.py - RAG Pipeline for SEBI Investor Assistant

Handles: query embedding → ChromaDB retrieval → Gemini answer generation
"""

import os
import time
import chromadb
from pathlib import Path
from dotenv import load_dotenv
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from google import genai
from google.genai import types as genai_types

load_dotenv()

BASE_DIR        = Path(__file__).parent
CHROMA_DIR      = BASE_DIR / "chroma_db"
COLLECTION_NAME = "sebi_docs"
TOP_K           = 8   # number of chunks to retrieve

# ── System prompt ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are a helpful SEBI (Securities and Exchange Board of India) "
    "Retail Investor Assistant. Your role is to help everyday Indian retail investors "
    "understand SEBI regulations, processes, and their rights.\n\n"
    "Rules:\n"
    "1. Answer using ALL provided context excerpts from official SEBI documents.\n"
    "2. The context may include table-of-contents pages alongside actual content pages. "
    "   Always look across ALL excerpts and synthesize a complete answer from the content pages.\n"
    "3. Never say a topic is 'covered separately' or 'not in the excerpts' if any excerpt "
    "   contains relevant information — even partial. Synthesize what is available.\n"
    "4. Only say information is unavailable if NONE of the excerpts contain any relevant detail.\n"
    "5. Be concise but complete. Use numbered steps or bullet points where appropriate.\n"
    "6. Always mention which document your answer is from.\n"
    "7. Do not make up information or speculate beyond the documents.\n"
    "8. Be friendly, clear, and accessible to a non-expert Indian investor."
)

HINDI_SUFFIX   = "\n\nIMPORTANT: You MUST respond entirely in Hindi (Devanagari script). Do not use English."
ENGLISH_SUFFIX = "\n\nIMPORTANT: You MUST respond entirely in English, regardless of any previous messages."


class SEBIAssistant:
    """RAG pipeline for SEBI investor queries."""

    def __init__(self):
        self._collection = None
        self._embed_fn   = None
        self._model      = None

    def _load(self):
        """Lazy-load embeddings, ChromaDB, and Gemini."""
        if self._collection is not None:
            return

        # Embeddings
        try:
            self._embed_fn = SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        except Exception as e:
            raise RuntimeError(
                "Could not load embedding model `all-MiniLM-L6-v2`. "
                "Ensure internet access at least once to download it from Hugging Face, "
                "or pre-cache the model locally."
            ) from e

        # ChromaDB
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        try:
            self._collection = client.get_collection(
                name=COLLECTION_NAME,
                embedding_function=self._embed_fn,
            )
        except Exception as e:
            raise ValueError(
                "Knowledge base collection 'sebi_docs' not found in chroma_db. "
                "Please run `python ingest.py` from the `sebi_chatbot/` folder first."
            ) from e

        # Gemini (new google-genai SDK)
        api_key = os.getenv("GOOGLE_API_KEY", "")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY not set. Please add it to your .env file.\n"
                "Get a free key at https://aistudio.google.com"
            )
        self._genai_client = genai.Client(api_key=api_key)
        # Model fallback: ordered by free-tier daily quota (highest first)
        # gemini-1.5-flash     : ~1500 req/day free
        # gemini-2.0-flash-lite: ~200  req/day free
        # gemini-2.0-flash     : ~200  req/day free
        # gemini-2.5-flash     : ~20   req/day free
        self._model_candidates = [
            "gemini-1.5-flash",
            "gemini-2.0-flash-lite",
            "gemini-2.0-flash",
            "gemini-2.5-flash",
        ]

    def retrieve(self, query: str, top_k: int = TOP_K) -> list[dict]:
        """Retrieve the top-K relevant chunks from ChromaDB."""
        self._load()
        results = self._collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        chunks = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            # Chroma returns cosine distance (smaller is better). Convert to a
            # bounded similarity-style score for UI display.
            distance = float(dist) if dist is not None else 1.0
            score = max(0.0, min(1.0, 1.0 - distance))
            chunks.append({
                "text":       doc,
                "title":      meta.get("title", "Unknown"),
                "topic":      meta.get("topic", ""),
                "page":       meta.get("page", "?"),
                "source_pdf": meta.get("source_pdf", ""),
                "source_url": meta.get("source_url", ""),
                "score":      round(score, 3),
            })
        return chunks

    def build_context(self, chunks: list[dict]) -> str:
        """Format retrieved chunks into a context block for the LLM."""
        parts = []
        for i, c in enumerate(chunks, 1):
            parts.append(
                f"[{i}] Source: {c['title']} (Page {c['page']})\n"
                f"Topic: {c['topic']}\n"
                f"---\n{c['text']}\n"
            )
        return "\n\n".join(parts)

    def deduplicate_citations(self, chunks: list[dict]) -> list[dict]:
        """Return unique citation records (by pdf + page)."""
        by_page = {}
        for c in chunks:
            key = (c["source_pdf"], c["page"])
            if key not in by_page or c["score"] > by_page[key]["score"]:
                by_page[key] = {
                    "title":      c["title"],
                    "topic":      c["topic"],
                    "page":       c["page"],
                    "source_url": c["source_url"],
                    "source_pdf": c["source_pdf"],
                    "score":      c["score"],
                }
        return list(by_page.values())

    def answer(
        self,
        query: str,
        hindi: bool = False,
        chat_history: list | None = None,
    ) -> dict:
        """
        Full RAG pipeline.

        Returns:
            {
                "answer":     str,
                "citations":  list[dict],
                "chunks":     list[dict],
            }
        """
        self._load()

        chunks = self.retrieve(query)
        context = self.build_context(chunks)

        user_message = (
            f"Context from SEBI official documents:\n\n{context}\n\n"
            f"Question: {query}"
        )
        # Always inject an explicit language instruction so toggling mid-conversation
        # doesn't leave the model following the previous language from chat history.
        user_message += HINDI_SUFFIX if hindi else ENGLISH_SUFFIX

        # Build conversation history for the new SDK
        contents = []
        if chat_history:
            for turn in chat_history[-6:]:   # last 3 exchanges
                contents.append(
                    genai_types.Content(role="user",  parts=[genai_types.Part(text=turn["user"])])
                )
                contents.append(
                    genai_types.Content(role="model", parts=[genai_types.Part(text=turn["assistant"])])
                )
        contents.append(
            genai_types.Content(role="user", parts=[genai_types.Part(text=user_message)])
        )

        # Try models in order; retry transient errors (503/429) with backoff
        last_error  = None
        MAX_RETRIES = 3
        answer_text = None  # will be set on success

        def _is_retryable(err_str: str) -> bool:
            """Quota/rate errors: retry with backoff on the same model."""
            return (
                "429" in err_str
                or "503" in err_str
                or "RESOURCE_EXHAUSTED" in err_str
                or "UNAVAILABLE" in err_str
                or "quota" in err_str.lower()
                or "unavailable" in err_str.lower()
            )

        def _skip_model(err_str: str) -> bool:
            """Model not found / not supported for this key: skip silently."""
            return (
                "404" in err_str
                or "NOT_FOUND" in err_str
                or "not found" in err_str.lower()
                or "not supported" in err_str.lower()
            )

        for model_name in self._model_candidates:
            success = False
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    response = self._genai_client.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config=genai_types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT,
                            temperature=0.2,
                            max_output_tokens=2048,
                        ),
                    )
                    answer_text = response.text
                    last_error  = None
                    success     = True
                    break                       # got answer — exit inner loop
                except Exception as e:
                    err_str = str(e)
                    if _skip_model(err_str):
                        last_error = e
                        break                   # model unavailable — try next
                    elif _is_retryable(err_str):
                        last_error = e
                        if attempt < MAX_RETRIES:
                            time.sleep(2 ** attempt)   # 2 s, 4 s back-off
                        # else: fall through to next attempt, which ends loop
                    else:
                        raise                   # non-retryable — bubble up
            if success:
                break                           # have answer — exit outer loop
            # else: try next model

        if answer_text is None:
            raise RuntimeError(
                f"All Gemini models are temporarily unavailable. "
                f"Last error: {last_error}\n"
                "Please wait a moment and try again."
            )

        citations = self.deduplicate_citations(chunks)

        return {
            "answer":    answer_text,
            "citations": citations,
            "chunks":    chunks,
        }


# Module-level singleton
_assistant = None

def get_assistant() -> SEBIAssistant:
    global _assistant
    if _assistant is None:
        _assistant = SEBIAssistant()
    return _assistant


if __name__ == "__main__":
    # Quick smoke test
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else "How do I file a complaint against my broker?"
    print(f"\nQuery: {query}\n")
    result = get_assistant().answer(query)
    print("Answer:\n", result["answer"])
    print("\nCitations:")
    for c in result["citations"]:
        print(f"  - {c['title']} | Page {c['page']} | Score: {c['score']}")
