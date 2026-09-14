import streamlit as st
import os

def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style='text-align:center; padding: 10px 0 20px;'>
            <div style='font-family: Share Tech Mono, monospace; color: #ff2244;
                        font-size: 22px; text-shadow: 0 0 15px #ff224488;'>
                🔴 RED TEAM
            </div>
            <div style='font-family: Share Tech Mono, monospace; color: #666;
                        font-size: 10px; letter-spacing: 3px;'>
                AUTONOMOUS ADVERSARIAL AI
            </div>
        </div>
        """, unsafe_allow_html=True)

        api_key = os.getenv("DEEPSEEK_API_KEY", "")

        st.markdown("---")
        st.markdown("### 📁 Target")
        target_mode = st.selectbox("Input Mode", ["GitHub Repository", "Paste Code"])

        github_token = ""
        auto_pr = False
        if target_mode == "GitHub Repository":
            github_token = st.text_input("GitHub Token (optional for scan, REQUIRED for PR)", type="password",
                                         placeholder="ghp_...")
            auto_pr = st.checkbox("Auto-Create Pull Request for fixes")

        st.markdown("---")
        st.markdown("### ⚙️ Scan Options")
        depth = st.select_slider("Analysis Depth", ["Quick", "Standard", "Deep"], value="Standard")
        focus = st.multiselect("Focus Areas",
                               ["Injection", "Auth/AuthZ", "Secrets", "SSRF", "XXE",
                                "Insecure Deserialization", "Crypto", "Business Logic"],
                               default=["Injection", "Auth/AuthZ", "Secrets"])

        st.markdown("---")
        st.warning("⚠️ **FREE TIER NOTICE**: DeepSeek free tier has strict quotas (50 req/min). Using 3 combined API calls instead of 5 to stay within limits. For unlimited access, upgrade to a paid plan.", icon="⚠️")
        
        st.markdown("""
        <div style='font-family: Share Tech Mono, monospace; color: #444; font-size: 10px; text-align:center;'>
            AI Red Team Agent v2.0<br>
            Powered by DeepSeek (Free Tier Optimized)<br>
            3 Parallel Agent Combos · Max 3 API Calls
        </div>
        """, unsafe_allow_html=True)

    return api_key, target_mode, github_token, auto_pr, depth, focus


def render_header():
    st.markdown("""
    <h1>⬡ AI RED TEAM AGENT</h1>
    <div class='status-banner'>
        AUTONOMOUS ADVERSARIAL TESTING SYSTEM  ·  5-AGENT PIPELINE  ·  REAL-WORLD EXPLOITABILITY FOCUS
    </div>
    """, unsafe_allow_html=True)


def render_input_area(target_mode, focus, depth):
    col_input, col_info = st.columns([3, 1])

    with col_input:
        if target_mode == "GitHub Repository":
            repo_url = st.text_input(
                "GitHub Repository URL",
                placeholder="https://github.com/owner/repo",
                label_visibility="collapsed"
            )
            manual_code = ""
        else:
            manual_code = st.text_area(
                "Paste your code here",
                height=200,
                placeholder="# Paste your code, config files, or any text to analyze...",
                label_visibility="collapsed"
            )
            repo_url = ""

    with col_info:
        if focus:
            st.markdown(f"""
            <div style='background:#12121f; border:1px solid #ff224430; border-radius:4px;
                        padding:12px; font-family:Share Tech Mono,monospace; font-size:11px; color:#888;'>
                <div style='color:#ff2244; margin-bottom:6px;'>FOCUS AREAS</div>
                {'<br>'.join(['▸ ' + f for f in focus])}
                <br><br>
                <div style='color:#ff2244; margin-bottom:4px;'>DEPTH</div>
                ▸ {depth}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("")
    col_btn, col_clear = st.columns([2, 8])
    with col_btn:
        run_btn = st.button("🚀 LAUNCH SCAN", use_container_width=True)

    st.markdown("---")
    return repo_url, manual_code, run_btn


def render_agent_pipeline():
    st.markdown("### 🤖 Agent Pipeline")

    pipeline_cols = st.columns(6)
    labels = [
        ("⚔️", "Attack\nGenerator", "attack"),
        ("🔍", "Exploit\nFinder", "exploit"),
        ("💥", "Impact\nAnalyzer", "impact"),
        ("🛠️", "Fix\nSuggestion", "fix"),
        ("🔄", "Re-Test\nAgent", "retest"),
        ("🚀", "Patch &\nPR", "pr"),
    ]
    for col, (icon, label, _) in zip(pipeline_cols, labels):
        with col:
            st.markdown(f"""
            <div style='text-align:center; background:#12121f; border:1px solid #ff224420;
                        border-radius:4px; padding:12px 4px;
                        font-family:Rajdhani,sans-serif; font-size:13px; color:#666;'>
                <div style='font-size:22px;'>{icon}</div>
                <div style='color:#888; margin-top:4px; white-space:pre;'>{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("")
    return labels


def render_results_placeholders(labels):
    progress_placeholder = st.empty()
    results_area = st.container()

    with results_area:
        st.markdown("### 📋 Assessment Results")
        ph_attack = st.empty()
        ph_exploit = st.empty()
        ph_impact = st.empty()
        ph_fix = st.empty()
        ph_retest = st.empty()
        ph_pr = st.empty()

    # Idle state
    for ph, (icon, label, badge) in zip(
        [ph_attack, ph_exploit, ph_impact, ph_fix, ph_retest, ph_pr], labels
    ):
        ph.markdown(
            f'<div class="agent-card"><span class="badge badge-{badge}" '
            f'style="opacity:0.4;">{icon} {label.replace(chr(10)," ")}</span>'
            f'<br><span style="color:#444;">Waiting for scan to start...</span></div>',
            unsafe_allow_html=True
        )

    placeholder_dict = {
        "attack": ph_attack,
        "exploit": ph_exploit,
        "impact": ph_impact,
        "fix": ph_fix,
        "retest": ph_retest,
        "pr": ph_pr,
    }

    return progress_placeholder, placeholder_dict


def render_summary_metrics(final_results, repo_url):
    st.markdown("---")
    st.markdown("### 📊 Scan Summary")

    # Quick parse for severity counts (rough heuristic)
    combined = " ".join(final_results.values()).upper()
    c_crit = combined.count("CRITICAL")
    c_high = combined.count("HIGH")
    c_med = combined.count("MEDIUM")
    c_low = combined.count("LOW")

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("🔴 Critical", c_crit)
    m2.metric("🟠 High", c_high)
    m3.metric("🟡 Medium", c_med)
    m4.metric("🟢 Low", c_low)
    m5.metric("✅ Agents Run", 5)

    # Download report
    st.markdown("---")
    report_md = f"""# AI Red Team Report
Generated by AI Red Team Agent

## Target
{"Repository: " + repo_url if repo_url else "Manual Code Submission"}

---

{final_results.get('attack', '')}

---

{final_results.get('exploit', '')}

---

{final_results.get('impact', '')}

---

{final_results.get('fix', '')}

---

{final_results.get('retest', '')}

---

## Auto-Patch & PR

{final_results.get('pr', '')}
"""
    st.download_button(
        "📥 Download Full Report (Markdown)",
        data=report_md,
        file_name="redteam_report.md",
        mime="text/markdown",
    )

    st.markdown("""
    <div style='text-align:center; font-family:Share Tech Mono,monospace;
                color:#444; font-size:11px; margin-top:20px;'>
        SCAN COMPLETE ·  AI RED TEAM AGENT  ·  FOR AUTHORIZED TESTING ONLY
    </div>
    """, unsafe_allow_html=True)
