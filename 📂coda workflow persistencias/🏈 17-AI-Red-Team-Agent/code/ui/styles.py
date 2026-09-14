import streamlit as st

def load_css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Rajdhani', sans-serif;
    background-color: #0a0a0f;
    color: #e0e0e0;
}

.stApp {
    background: linear-gradient(135deg, #0a0a0f 0%, #0f0f1a 50%, #0a0a0f 100%);
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0d0d18 !important;
    border-right: 1px solid #ff003320;
}

/* Title */
h1 {
    font-family: 'Share Tech Mono', monospace !important;
    color: #ff2244 !important;
    text-shadow: 0 0 20px #ff224488, 0 0 40px #ff224444;
    letter-spacing: 2px;
}

h2, h3 {
    font-family: 'Rajdhani', sans-serif !important;
    color: #ff4466 !important;
    font-weight: 700;
}

/* Cards */
.agent-card {
    background: linear-gradient(135deg, #12121f 0%, #1a1a2e 100%);
    border: 1px solid #ff224430;
    border-left: 3px solid #ff2244;
    border-radius: 4px;
    padding: 16px 20px;
    margin: 10px 0;
    font-family: 'Share Tech Mono', monospace;
    font-size: 13px;
    line-height: 1.7;
    color: #c8c8d4;
}

.agent-card.active {
    border-left-color: #00ff88;
    box-shadow: 0 0 15px #00ff8820;
    animation: pulse-border 1.5s infinite;
}

.agent-card.done {
    border-left-color: #00aaff;
    opacity: 0.85;
}

.agent-card.error {
    border-left-color: #ff4400;
    box-shadow: 0 0 10px #ff440020;
}

@keyframes pulse-border {
    0%, 100% { box-shadow: 0 0 10px #00ff8820; }
    50% { box-shadow: 0 0 25px #00ff8860; }
}

/* Agent badges */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 2px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.badge-attack   { background: #ff2244; color: #fff; }
.badge-exploit  { background: #ff6600; color: #fff; }
.badge-impact   { background: #cc00ff; color: #fff; }
.badge-fix      { background: #00aaff; color: #fff; }
.badge-retest   { background: #00cc66; color: #fff; }
.badge-pr       { background: #2266ff; color: #fff; }
.badge-running  { background: #ffcc00; color: #000; }

/* Severity pills */
.sev-critical { color: #ff0033; font-weight: 700; }
.sev-high     { color: #ff6600; font-weight: 700; }
.sev-medium   { color: #ffcc00; font-weight: 700; }
.sev-low      { color: #00cc66; font-weight: 700; }

/* Inputs */
.stTextInput input, .stTextArea textarea {
    background: #12121f !important;
    border: 1px solid #ff224440 !important;
    color: #e0e0e0 !important;
    font-family: 'Share Tech Mono', monospace !important;
    border-radius: 2px !important;
}

.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #ff2244 !important;
    box-shadow: 0 0 8px #ff224440 !important;
}

/* Buttons */
.stButton button {
    background: linear-gradient(135deg, #ff2244, #cc0033) !important;
    color: white !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    letter-spacing: 2px !important;
    text-transform: uppercase;
    border: none !important;
    border-radius: 2px !important;
    padding: 8px 24px !important;
    box-shadow: 0 0 15px #ff224460 !important;
    transition: all 0.2s !important;
}
.stButton button:hover {
    box-shadow: 0 0 25px #ff224480 !important;
    transform: translateY(-1px) !important;
}

/* Expanders */
.streamlit-expanderHeader {
    background: #12121f !important;
    border: 1px solid #ff224420 !important;
    color: #e0e0e0 !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 600 !important;
}

/* Progress bar */
.stProgress > div > div {
    background: linear-gradient(90deg, #ff2244, #ff6600) !important;
}

/* Metric */
[data-testid="metric-container"] {
    background: #12121f;
    border: 1px solid #ff224430;
    border-radius: 4px;
    padding: 12px;
}

/* Divider */
hr { border-color: #ff224420 !important; }

/* Selectbox */
[data-baseweb="select"] > div {
    background: #12121f !important;
    border-color: #ff224440 !important;
    color: #e0e0e0 !important;
}

/* Code blocks */
code {
    background: #0d0d18 !important;
    color: #00ff88 !important;
    font-family: 'Share Tech Mono', monospace !important;
    border: 1px solid #00ff8820 !important;
}

pre code {
    font-size: 12px !important;
}

/* Status banner */
.status-banner {
    background: linear-gradient(135deg, #12121f, #1a1a2e);
    border: 1px solid #ff224430;
    border-top: 2px solid #ff2244;
    border-radius: 4px;
    padding: 12px 20px;
    text-align: center;
    font-family: 'Share Tech Mono', monospace;
    font-size: 13px;
    color: #888;
    margin-bottom: 20px;
}

.terminal-output {
    background: #080810;
    border: 1px solid #1a1a30;
    border-radius: 4px;
    padding: 16px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 12px;
    color: #00ff88;
    max-height: 300px;
    overflow-y: auto;
    line-height: 1.8;
}

.scan-header {
    font-family: 'Share Tech Mono', monospace;
    color: #ff2244;
    font-size: 11px;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 4px;
}
</style>
""", unsafe_allow_html=True)
