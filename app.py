import streamlit as st
import threading
import queue
import sys
from io import StringIO
from agent import build_search_agent, build_reader_agent, writer_chain, critic_chain

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Multi-Agent Research",
    page_icon="🔬",
    layout="wide"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Mono:ital@0;1&display=swap');

  html, body, [class*="css"] { font-family: 'Syne', sans-serif; }

  .stApp { background: #0c0c0f; color: #e8e6e0; }

  h1 { font-size: 2.8rem !important; font-weight: 800 !important;
       letter-spacing: -0.04em !important; color: #f0ede6 !important; }

  .tag { display: inline-block; font-family: 'DM Mono', monospace;
         font-size: 0.65rem; letter-spacing: 0.12em; text-transform: uppercase;
         background: #1e1e26; border: 1px solid #2e2e3a;
         color: #8b8fa8; padding: 3px 10px; border-radius: 3px; margin-bottom: 1rem; }

  .agent-card { background: #13131a; border: 1px solid #1f1f2e;
                border-radius: 8px; padding: 1.2rem 1.4rem; margin-bottom: 1rem; }

  .agent-card.active { border-color: #5b5fef; background: #14142a; }
  .agent-card.done   { border-color: #2a7a4f; background: #0f1f17; }

  .agent-label { font-family: 'DM Mono', monospace; font-size: 0.7rem;
                 letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 0.4rem; }

  .active .agent-label { color: #7c80ff; }
  .done   .agent-label { color: #4caf7d; }
  .idle   .agent-label { color: #44445a; }

  .result-box { background: #0f0f16; border: 1px solid #222230;
                border-radius: 6px; padding: 1rem 1.2rem;
                font-family: 'DM Mono', monospace; font-size: 0.78rem;
                color: #b0aec8; line-height: 1.7; max-height: 280px;
                overflow-y: auto; white-space: pre-wrap; }

  div[data-testid="stTextInput"] input {
    background: #13131a !important; border: 1px solid #2a2a3a !important;
    color: #e8e6e0 !important; border-radius: 6px !important;
    font-family: 'Syne', sans-serif !important; font-size: 1rem !important;
    padding: 0.7rem 1rem !important;
  }

  div[data-testid="stButton"] button {
    background: #5b5fef !important; color: #fff !important;
    border: none !important; border-radius: 6px !important;
    font-family: 'Syne', sans-serif !important; font-weight: 700 !important;
    font-size: 0.9rem !important; letter-spacing: 0.04em !important;
    padding: 0.6rem 2rem !important; transition: opacity 0.2s !important;
  }
  div[data-testid="stButton"] button:hover { opacity: 0.85 !important; }

  .final-report { background: #0f1a14; border: 1px solid #2a5a3f;
                  border-radius: 8px; padding: 1.4rem 1.6rem; color: #d4f0e0; }
  .final-report h3 { color: #4caf7d; font-size: 1rem;
                     letter-spacing: 0.08em; text-transform: uppercase; }

  .feedback-box { background: #1a1510; border: 1px solid #5a4020;
                  border-radius: 8px; padding: 1.4rem 1.6rem; color: #e8d8b0; }
  .feedback-box h3 { color: #c8943a; font-size: 1rem;
                     letter-spacing: 0.08em; text-transform: uppercase; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<div class="tag">multi-agent system</div>', unsafe_allow_html=True)
st.title("Research Pipeline")
st.markdown("Autonomous agents that search, scrape, write, and critique — end to end.")
st.divider()

# ── Input ─────────────────────────────────────────────────────────────────────
col_input, col_btn = st.columns([5, 1])
with col_input:
    topic = st.text_input("", placeholder="Enter a research topic…", label_visibility="collapsed")
with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    run = st.button("Run →")

# ── Agent status placeholders ─────────────────────────────────────────────────
def agent_card(placeholder, label: str, status: str, content: str = ""):
    css_class = {"idle": "idle", "active": "active", "done": "done"}.get(status, "idle")
    icon = {"idle": "○", "active": "◎", "done": "●"}.get(status, "○")
    body = f'<div class="result-box">{content}</div>' if content else ""
    placeholder.markdown(
        f"""<div class="agent-card {css_class}">
              <div class="agent-label">{icon} {label}</div>
              {body}
            </div>""",
        unsafe_allow_html=True,
    )

if run and topic.strip():
    st.markdown("---")
    st.markdown("#### Agent Activity")

    ph_search  = st.empty()
    ph_reader  = st.empty()
    ph_writer  = st.empty()
    ph_critic  = st.empty()

    # initialise all as idle
    for ph, label in [
        (ph_search, "01 · Search Agent"),
        (ph_reader, "02 · Reader Agent"),
        (ph_writer, "03 · Writer Chain"),
        (ph_critic, "04 · Critic Chain"),
    ]:
        agent_card(ph, label, "idle")

    state = {}

    # ── Step 1: Search agent ──────────────────────────────────────────────────
    agent_card(ph_search, "01 · Search Agent", "active", "Searching the web…")
    try:
        search_agent  = build_search_agent()
        search_result = search_agent.invoke({
            "messages": [("user", f"find recent, reliable and detailed information about: {topic}")]
        })
        state["search_result"] = search_result["messages"][-1].content
        agent_card(ph_search, "01 · Search Agent", "done", state["search_result"])
    except Exception as e:
        agent_card(ph_search, "01 · Search Agent", "done", f"Error: {e}")
        st.stop()

    # ── Step 2: Reader agent ──────────────────────────────────────────────────
    agent_card(ph_reader, "02 · Reader Agent", "active", "Scraping top URL…")
    try:
        reader_agent  = build_reader_agent()
        reader_result = reader_agent.invoke({
            "messages": [("user",
                f"based on the following search results about '{topic}', "
                f"pick the most relevant URL and scrape it for deeper content.\n\n"
                f"Search Results:\n{state['search_result']}")[:1000]]
        })
        state["scraped_content"] = reader_result["messages"][-1].content
        agent_card(ph_reader, "02 · Reader Agent", "done", state["scraped_content"])
    except Exception as e:
        agent_card(ph_reader, "02 · Reader Agent", "done", f"Error: {e}")
        st.stop()

    # ── Step 3: Writer chain ──────────────────────────────────────────────────
    agent_card(ph_writer, "03 · Writer Chain", "active", "Drafting report…")
    try:
        research_combined = (
            f"SEARCH RESULTS:\n{state['search_result']}\n\n"
            f"DETAILED SCRAPED CONTENT:\n{state['scraped_content']}"
        )
        state["report"] = writer_chain.invoke({
            "topic": topic,
            "research": research_combined
        })
        agent_card(ph_writer, "03 · Writer Chain", "done", state["report"][:500] + "…")
    except Exception as e:
        agent_card(ph_writer, "03 · Writer Chain", "done", f"Error: {e}")
        st.stop()

    # ── Step 4: Critic chain ──────────────────────────────────────────────────
    agent_card(ph_critic, "04 · Critic Chain", "active", "Evaluating report…")
    try:
        state["feedback"] = critic_chain.invoke({"report": state["report"]})
        agent_card(ph_critic, "04 · Critic Chain", "done", str(state["feedback"])[:500] + "…")
    except Exception as e:
        agent_card(ph_critic, "04 · Critic Chain", "done", f"Error: {e}")

    # ── Final outputs ─────────────────────────────────────────────────────────
    st.markdown("---")
    col_r, col_f = st.columns(2)

    with col_r:
        st.markdown(
            f'<div class="final-report"><h3>📄 Final Report</h3>{state.get("report", "")}</div>',
            unsafe_allow_html=True,
        )

    with col_f:
        st.markdown(
            f'<div class="feedback-box"><h3>🧠 Critic Feedback</h3>{state.get("feedback", "")}</div>',
            unsafe_allow_html=True,
        )

elif run and not topic.strip():
    st.warning("Please enter a research topic first.")