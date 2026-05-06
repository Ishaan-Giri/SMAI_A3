"""
app.py - SEBI Retail Investor Assistant Chatbot
A Streamlit RAG chatbot backed by official SEBI educational PDFs.
"""

import os
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Page config (must be FIRST Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="SEBI Investor Assistant",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* === Base === */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

/* === Hide only the footer & top decoration bar, keep header/sidebar toggle === */
footer,
footer * {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
}
[data-testid="stDecoration"] {
    display: none !important;
}


/* === App background === */
.stApp {
    background: #0D1B2A !important;
}

/* === Chat input bar — keep Streamlit's natural positioning, just restyle === */
[data-testid="stBottom"],
[data-testid="stBottomBlockContainer"] {
    background: #0D1B2A !important;
    border-top: 1px solid #1E3A52 !important;
    padding: 10px 20px 14px !important;
    box-shadow: none !important;
}
[data-testid="stChatFloatingInputContainer"] {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
}

/* Remove any stray outline Streamlit adds around the input zone */
[data-testid="stBottom"] > div,
[data-testid="stBottomBlockContainer"] > div {
    outline: none !important;
    border: none !important;
    background: transparent !important;
}

/* === Main container === */
[data-testid="stMainBlockContainer"] {
    background: transparent !important;
    max-width: 820px !important;
    padding-bottom: 110px !important;
}

/* === Sidebar === */
[data-testid="stSidebar"] {
    background: #0F2133 !important;
    border-right: 1px solid #1E3A52 !important;
}
[data-testid="stSidebar"] * {
    color: #CBD5E1 !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4 {
    color: #F1F5F9 !important;
}
[data-testid="stSidebar"] label {
    color: #CBD5E1 !important;
}
[data-testid="stSidebar"] .stCaption p,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
    color: #64748B !important;
}

/* --- Sidebar: success / warning alerts --- */
[data-testid="stSidebar"] [data-testid="stAlert"] {
    border-radius: 10px !important;
    border-left-width: 4px !important;
}
[data-testid="stSidebar"] [data-testid="stAlert"] p,
[data-testid="stSidebar"] [data-testid="stAlert"] span {
    color: #A7F3D0 !important;
    font-weight: 500 !important;
}

/* --- Sidebar: expander --- */
[data-testid="stSidebar"] [data-testid="stExpander"] {
    background: #152D42 !important;
    border: 1px solid #1E3A52 !important;
    border-radius: 10px !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary span,
[data-testid="stSidebar"] [data-testid="stExpander"] p {
    color: #CBD5E1 !important;
}

/* --- Sidebar: button --- */
[data-testid="stSidebar"] .stButton > button {
    border: 1px solid #1E3A52 !important;
    border-radius: 10px !important;
    background: #152D42 !important;
    color: #CBD5E1 !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    border-color: #00C2CB !important;
    background: #1A3A4F !important;
    color: #E2E8F0 !important;
}

/* === Bottom bar & chat input === */
[data-testid="stBottomBlockContainer"] {
    background: #0D1B2A !important;
}
[data-testid="stChatFloatingInputContainer"] {
    background: #0D1B2A !important;
    border-top: 1px solid #1E3A52 !important;
    padding-bottom: 10px !important;
}
[data-testid="stChatInput"] textarea {
    background: #132436 !important;
    border: 1px solid #2A4A63 !important;
    border-radius: 14px !important;
    color: #E2E8F0 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.95rem !important;
    padding: 12px 16px !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: #4A6477 !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: #00C2CB !important;
    box-shadow: 0 0 0 3px rgba(0,194,203,0.15) !important;
}

/* === Chat messages === */
[data-testid="stChatMessage"] {
    background: #132436 !important;
    border: 1px solid #1E3A52 !important;
    border-radius: 14px !important;
    padding: 14px 18px !important;
    margin-bottom: 10px !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: #0E2F45 !important;
    border-color: #1D4D6A !important;
}
/* All text inside chat bubbles */
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] td,
[data-testid="stChatMessage"] th,
[data-testid="stChatMessage"] div,
[data-testid="stChatMessage"] strong,
[data-testid="stChatMessage"] em,
[data-testid="stChatMessage"] label {
    color: #CBD5E1 !important;
}
[data-testid="stChatMessage"] h1,
[data-testid="stChatMessage"] h2,
[data-testid="stChatMessage"] h3,
[data-testid="stChatMessage"] h4 {
    color: #F1F5F9 !important;
}
[data-testid="stChatMessage"] a {
    color: #00C2CB !important;
}
[data-testid="stChatMessage"] code {
    background: #0D2035 !important;
    color: #7DD3FC !important;
    border-radius: 4px !important;
    padding: 1px 6px !important;
    font-size: 0.88em !important;
}

/* === Expander (citations) === */
[data-testid="stExpander"] {
    background: #132436 !important;
    border: 1px solid #1E3A52 !important;
    border-radius: 10px !important;
    margin-top: 8px !important;
}
[data-testid="stExpander"] summary {
    color: #94A3B8 !important;
}
[data-testid="stExpander"] summary span {
    color: #94A3B8 !important;
    font-size: 0.88rem !important;
}
[data-testid="stExpander"] summary:hover span {
    color: #00C2CB !important;
}
[data-testid="stExpander"] p,
[data-testid="stExpander"] div,
[data-testid="stExpander"] span {
    color: #CBD5E1 !important;
}

/* === Caption (main area) === */
.stCaption p,
[data-testid="stCaptionContainer"] p {
    color: #64748B !important;
}

/* === Suggestion buttons (main area) === */
.stButton > button {
    border: 1px solid #1E3A52 !important;
    border-radius: 12px !important;
    background: #132436 !important;
    color: #CBD5E1 !important;
    font-size: 0.84rem !important;
    font-weight: 500 !important;
    text-align: left !important;
    white-space: normal !important;
    height: auto !important;
    padding: 12px 14px !important;
    line-height: 1.5 !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    border-color: #00C2CB !important;
    background: #0E2F45 !important;
    color: #E2E8F0 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 18px rgba(0,194,203,0.12) !important;
}

/* === Horizontal rule === */
hr {
    border: none !important;
    border-top: 1px solid #1E3A52 !important;
    margin: 18px 0 !important;
}

/* === Custom scrollbar === */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #0D1B2A; }
::-webkit-scrollbar-thumb { background: #2A4A63; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #00C2CB; }

/* === Header card === */
.header-card {
    background: linear-gradient(135deg, #0E2F45 0%, #0F3A52 60%, #0B2D43 100%);
    border: 1px solid #1D4D6A;
    border-radius: 18px;
    padding: 26px 28px 22px;
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
}
.header-card::before {
    content: '';
    position: absolute;
    top: -40px; right: -40px;
    width: 160px; height: 160px;
    background: radial-gradient(circle, rgba(0,194,203,0.18) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
}
.header-badge {
    display: inline-block;
    background: rgba(0,194,203,0.14);
    border: 1px solid rgba(0,194,203,0.38);
    color: #00C2CB !important;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 1px;
    padding: 3px 11px;
    border-radius: 999px;
    margin-bottom: 12px;
    text-transform: uppercase;
}
.header-card h1 {
    margin: 0 0 8px 0;
    color: #F1F5F9 !important;
    font-size: 1.55rem;
    font-weight: 700;
    letter-spacing: -0.4px;
}
.header-card p {
    margin: 0;
    color: #94A3B8 !important;
    font-size: 0.92rem;
    line-height: 1.55;
}

/* === Citation cards === */
.cit-card {
    background: #0D2035;
    border: 1px solid #1E3A52;
    border-left: 3px solid #00C2CB;
    border-radius: 9px;
    padding: 10px 14px;
    margin: 7px 0;
    transition: background 0.15s ease;
}
.cit-card:hover { background: #112840; }
.cit-title {
    font-weight: 600;
    color: #E2E8F0 !important;
    font-size: 0.9rem;
}
.cit-meta {
    color: #64748B !important;
    font-size: 0.78rem;
    margin-top: 4px;
}
.cit-badge {
    display: inline-block;
    margin-left: 8px;
    border-radius: 999px;
    border: 1px solid rgba(0,194,203,0.4);
    background: rgba(0,194,203,0.1);
    color: #00C2CB !important;
    font-size: 0.66rem;
    font-weight: 700;
    padding: 1px 8px;
    text-transform: uppercase;
    letter-spacing: 0.4px;
}
.cit-link {
    color: #00C2CB !important;
    text-decoration: none;
    font-weight: 500;
}
.cit-link:hover {
    text-decoration: underline;
    color: #38DDE8 !important;
}

/* === Sidebar brand === */
.sidebar-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 4px;
}
.sidebar-brand .brand-icon { font-size: 1.6rem; }
.sidebar-brand .brand-name {
    font-size: 1.08rem;
    font-weight: 700;
    color: #F1F5F9 !important;
}
.sidebar-section-label {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 1.3px;
    text-transform: uppercase;
    color: #475569 !important;
    margin: 20px 0 7px 0;
}
</style>
""", unsafe_allow_html=True)


# ── PDF title/topic map (mirrors ingest.py) ───────────────────────────────────
PDF_INFO = {
    "ipo_guide.pdf":                                           ("How to Invest in an IPO",                    "IPO"),
    "mutual_funds_intro.pdf":                                  ("Introduction to Mutual Funds",               "Mutual Funds"),
    "scores_grievance.pdf":                                    ("Investor Grievance – SEBI SCORES",           "SCORES"),
    "securities_market_booklet.pdf":                           ("Securities Market Booklet",                  "Securities Market"),
    "Financial Education Booklet - English.pdf":               ("Financial Education Booklet",                "Financial Education"),
    "mutual_funds_dos_donts.pdf":                              ("Mutual Funds – Dos and Don'ts",              "Mutual Funds"),
    "intro_securities_markets.pdf":                            ("Introduction to Securities Markets",         "Securities Market"),
    "investor_charter_stock_exchange.pdf":                     ("Investor Charter – Stock Exchange",          "Investor Rights"),
    "FAQ_on_kyc_norms.pdf":                                    ("KYC and Demat Account Opening",              "KYC"),
    "nri_investments.pdf":                                     ("Investments by NRIs",                        "NRI Investments"),
    "PPT-5 Corporate Actions - Dividends, Bonus, Splits, etc_.pdf": ("Corporate Actions",                   "Corporate Actions"),
    "sharedebentureholder.pdf":                                ("Share and Debenture Holder Guide",           "Shares & Debentures"),
    "MCQ on Commodity Derivatives - English-Options.pdf":      ("Commodity Derivatives – Options",           "Derivatives"),
    "PPT-21-ISM.pdf":                                          ("Indian Securities Market (Detailed)",        "Securities Market"),
    "executivesmodule.pdf":                                    ("Financial Education – Executives",           "Financial Planning"),
    "PPT-6 How to buy and sell shares in Stock Exchanges.pdf": ("How to Buy & Sell Shares",                  "Trading"),
    "beginners.pdf":                                           ("Beginner's Guide to Capital Markets",        "Capital Markets"),
    "PPT-10 Updated PPT on REITs_approved 30 Sep 2022.pdf":   ("Introduction to REITs",                     "REITs"),
    "PPT-11 Updated PPT on InvITs _approved 30 Sep 2022.pdf": ("Introduction to InvITs",                    "InvITs"),
    "PPT-4 How to Invest in Rights Issue.pdf":                 ("Primary Market – Rights Issue",             "Rights Issue"),
    "PPT-7 Depository Services updated 30 Sep 2022.pdf":       ("Depository Services",                       "Depository"),
    "corporatebonds.pdf":                                      ("Corporate Bonds Market Guide",               "Corporate Bonds"),
    "primarymarkets.pdf":                                      ("Introduction to Primary Markets",            "Primary Market"),
}


# ── Helpers ───────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="🔧 Loading AI models and knowledge base…")
def load_assistant():
    """Load the SEBI RAG assistant (cached across sessions)."""
    from rag import get_assistant
    asst = get_assistant()
    asst._load()
    return asst


def render_citations(citations: list[dict]):
    """Render citation cards inside an expander."""
    if not citations:
        return
    label = f"📄 {len(citations)} Source{'s' if len(citations) > 1 else ''} from SEBI Documents"
    with st.expander(label, expanded=False):
        for c in citations:
            score_pct = int(c.get("score", 0) * 100)
            url_html  = ""
            if c.get("source_url"):
                url_html = f'&nbsp;·&nbsp;<a href="{c["source_url"]}" target="_blank" class="cit-link">🔗 View PDF</a>'
            st.markdown(f"""
<div class="cit-card">
  <div class="cit-title">
    {c['title']}
    <span class="cit-badge">{c['topic']}</span>
  </div>
  <div class="cit-meta">
    Page {c['page']}&nbsp;·&nbsp;Relevance {score_pct}%{url_html}
  </div>
</div>
""", unsafe_allow_html=True)


# ── Suggested questions ────────────────────────────────────────────────────────
SUGGESTIONS = [
    "How do I file a complaint against my broker on SEBI SCORES?",
    "What is the step-by-step process to apply for an IPO?",
    "What documents are needed to open a Demat account?",
    "How does SEBI protect mutual fund investors?",
    "What are my rights as a retail investor in India?",
    "What is the KYC process for investing in mutual funds?",
]


# ── Session state init ─────────────────────────────────────────────────────────
if "messages"      not in st.session_state: st.session_state.messages      = []
if "chat_history"  not in st.session_state: st.session_state.chat_history  = []
if "pending_query" not in st.session_state: st.session_state.pending_query = None


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
<div class="sidebar-brand">
  <span class="brand-icon">📊</span>
  <span class="brand-name">SEBI Assistant</span>
</div>
""", unsafe_allow_html=True)
    st.caption("RAG helpdesk for retail investors · powered by Gemini")

    # — API Key —
    st.markdown('<div class="sidebar-section-label">API Key</div>', unsafe_allow_html=True)
    env_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if env_key:
        key_preview = f"{env_key[:5]}..." if len(env_key) > 5 else f"{env_key}..."
        st.success(f"✅ Active key: `{key_preview}`")
    else:
        st.warning("⚠️ No API key found in `.env`.")

    # — Language toggle —
    st.markdown('<div class="sidebar-section-label">Language</div>', unsafe_allow_html=True)
    hindi_mode = st.toggle("🇮🇳 Respond in Hindi", value=False, key="hindi_toggle")

    # — Knowledge base status —
    st.markdown('<div class="sidebar-section-label">Knowledge Base</div>', unsafe_allow_html=True)
    pdf_dir   = Path(__file__).parent / "data" / "pdfs"
    pdf_files = sorted(pdf_dir.glob("*.pdf"))

    if pdf_files:
        st.success(f"📚 {len(pdf_files)} SEBI PDFs loaded")
        with st.expander("View loaded documents", expanded=False):
            for p in pdf_files:
                info  = PDF_INFO.get(p.name)
                title = info[0] if info else p.stem.replace("_", " ").title()
                st.write(f"• {title}")
    else:
        st.error("❌ No PDFs found. Run `python ingest.py` first.")

    # — Clear chat —
    st.markdown('<div class="sidebar-section-label">Actions</div>', unsafe_allow_html=True)
    if st.button("🗑️  Clear Chat History", use_container_width=True):
        st.session_state.messages     = []
        st.session_state.chat_history = []
        st.rerun()

    # — Disclaimer —
    st.markdown('<div style="margin-top:24px;"></div>', unsafe_allow_html=True)
    st.caption(
        "📌 For educational use only. Verify final details on "
        "[sebi.gov.in](https://www.sebi.gov.in) or "
        "[investor.sebi.gov.in](https://investor.sebi.gov.in)."
    )


# ══════════════════════════════════════════════════════════════════════════════
# MAIN AREA
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="header-card">
  <div class="header-badge">📋 Official SEBI Documents · RAG Powered</div>
  <h1>SEBI Retail Investor Assistant</h1>
  <p>Ask about IPOs, KYC, mutual funds, grievances, and investor rights.
     Every answer cites official SEBI PDFs with page references.</p>
</div>
""", unsafe_allow_html=True)


# ── Suggested questions (only when chat is empty) ─────────────────────────────
if not st.session_state.messages:
    st.caption("✨ Try one of these questions:")
    cols = st.columns(2)
    for i, q in enumerate(SUGGESTIONS):
        with cols[i % 2]:
            if st.button(q, key=f"sq_{i}", use_container_width=True):
                st.session_state.pending_query = q
                st.rerun()
    st.markdown("<hr/>", unsafe_allow_html=True)


# ── Render chat history ────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("citations"):
            render_citations(msg["citations"])


# ── Core query handler ────────────────────────────────────────────────────────
def process_query(user_query: str):
    """Run RAG pipeline and append results to session state."""
    user_query = user_query.strip()
    if not user_query:
        return

    # Guard: API key required
    if not os.getenv("GOOGLE_API_KEY", "").strip():
        st.warning("Please enter your **Google AI Studio API key** in the sidebar to start chatting.", icon="🔑")
        return

    # Show user message immediately
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    # Get assistant response
    with st.chat_message("assistant"):
        with st.spinner("🔍 Searching SEBI documents…"):
            try:
                assistant = load_assistant()
                result    = assistant.answer(
                    query=user_query,
                    hindi=st.session_state.get("hindi_toggle", False),
                    chat_history=st.session_state.chat_history,
                )
                answer_text = result["answer"]
                citations   = result["citations"]

            except ValueError as e:
                answer_text = f"⚠️ **Configuration error:** {e}"
                citations   = []
            except Exception as e:
                answer_text = (
                    f"❌ **Error:** {str(e)}\n\n"
                    "Please check your API key and ensure the knowledge base is ingested."
                )
                citations = []

        st.markdown(answer_text)
        render_citations(citations)

    # Persist
    st.session_state.messages.append({
        "role":      "assistant",
        "content":   answer_text,
        "citations": citations,
    })
    st.session_state.chat_history.append({
        "user":      user_query,
        "assistant": answer_text,
    })


# ── Handle suggested question click ──────────────────────────────────────────
if st.session_state.pending_query:
    q = st.session_state.pending_query
    st.session_state.pending_query = None
    process_query(q)

# ── Chat input ────────────────────────────────────────────────────────────────
if prompt := st.chat_input("Ask about IPOs, Mutual Funds, SCORES complaints, KYC…"):
    process_query(prompt)
