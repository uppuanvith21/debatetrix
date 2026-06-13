from __future__ import annotations

import datetime as dt
import html
from urllib.parse import quote_plus

import streamlit as st

from backend.ai_engine import analyze_claim, compare_rivals, get_provider_status
from backend.db import get_database_config, initialize_database, is_mysql_driver_available, load_fact_items, save_fact_items
from backend.fact_check_sources import FACT_CHECK_SOURCES, trusted_sources_by_region
from backend.i18n import LANGUAGES, t
from backend.ingestion import fetch_all_sources


st.set_page_config(
    page_title="Debatetrix AI",
    page_icon="DT",
    layout="wide",
    initial_sidebar_state="expanded",
)


CSS = """
<style>
:root {
  --dt-bg: #0b1020;
  --dt-panel: rgba(255,255,255,.08);
  --dt-card: rgba(255,255,255,.11);
  --dt-line: rgba(255,255,255,.16);
  --dt-text: #f7f8ff;
  --dt-muted: #b9c2d9;
  --dt-hot: #ff477e;
  --dt-cyan: #1ee3cf;
  --dt-yellow: #ffd166;
}
.stApp {
  background:
    radial-gradient(circle at 12% 10%, rgba(30,227,207,.18), transparent 30%),
    radial-gradient(circle at 84% 4%, rgba(255,71,126,.16), transparent 34%),
    linear-gradient(135deg, #0b1020 0%, #141827 52%, #101827 100%);
  color: var(--dt-text);
}
[data-testid="stSidebar"] {
  background: rgba(9, 13, 27, .92);
  border-right: 1px solid var(--dt-line);
}
h1, h2, h3 { letter-spacing: 0; }
.hero {
  padding: 30px 0 18px;
  border-bottom: 1px solid var(--dt-line);
  margin-bottom: 22px;
}
.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 7px 12px;
  border: 1px solid var(--dt-line);
  background: rgba(255,255,255,.06);
  border-radius: 8px;
  color: var(--dt-muted);
  font-size: 14px;
}
.hero h1 {
  font-size: clamp(42px, 6vw, 82px);
  line-height: .94;
  margin: 14px 0 12px;
}
.hero p {
  max-width: 790px;
  color: var(--dt-muted);
  font-size: 18px;
}
.pulse {
  color: var(--dt-cyan);
}
.metric-card, .source-card, .verdict-card {
  border: 1px solid var(--dt-line);
  border-radius: 8px;
  padding: 16px;
  background: var(--dt-card);
}
.intel-card {
  border: 1px solid rgba(255,255,255,.15);
  border-radius: 8px;
  padding: 18px;
  background: linear-gradient(135deg, rgba(255,255,255,.12), rgba(255,255,255,.06));
  min-height: 190px;
}
.intel-card a {
  color: #8dfff4;
  text-decoration: none;
}
.intel-title {
  font-size: 18px;
  font-weight: 800;
  line-height: 1.28;
  margin: 8px 0 8px;
}
.reliability {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 999px;
  background: rgba(255,209,102,.12);
  border: 1px solid rgba(255,209,102,.35);
  color: #ffe6a3;
  font-size: 12px;
}
.glass-row {
  border: 1px solid var(--dt-line);
  border-radius: 8px;
  padding: 14px;
  background: rgba(255,255,255,.07);
}
.verdict-card {
  border-left: 4px solid var(--dt-cyan);
}
.tiny {
  color: var(--dt-muted);
  font-size: 13px;
}
.tag {
  display: inline-block;
  padding: 4px 8px;
  margin: 3px 4px 3px 0;
  border-radius: 999px;
  background: rgba(30,227,207,.12);
  border: 1px solid rgba(30,227,207,.35);
  color: #dffffb;
  font-size: 12px;
}
.risk-high { color: #ff8aa8; font-weight: 700; }
.risk-mid { color: #ffd166; font-weight: 700; }
.risk-low { color: #8cffd5; font-weight: 700; }
.stButton > button {
  border-radius: 8px;
  border: 1px solid rgba(30,227,207,.45);
  background: linear-gradient(135deg, #1ee3cf, #ff477e);
  color: #07101d;
  font-weight: 800;
}
.stTextArea textarea, .stTextInput input {
  background: rgba(255,255,255,.08);
  color: var(--dt-text);
  border-radius: 8px;
}
</style>
"""


def render_header(language: str) -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(
        f"""
        <section class="hero">
          <div class="brand">DEBATETRIX AI <span class="pulse">LIVE INTEL</span></div>
          <h1>{t(language, "title")}</h1>
          <p>{t(language, "subtitle")}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def source_grid(region: str) -> None:
    sources = trusted_sources_by_region(region)
    for source in sources:
        st.markdown(
            f"""
            <div class="source-card">
              <strong>{source.name}</strong><br>
              <span class="tiny">{source.region} | Reliability {source.reliability}/100</span><br>
              <a href="{source.url}" target="_blank">{source.url}</a>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_intel_card(item: dict[str, object]) -> None:
    title = html.escape(str(item.get("title", "Untitled")))
    url = html.escape(str(item.get("url", "")), quote=True)
    source = html.escape(str(item.get("source_name", "Unknown source")))
    region = html.escape(str(item.get("source_region", "")))
    reliability = item.get("source_reliability", "?")
    summary = html.escape(str(item.get("summary") or "No summary available from this feed item."))
    published = html.escape(str(item.get("published_at") or "Date unavailable"))
    tags = html.escape(str(item.get("tags") or "").replace(",", " #"))
    st.markdown(
        f"""
        <div class="intel-card">
          <span class="reliability">{source} | {region} | {reliability}/100</span>
          <div class="intel-title">{title}</div>
          <p class="tiny">{summary}</p>
          <p class="tiny">Published: {published}</p>
          <span class="tag">#{tags or "fact-check"}</span><br><br>
          <a href="{url}" target="_blank">Open source</a>
        </div>
        """,
        unsafe_allow_html=True,
    )


with st.sidebar:
    st.title("Debatetrix")
    language = st.selectbox("Language", LANGUAGES, index=0)
    region = st.selectbox("Region focus", ["India", "Global"], index=0)
    mode = st.radio(
        "Mode",
        ["Fact Check", "Intel Feed", "Debate/Rivalry", "Source Library", "Transparency"],
        index=0,
    )
    st.divider()
    provider_status = get_provider_status()
    st.caption("Inference Source")
    st.info(provider_status["source"])
    st.caption(provider_status["detail"])


render_header(language)

if mode == "Fact Check":
    col_input, col_tips = st.columns([1.45, .75], gap="large")
    with col_input:
        st.subheader(t(language, "fact_check"))
        claim = st.text_area(
            t(language, "claim_label"),
            height=170,
            placeholder="Example: A viral post claims a new government scheme gives every student Rs 25,000.",
        )
        context = st.text_input(
            "Optional context",
            placeholder="Country, date, platform, people involved, or link",
        )
        analyze = st.button(t(language, "analyze"), use_container_width=True)
    with col_tips:
        st.markdown(
            """
            <div class="metric-card">
              <strong>Verification workflow</strong><br><br>
              <span class="tag">Claim extraction</span>
              <span class="tag">Evidence gaps</span>
              <span class="tag">Source routing</span>
              <span class="tag">Neutral verdict</span>
              <p class="tiny">For live evidence, add provider/API keys in environment variables. Without keys, Debatetrix runs a transparent local analysis and gives source links to verify manually.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if analyze and claim.strip():
        result = analyze_claim(claim, context=context, region=region, language=language)
        st.markdown(
            f"""
            <div class="verdict-card">
              <h3>{result.verdict}</h3>
              <p>{result.summary}</p>
              <strong>Confidence Score:</strong> {result.confidence}%<br>
              <strong>Verification Timestamp:</strong> {result.timestamp}
            </div>
            """,
            unsafe_allow_html=True,
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Status", result.status)
        c2.metric("Evidence Count", result.evidence_count)
        c3.metric("Source Count", len(result.sources))
        c4.metric("Risk", result.risk_level)

        st.subheader("Claim Breakdown")
        for item in result.claims:
            st.write(f"- **{item['type']}**: {item['text']}")

        st.subheader("Evidence Assessment")
        st.write(result.evidence_assessment)

        if result.evidence_matches:
            st.subheader("Trusted Source Evidence Candidates")
            evidence_cols = st.columns(2)
            for index, evidence in enumerate(result.evidence_matches):
                with evidence_cols[index % 2]:
                    render_intel_card(evidence)
        else:
            st.info("No matching stored evidence yet. Go to Intel Feed, fetch latest trusted-source data, then analyze again.")

        st.subheader("Recommended Trusted Sources")
        for source in result.sources:
            st.markdown(f"- [{source.name}]({source.url}) - reliability {source.reliability}/100")

        st.subheader("Transparency Panel")
        st.json(result.transparency)
    elif analyze:
        st.warning("Please enter a claim to analyze.")

elif mode == "Intel Feed":
    st.subheader("Live Fact-Check Intel Feed")
    st.write("Fetch public feed items from trusted fact-checking websites, store them in MySQL, then search them from this frontend.")

    config = get_database_config()
    db_col, fetch_col, hint_col = st.columns([.9, .9, 1.1], gap="large")
    with db_col:
        st.markdown(
            f"""
            <div class="glass-row">
              <strong>MySQL Target</strong><br>
              <span class="tiny">{config.user}@{config.host}:{config.port}/{config.database}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if not is_mysql_driver_available():
            st.error("MySQL driver missing. Run pip install -r requirements.txt")
        if st.button("Setup MySQL", use_container_width=True):
            ok, message = initialize_database()
            if ok:
                st.success(message)
            else:
                st.error(message)
    with fetch_col:
        fetch_region = st.selectbox("Fetch region", ["India", "Global", "All"], index=0)
        max_per_source = st.slider("Items per source", 2, 20, 6)
        if st.button("Fetch + Store Latest", use_container_width=True):
            with st.spinner("Fetching public feeds and saving to MySQL..."):
                items, logs = fetch_all_sources(region=fetch_region, max_per_source=max_per_source)
                inserted, message = save_fact_items(items)
            st.success(message) if inserted else st.warning(message)
            with st.expander("Fetch log"):
                st.write("\n".join(logs))
    with hint_col:
        st.markdown(
            """
            <div class="metric-card">
              <strong>How fetching works</strong><br><br>
              <span class="tag">RSS feeds</span>
              <span class="tag">No fake data</span>
              <span class="tag">MySQL dedupe</span>
              <span class="tag">Searchable cards</span>
              <p class="tiny">Some sites do not expose a reliable public feed. Those are listed as source links and can be added later with official APIs or permitted crawlers.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()
    search_col, region_col, limit_col = st.columns([1.5, .7, .55])
    search = search_col.text_input("Search stored intel", placeholder="Search claims, source names, summaries...")
    view_region = region_col.selectbox("Stored region", ["All", "India", "Global"], index=0)
    limit = limit_col.selectbox("Limit", [12, 24, 48, 96], index=1)

    rows, load_message = load_fact_items(limit=limit, search=search, region=view_region)
    if rows:
        m1, m2, m3 = st.columns(3)
        m1.metric("Stored Items Shown", len(rows))
        m2.metric("Region", view_region)
        m3.metric("MySQL", "Connected")
        card_cols = st.columns(3)
        for index, item in enumerate(rows):
            with card_cols[index % 3]:
                render_intel_card(item)
    else:
        st.info(load_message)
        st.markdown(
            f"Try fetching feeds first, or search manually on [Google Fact Check Explorer](https://toolbox.google.com/factcheck/explorer/search/{quote_plus(search or 'fact check')})."
        )

elif mode == "Debate/Rivalry":
    st.subheader(t(language, "debate"))
    left, right = st.columns(2)
    with left:
        side_a = st.text_input("Perspective / Person / Team A", placeholder="Example: Messi")
    with right:
        side_b = st.text_input("Perspective / Person / Team B", placeholder="Example: Ronaldo")
    topic = st.text_input("Topic", placeholder="Example: Who had the stronger international career?")
    if st.button("Build Neutral Debate Brief", use_container_width=True):
        brief = compare_rivals(side_a, side_b, topic, region=region)
        st.markdown(brief, unsafe_allow_html=False)

elif mode == "Source Library":
    st.subheader(t(language, "sources"))
    st.write("Curated fact-check and primary verification sources used by Debatetrix routing.")
    source_grid(region)
    with st.expander("All configured sources"):
        for src in FACT_CHECK_SOURCES:
            st.markdown(f"- [{src.name}]({src.url}) | {src.region} | {src.reliability}/100")

else:
    st.subheader("Transparency")
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.markdown(
        f"""
        <div class="verdict-card">
          <strong>Model Used:</strong> Local rules engine with optional BYOK/cloud provider<br>
          <strong>Inference Source:</strong> {provider_status["source"]}<br>
          <strong>Verification Status:</strong> Transparent; live evidence depends on configured APIs<br>
          <strong>Last Updated:</strong> {now}
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write(
        "Debatetrix does not fabricate sources. When live web/API access is not configured, it gives a cautious local assessment and points you to trusted verification sources."
    )
