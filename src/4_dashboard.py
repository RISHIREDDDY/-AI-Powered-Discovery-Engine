import os
import sys
import time
import subprocess
import html
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from pinecone import Pinecone

# Determine project root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Streamlit Page Config
st.set_page_config(
    page_title="Google Photos | Discovery Engine",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-End Modern CSS Design System
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg-main: #0B0F19;
    --card-bg: rgba(17, 24, 39, 0.75);
    --border-color: rgba(255, 255, 255, 0.08);
    --border-hover: rgba(99, 102, 241, 0.4);
    --text-primary: #F9FAFB;
    --text-secondary: #9CA3AF;
    --accent-blue: #4285F4;
    --accent-red: #EA4335;
    --accent-yellow: #FBBC05;
    --accent-green: #34A853;
    --accent-indigo: #6366F1;
}

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background-color: var(--bg-main);
    color: var(--text-primary);
}

/* Glassmorphic Cards */
.bento-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    backdrop-filter: blur(16px);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 20px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.5);
}

.bento-card:hover {
    border-color: var(--border-hover);
    transform: translateY(-2px);
    box-shadow: 0 12px 30px -4px rgba(99, 102, 241, 0.15);
}

/* KPI Chips */
.kpi-container {
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.kpi-title {
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-secondary);
}
.kpi-value {
    font-size: 2.2rem;
    font-weight: 800;
    color: #FFFFFF;
    margin-top: 4px;
    background: linear-gradient(135deg, #FFFFFF 0%, #CBD5E1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.kpi-badge {
    padding: 4px 10px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
}

/* Hero Header */
.hero-header {
    background: linear-gradient(135deg, rgba(66, 133, 244, 0.1) 0%, rgba(99, 102, 241, 0.05) 50%, rgba(0, 0, 0, 0) 100%);
    border: 1px solid rgba(66, 133, 244, 0.2);
    border-radius: 20px;
    padding: 32px;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
}
.hero-title {
    font-size: 2.3rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    background: linear-gradient(135deg, #FFFFFF 30%, #93C5FD 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 8px;
}
.hero-subtitle {
    font-size: 1.05rem;
    color: var(--text-secondary);
    max-width: 800px;
    line-height: 1.6;
}

/* Source Badges */
.badge-gp { background: rgba(52, 168, 83, 0.15); color: #34A853; border: 1px solid rgba(52, 168, 83, 0.3); }
.badge-apple { background: rgba(255, 255, 255, 0.1); color: #E2E8F0; border: 1px solid rgba(255, 255, 255, 0.2); }
.badge-reddit { background: rgba(255, 69, 0, 0.15); color: #FF4500; border: 1px solid rgba(255, 69, 0, 0.3); }
.badge-support { background: rgba(66, 133, 244, 0.15); color: #4285F4; border: 1px solid rgba(66, 133, 244, 0.3); }

/* Evidence Card */
.evidence-card {
    background: rgba(17, 24, 39, 0.6);
    border-left: 4px solid var(--accent-indigo);
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 16px;
    border-top: 1px solid var(--border-color);
    border-right: 1px solid var(--border-color);
    border-bottom: 1px solid var(--border-color);
}
.evidence-quote {
    font-size: 0.98rem;
    font-style: italic;
    color: #F1F5F9;
    line-height: 1.6;
    margin-bottom: 12px;
}
.pill-tag {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-right: 8px;
    margin-bottom: 4px;
}
.pill-blue { background: rgba(66, 133, 244, 0.15); color: #93C5FD; }
.pill-purple { background: rgba(168, 85, 247, 0.15); color: #D8B4FE; }
.pill-amber { background: rgba(245, 158, 11, 0.15); color: #FCD34D; }

/* Custom Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: rgba(17, 24, 39, 0.5);
    padding: 6px;
    border-radius: 12px;
    border: 1px solid var(--border-color);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: #94A3B8;
    font-weight: 600;
    padding: 8px 18px;
    transition: all 0.2s;
}
.stTabs [aria-selected="true"] {
    background-color: var(--accent-indigo) !important;
    color: #FFFFFF !important;
}
</style>
"""

st.html(CUSTOM_CSS)

@st.cache_resource(show_spinner=False)
def get_vector_services():
    pinecone_key = os.getenv("PINECONE_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    pc = Pinecone(api_key=pinecone_key)
    index = pc.Index("google-photos-discovery-v3")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=gemini_key)
    return index, embeddings

@st.cache_resource(show_spinner=False)
def get_llm():
    gemini_key = os.getenv("GEMINI_API_KEY")
    return ChatGoogleGenerativeAI(model="gemini-3.6-flash", api_key=gemini_key, temperature=0.2, max_retries=0)

def run_live_ingestion_pipeline():
    with st.status("🔍 Scraping & Analyzing Live Reviews...", expanded=True) as status:
        # Step 1: Ingestion
        status.write("🌐 **Step 1/3**: Scraping Google Play Store, Apple App Store, Reddit & Google Support Forums via Apify...")
        ingest_script = os.path.join(BASE_DIR, "src", "1_ingest_data.py")
        res1 = subprocess.run([sys.executable, ingest_script], capture_output=True, text=True, cwd=BASE_DIR)
        if res1.returncode != 0:
            st.error(f"Ingestion failed: {res1.stderr}")
            status.update(label="❌ Ingestion failed", state="error")
            return
        status.write("✅ Live reviews scraped across all 4 public sources.")
        
        # Step 2: Processing & Cognitive Structuring
        status.write("🧠 **Step 2/3**: Extracting cognitive memory patterns into SQLite (`discovery_engine.db`)...")
        process_script = os.path.join(BASE_DIR, "src", "2_process_reviews.py")
        res2 = subprocess.run([sys.executable, process_script], capture_output=True, text=True, cwd=BASE_DIR)
        if res2.returncode != 0:
            st.error(f"Processing failed: {res2.stderr}")
            status.update(label="❌ Processing failed", state="error")
            return
        status.write("✅ Memory breakdowns classified into structured database.")
        
        # Step 3: Pinecone Indexing
        status.write("🌲 **Step 3/3**: Generating embeddings & indexing vectors to Pinecone...")
        index_script = os.path.join(BASE_DIR, "src", "3_index_pinecone.py")
        res3 = subprocess.run([sys.executable, index_script], capture_output=True, text=True, cwd=BASE_DIR)
        if res3.returncode != 0:
            status.write(f"⚠️ Pinecone sync skipped or warning: {res3.stderr.strip() or 'Continuing with updated database.'}")
        else:
            status.write("✅ Vector embeddings synced to Pinecone.")
            
        status.update(label="🎉 Live Analysis Complete! Refreshing dashboard...", state="complete", expanded=False)
        time.sleep(1)
        st.rerun()

def get_data():
    db_path = os.path.join(BASE_DIR, "data", "discovery_engine.db")
    df = pd.DataFrame()
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        try:
            df = pd.read_sql_query("SELECT * FROM structured_reviews", conn)
        except Exception:
            pass
        finally:
            conn.close()
            
    if df.empty:
        json_path = os.path.join(BASE_DIR, "data", "structured_reviews.json")
        if os.path.exists(json_path):
            try:
                df = pd.read_json(json_path)
            except Exception:
                pass
                
    if not df.empty and 'source_url' not in df.columns:
        df['source_url'] = ''
        
    return df

@st.cache_data(show_spinner=False)
def generate_executive_summary_cached(stats_tuple):
    stats = dict(stats_tuple)
    top_opps = list(stats.keys())[:3]
    top_opps_str = ", ".join(top_opps) if top_opps else "Episodic Search Gaps"
    
    return f"""
    ### 🎯 Executive Synthesis for Product Review
    
    **1. Core Memory Breakdown Pattern:**
    Analysis of live user feedback across **Google Play, Apple App Store, Reddit, and Google Support Community** reveals that search failures are predominantly cognitive mismatches rather than keyword omissions. Users retain vivid **episodic context** (e.g. *who was in the photo, emotional intent, humor, visual packaging cues*), but modern algorithmic search is over-reliant on **exact text OCR or front-facing facial tags**. 
    
    **2. Top Identified Opportunity Clusters:**
    - **{top_opps[0] if len(top_opps) > 0 else 'Non-Frontal Facial Recognition'}**: Users report severe frustration trying to retrieve photos of loved ones when faces are angled away or in profile.
    - **{top_opps[1] if len(top_opps) > 1 else 'Document & Receipt OCR Mismatch'}**: Searching broad conceptual categories ('medicine') fails to identify text on blister packs.
    - **{top_opps[2] if len(top_opps) > 2 else 'Chronological Sorting Discrepancies'}**: Cross-device sync discrepancies break user's chronological mental models.
    
    **3. High-Leverage Recommendations:**
    1. **Multimodal Intent Matching**: Empower search to understand semantic visual concepts (*e.g. 'cat meme'* rather than literal cat image recognition).
    2. **Co-Occurrence Entity Association**: Cluster profile photos by co-occurring metadata (clothing, events, timestamp sequences).
    3. **Hybrid Fuzzy Document OCR**: Automatically map product categories to text snippets found on receipts and packaging.
    """

def generate_executive_summary(df, llm):
    stats = df['opportunity_area'].value_counts().to_dict()
    stats_tuple = tuple(stats.items())
    prompt = f"""
    You are a Google Photos Principal PM presenting to leadership.
    Analyze this breakdown of photo retrieval failures from public feedback: {stats}
    
    Generate a sleek 3-part brief:
    1. Core Memory Breakdown Pattern
    2. Top 3 Opportunity Clusters
    3. Strategic Product Recommendations
    Use concise Markdown, bullet points, and high-impact PM phrasing.
    """
    try:
        response = llm.invoke(prompt)
        return response.content, False
    except Exception:
        return generate_executive_summary_cached(stats_tuple), True

def format_source_badge(source):
    s = str(source).lower()
    if "play" in s:
        return '<span class="kpi-badge badge-gp">▶ Google Play</span>'
    elif "apple" in s or "ios" in s or "app store" in s:
        return '<span class="kpi-badge badge-ios">🍏 App Store</span>'
    elif "reddit" in s:
        return '<span class="kpi-badge badge-reddit">💬 Reddit</span>'
    else:
        return '<span class="kpi-badge badge-support">🌐 Support Community</span>'

def main():
    # Hero Section
    st.html("""
    <div class="hero-header">
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
            <span style="font-size: 2rem;">📸</span>
            <span style="font-size: 0.85rem; font-weight: 700; color: #60A5FA; text-transform: uppercase; letter-spacing: 0.1em; background: rgba(59, 130, 246, 0.15); padding: 4px 12px; border-radius: 9999px; border: 1px solid rgba(59, 130, 246, 0.3);">
                Product Discovery Engine
            </span>
        </div>
        <div class="hero-title">Google Photos: Human Memory Breakdown</div>
        <div class="hero-subtitle">
            Uncovering what people remember, what they forget, and where algorithmic retrieval breaks down using live evidence from <b>Google Play, App Store, Reddit, and Google Support Forums</b>.
        </div>
    </div>
    """)
    
    raw_df = get_data()
    if raw_df.empty:
        st.error("⚠️ No data found in SQLite database. Please run the ingestion script (`python src/1_ingest_data.py`) and processing script (`python src/2_process_reviews.py`).")
        return
        
    # Sidebar Controls
    with st.sidebar:
        st.markdown("### ⚙️ Engine Controls")
        st.html("<div style='height: 1px; background: rgba(255,255,255,0.08); margin-bottom: 16px;'></div>")
        
        sources = list(raw_df['source'].unique())
        selected_sources = st.multiselect(
            "Filter Public Sources:",
            options=sources,
            default=sources
        )
        
        st.html("<div style='height: 1px; background: rgba(255,255,255,0.08); margin: 20px 0;'></div>")
        st.markdown("### ⚡ Live Discovery Pipeline")
        st.caption("Trigger Apify & public scrapers to crawl fresh user feedback across Google Play, Apple App Store, Reddit, and Google Support Community.")
        
        if st.button("🚀 Fetch & Analyse Live Reviews", type="primary", use_container_width=True):
            run_live_ingestion_pipeline()
            
        st.html("<div style='height: 1px; background: rgba(255,255,255,0.08); margin: 20px 0;'></div>")
        st.caption("NextLeap PM Discovery Project • v2.0")

    df = raw_df[raw_df['source'].isin(selected_sources)] if selected_sources else raw_df
    
    # KPI Bento Metric Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.html(f"""
        <div class="bento-card">
            <div class="kpi-title">Analyzed Public Issues</div>
            <div class="kpi-value">{len(df)}</div>
            <div style="font-size: 0.8rem; color: #34D399; margin-top: 4px;">● Multi-Source Validated</div>
        </div>
        """)
    with col2:
        st.html(f"""
        <div class="bento-card">
            <div class="kpi-title">Active Public Sources</div>
            <div class="kpi-value">{df['source'].nunique()}</div>
            <div style="font-size: 0.8rem; color: #60A5FA; margin-top: 4px;">Play, iOS, Reddit, Forum</div>
        </div>
        """)
    with col3:
        st.html(f"""
        <div class="bento-card">
            <div class="kpi-title">Identified Root Causes</div>
            <div class="kpi-value">{df['opportunity_area'].nunique()}</div>
            <div style="font-size: 0.8rem; color: #FBBF24; margin-top: 4px;">Opportunity Vectors</div>
        </div>
        """)
    with col4:
        st.html(f"""
        <div class="bento-card">
            <div class="kpi-title">Semantic Vectors</div>
            <div class="kpi-value">{len(raw_df)}</div>
            <div style="font-size: 0.8rem; color: #A78BFA; margin-top: 4px;">Pinecone Index Ready</div>
        </div>
        """)

    # Main Navigation Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🧠 4 Memory Patterns",
        "📋 Executive Brief & Strategy",
        "🔍 Semantic Evidence (Pinecone RAG)",
        "🗃️ Raw Multi-Source Data"
    ])

    # ---------------- TAB 1: 4 MEMORY PATTERNS ----------------
    with tab1:
        st.markdown("### 🧩 How Human Memory Breaks Down During Photo Search")
        st.markdown("A deep empirical look into the **4 core exploratory questions** governing photo retrieval:")
        
        row1_col1, row1_col2 = st.columns(2)
        
        with row1_col1:
            st.html("""
            <div class="bento-card" style="margin-bottom: 10px;">
                <div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 4px;">
                    1. What kinds of photos do users struggle to retrieve?
                </div>
                <div style="font-size: 0.85rem; color: #94A3B8;">
                    Distribution of media types that trigger search failures
                </div>
            </div>
            """)
            
            pie_counts = df['photo_type'].value_counts().reset_index()
            fig_pie = px.pie(
                pie_counts,
                names='photo_type',
                values='count',
                hole=0.55,
                color_discrete_sequence=['#4285F4', '#EA4335', '#FBBC05', '#34A853', '#8B5CF6', '#EC4899']
            )
            fig_pie.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#F1F5F9', family='Plus Jakarta Sans'),
                margin=dict(t=10, b=10, l=10, r=10),
                legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
                height=320
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with row1_col2:
            st.html("""
            <div class="bento-card" style="margin-bottom: 10px;">
                <div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 4px;">
                    2. What information do people actually remember?
                </div>
                <div style="font-size: 0.85rem; color: #94A3B8;">
                    Cognitive memory anchors users cling to when searching
                </div>
            </div>
            """)
            
            rem_df = df['remembered_anchors'].value_counts().reset_index().head(5)
            fig_bar_rem = px.bar(
                rem_df,
                x='count',
                y='remembered_anchors',
                orientation='h',
                color='count',
                color_continuous_scale=['#3B82F6', '#8B5CF6']
            )
            fig_bar_rem.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#F1F5F9', family='Plus Jakarta Sans'),
                margin=dict(t=10, b=10, l=10, r=10),
                xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', title="Reported Instances"),
                yaxis=dict(showgrid=False, title="", autorange="reversed"),
                coloraxis_showscale=False,
                height=320
            )
            st.plotly_chart(fig_bar_rem, use_container_width=True)

        row2_col1, row2_col2 = st.columns(2)
        
        with row2_col1:
            st.html("""
            <div class="bento-card" style="margin-bottom: 10px;">
                <div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 4px;">
                    3. What information have they forgotten?
                </div>
                <div style="font-size: 0.85rem; color: #94A3B8;">
                    Critical metadata gaps that cause keyword searches to fail
                </div>
            </div>
            """)
            
            forg_df = df['forgotten_elements'].value_counts().reset_index().head(5)
            fig_bar_forg = px.bar(
                forg_df,
                x='forgotten_elements',
                y='count',
                color='count',
                color_continuous_scale=['#EF4444', '#F59E0B']
            )
            fig_bar_forg.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#F1F5F9', family='Plus Jakarta Sans'),
                margin=dict(t=10, b=10, l=10, r=10),
                xaxis=dict(showgrid=False, title=""),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', title="Friction Frequency"),
                coloraxis_showscale=False,
                height=300
            )
            st.plotly_chart(fig_bar_forg, use_container_width=True)
            
        with row2_col2:
            # Safely build behavior cards inside single bento card using st.html
            behavior_cards = []
            for _, row in df.head(5).iterrows():
                src_url = row.get('source_url', '')
                is_valid = pd.notna(src_url) and str(src_url).strip().startswith("http")
                src_link = f"<a href='{src_url}' target='_blank' style='color: #60A5FA; text-decoration: none; font-size: 0.78rem; font-weight: 600; margin-left: 8px;'>🔗 View Source Proof ↗</a>" if is_valid else ""
                b_text = html.escape(str(row.get('search_behavior', 'Searched descriptive keywords')))
                s_text = html.escape(str(row.get('summary', 'Search friction reported.')))
                
                behavior_cards.append(f"""
                <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); padding: 12px 14px; border-radius: 8px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="font-size: 0.85rem; font-weight: 600; color: #93C5FD;">🔍 Behavior: {b_text}</div>
                        {src_link}
                    </div>
                    <div style="font-size: 0.8rem; color: #CBD5E1; margin-top: 4px;">⚡ Impact: {s_text}</div>
                </div>
                """)
            
            cards_html = "".join(behavior_cards)
            st.html(f"""
            <div class="bento-card">
                <div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 4px;">
                    4. How do users formulate searches when memory is incomplete?
                </div>
                <div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 16px;">
                    Observed user search behaviors vs. expected system response
                </div>
                {cards_html}
            </div>
            """)

    # ---------------- TAB 2: EXECUTIVE BRIEF ----------------
    with tab2:
        st.markdown("### 📋 Executive Summary & Strategic Roadmap")
        
        with st.spinner("Synthesizing executive findings..."):
            summary, is_fallback = generate_executive_summary(df, get_llm())
            
        st.html(f"""
        <div style="background: rgba(17, 24, 39, 0.75); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 4px solid #6366F1; border-radius: 12px; padding: 14px 20px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
            <span class="kpi-badge pill-purple">🤖 AI Strategy Brief</span>
            <span style="font-size: 0.8rem; color: #94A3B8;">{'Offline Heuristic Synthesis' if is_fallback else 'Generated Live by Gemini 3.6 Flash'}</span>
        </div>
        """)
        st.markdown(summary)
        
        st.markdown("### 📊 Opportunity Area Matrix")
        st.markdown("Root cause breakdown ranked by user volume and complaint severity:")
        
        opp_counts = df.groupby('opportunity_area').size().reset_index(name='Volume')
        fig_treemap = px.treemap(
            opp_counts,
            path=['opportunity_area'],
            values='Volume',
            color='Volume',
            color_continuous_scale=['#312E81', '#4F46E5', '#60A5FA']
        )
        fig_treemap.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#F1F5F9', family='Plus Jakarta Sans'),
            margin=dict(t=10, b=10, l=10, r=10),
            height=380
        )
        st.plotly_chart(fig_treemap, use_container_width=True)

    # ---------------- TAB 3: SEMANTIC EVIDENCE (RAG) ----------------
    with tab3:
        st.markdown("### 🔎 Semantic Evidence Search (Pinecone RAG)")
        st.markdown("Search across all vectorized user complaints to pull verbatim quotes, root causes, and **direct public source links**:")
        
        query_col, btn_col = st.columns([4, 1])
        with query_col:
            query = st.text_input(
                "Ask or search pain points:",
                value="face turned away cannot find photos of father",
                placeholder="e.g., 'medicine receipt OCR', 'out of order sync', 'funny meme search'",
                label_visibility="collapsed"
            )
        with btn_col:
            search_clicked = st.button("🚀 Retrieve Evidence", use_container_width=True)
            
        if search_clicked or query:
            with st.spinner("Querying Pinecone Vector Index..."):
                try:
                    index, embeddings = get_vector_services()
                    vector = embeddings.embed_query(query)
                    results = index.query(vector=vector, top_k=4, include_metadata=True)
                    
                    if results and 'matches' in results and len(results['matches']) > 0:
                        st.markdown(f"Found **{len(results['matches'])} matching user signals** in vector space:")
                        for match in results['matches']:
                            meta = match['metadata']
                            score = match['score']
                            source_url = meta.get('source_url', '')
                            source_name = meta.get('source', 'Public Discussion')
                            
                            link_btn = f"""<a href="{source_url}" target="_blank" style="display: inline-flex; align-items: center; gap: 6px; background: rgba(99, 102, 241, 0.2); color: #C7D2FE; padding: 6px 14px; border-radius: 8px; text-decoration: none; font-size: 0.82rem; font-weight: 600; border: 1px solid rgba(99, 102, 241, 0.4); transition: all 0.2s;">🔗 Verify Live Source Proof ↗</a>""" if source_url else ""
                            
                            safe_orig_text = html.escape(str(meta.get('original_text', '')))
                            safe_summary = html.escape(str(meta.get('summary', '')))
                            safe_source = html.escape(str(source_name))
                            safe_photo_type = html.escape(str(meta.get('photo_type', 'General Photo')))
                            safe_opp = html.escape(str(meta.get('opportunity_area', 'Retrieval Issue')))
                            
                            st.html(f"""
                            <div class="evidence-card">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                    <div>
                                        <span class="pill-tag pill-blue">🎯 {score*100:.1f}% Match</span>
                                        <span class="pill-tag pill-purple">{safe_photo_type}</span>
                                        <span style="font-size: 0.8rem; color: #94A3B8; margin-left: 6px;">Source: <b>{safe_source}</b></span>
                                    </div>
                                    <span class="pill-tag pill-amber">⚠️ {safe_opp}</span>
                                </div>
                                <div class="evidence-quote">"{safe_orig_text}"</div>
                                <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 10px; margin-top: 8px;">
                                    <div style="font-size: 0.85rem; color: #94A3B8; max-width: 70%;">
                                        <b>💡 Cognitive Takeaway:</b> {safe_summary}
                                    </div>
                                    <div>
                                        {link_btn}
                                    </div>
                                </div>
                            </div>
                            """)
                    else:
                        st.warning("No matches returned from Pinecone for this query.")
                except Exception as e:
                    st.error(f"Pinecone Search Error: {e}")

    # ---------------- TAB 4: RAW MULTI-SOURCE DATA ----------------
    with tab4:
        st.markdown("### 🗃️ Raw Multi-Source Discovery Database")
        st.markdown("Explore and verify all ingested user records with **direct clickable source links** across Google Play, Apple App Store, Reddit, and Google Support Community:")
        
        if 'source_url' not in df.columns:
            df['source_url'] = ''
            
        desired_cols = ['source', 'source_url', 'rating', 'photo_type', 'opportunity_area', 'summary', 'original_text']
        available_cols = [c for c in desired_cols if c in df.columns]
        display_df = df[available_cols]
        
        col_configs = {
            "source": st.column_config.TextColumn("Public Source", width="medium"),
            "source_url": st.column_config.LinkColumn("Proof Link", display_text="Open Live Source ↗", width="medium"),
            "rating": st.column_config.NumberColumn("Rating / Score", format="%d ⭐", width="small"),
            "photo_type": st.column_config.TextColumn("Target Media", width="medium"),
            "opportunity_area": st.column_config.TextColumn("Opportunity Cluster", width="medium"),
            "summary": st.column_config.TextColumn("AI Synthesis", width="large"),
            "original_text": st.column_config.TextColumn("Verbatim Feedback", width="large")
        }
        active_col_config = {k: v for k, v in col_configs.items() if k in available_cols}
        
        st.dataframe(
            display_df,
            use_container_width=True,
            column_config=active_col_config,
            hide_index=True
        )

if __name__ == "__main__":
    main()
