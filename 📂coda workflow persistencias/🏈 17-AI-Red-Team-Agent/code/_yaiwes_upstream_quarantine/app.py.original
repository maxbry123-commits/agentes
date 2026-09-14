import streamlit as st
from openai import OpenAI
import requests
import base64
import json
import time
import uuid
from pathlib import Path
from tenacity import RetryError, retry, wait_exponential, stop_after_attempt
import os
from dotenv import load_dotenv

load_dotenv()

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Red Team Agent",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
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


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_github_contents(repo_url: str, token: str = "") -> dict:
    """Fetch repo tree + sample files from GitHub."""
    repo_url = repo_url.strip().rstrip("/")
    parts = repo_url.replace("https://github.com/", "").split("/")
    if len(parts) < 2:
        return {"error": "Invalid GitHub URL"}
    owner, repo = parts[0], parts[1]
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # Get tree
    tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
    r = requests.get(tree_url, headers=headers, timeout=15)
    if r.status_code != 200:
        return {"error": f"GitHub API error: {r.status_code} — {r.json().get('message', '')}"}

    tree = r.json().get("tree", [])
    files = [f for f in tree if f["type"] == "blob" and f.get("size", 0) < 100_000]

    # Pick interesting files (limit to 15)
    priority_ext = [".py", ".js", ".ts", ".go", ".java", ".rb", ".php",
                    ".env", ".yml", ".yaml", ".json", ".sh", ".sql", ".tf"]
    priority_names = ["Dockerfile", "docker-compose.yml", ".env", "config.py",
                      "settings.py", "auth.py", "login.py", "api.py", "routes.py",
                      "database.py", "models.py", "package.json", "requirements.txt"]

    selected = []
    for f in files:
        name = Path(f["path"]).name
        ext = Path(f["path"]).suffix
        if name in priority_names or ext in priority_ext:
            selected.append(f)
        if len(selected) >= 15:
            break

    # Fetch file contents
    content_map = {}
    for f in selected[:10]:
        content_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{f['path']}"
        cr = requests.get(content_url, headers=headers, timeout=10)
        if cr.status_code == 200:
            data = cr.json()
            try:
                content = base64.b64decode(data.get("content", "")).decode("utf-8", errors="replace")
                content_map[f["path"]] = content[:3000]  # cap per file
            except Exception:
                pass

    return {
        "owner": owner,
        "repo": repo,
        "file_tree": [f["path"] for f in files[:80]],
        "file_contents": content_map,
    }


def create_github_pr(owner: str, repo: str, token: str, new_files: dict, commit_msg: str, pr_title: str, pr_body: str) -> str:
    """Create a new branch, commit modified files, and open a PR via GitHub API."""
    if not token:
        return "Error: GitHub token is required to create a Pull Request."
        
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    base_url = f"https://api.github.com/repos/{owner}/{repo}"
    
    # 1. Get default branch
    r = requests.get(base_url, headers=headers, timeout=10)
    if r.status_code != 200:
        return f"Error getting repo info: {r.status_code}"
    default_branch = r.json().get("default_branch", "main")
    
    # 2. Get default branch SHA
    r = requests.get(f"{base_url}/git/ref/heads/{default_branch}", headers=headers, timeout=10)
    if r.status_code != 200:
        return f"Error getting base branch ref: {r.status_code}"
    base_sha = r.json()["object"]["sha"]
    
    # 3. Create a tree with updated files
    tree_elements = []
    for path, content in new_files.items():
        tree_elements.append({
            "path": path,
            "mode": "100644",
            "type": "blob",
            "content": content
        })
        
    r = requests.post(f"{base_url}/git/trees", headers=headers, json={
        "base_tree": base_sha,
        "tree": tree_elements
    }, timeout=15)
    if r.status_code != 201:
        return f"Error creating tree: {r.status_code} - {r.text}"
    new_tree_sha = r.json()["sha"]
    
    # 4. Create commit
    r = requests.post(f"{base_url}/git/commits", headers=headers, json={
        "message": commit_msg,
        "tree": new_tree_sha,
        "parents": [base_sha]
    }, timeout=10)
    if r.status_code != 201:
        return f"Error creating commit: {r.status_code}"
    new_commit_sha = r.json()["sha"]
    
    # 5. Create new branch
    new_branch = f"redteam-fix-{uuid.uuid4().hex[:6]}"
    r = requests.post(f"{base_url}/git/refs", headers=headers, json={
        "ref": f"refs/heads/{new_branch}",
        "sha": new_commit_sha
    }, timeout=10)
    if r.status_code != 201:
        return f"Error creating branch: {r.status_code}"
        
    # 6. Create PR
    r = requests.post(f"{base_url}/pulls", headers=headers, json={
        "title": pr_title,
        "body": pr_body,
        "head": new_branch,
        "base": default_branch
    }, timeout=10)
    if r.status_code != 201:
        return f"Error creating PR: {r.status_code} - {r.text}"
        
    return r.json().get("html_url", "Failed to retrieve PR URL")


def call_agent(client, model_name: str, system_prompt: str, user_prompt: str, delay: int = 15, max_tokens: int = 500) -> str:
    """Single DeepSeek API call with aggressive rate limiting and retry logic."""
    time.sleep(delay)  # 15 second minimum gap for free tier
    
    @retry(
        wait=wait_exponential(multiplier=2, min=10, max=60),
        stop=stop_after_attempt(2),  # Reduced retries
        reraise=True,
    )
    def _call():
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=max_tokens,  # Parameterized max_tokens
            temperature=0.5,  # Lower temp = cheaper
        )
        return response.choices[0].message.content
    
    try:
        return _call()
    except RetryError as e:
        last_exception = e.last_attempt.exception()
        if last_exception is not None:
            return f"Error: {type(last_exception).__name__}: {str(last_exception)}"
        return f"Error: {type(e).__name__}: {str(e)}"
    except Exception as e:
        return f"Error: {type(e).__name__}: {str(e)}"


# ── Agent prompts ─────────────────────────────────────────────────────────────

ATTACK_SYSTEM = """You are the Attack Generator Agent of an AI Red Team system.
Your job: given a codebase, generate a comprehensive list of adversarial attack scenarios.
Think like a professional penetration tester. Be specific and technical.
Output format — use these exact headers:
## ATTACK SCENARIOS
List 6-10 concrete attack scenarios with:
- Attack Name
- Vector (e.g., HTTP endpoint, env var, file upload)
- Method (e.g., SQL injection, IDOR, path traversal)
- Likelihood: LOW/MEDIUM/HIGH/CRITICAL
Focus on the actual code provided. Do not be generic."""

EXPLOIT_SYSTEM = """You are the Exploit Finder Agent of an AI Red Team system.
Your job: given code and attack scenarios, identify ACTUAL exploitable vulnerabilities.
Look for real bugs — not theoretical ones. Cite specific lines or patterns.
Output format — use these exact headers:
## VULNERABILITIES FOUND
For each vulnerability:
- CVE/CWE reference if applicable
- Vulnerable code snippet or pattern
- Exact exploitation steps
- Severity: CRITICAL/HIGH/MEDIUM/LOW/INFO
Be precise. If something is not exploitable, say why."""

IMPACT_SYSTEM = """You are the Impact Analyzer Agent of an AI Red Team system.
Your job: assess the real-world business and technical impact of found vulnerabilities.
Think about: data exposure, financial loss, reputational damage, legal liability, lateral movement.
Output format — use these exact headers:
## IMPACT ANALYSIS
Overall Risk Score: X/10
For each vulnerability:
- Business Impact
- Technical Impact
- Affected Assets
- CVSS-like Score: X.X
- Exploitability (Easy/Medium/Hard)"""

FIX_SYSTEM = """You are the Fix Suggestion Agent of an AI Red Team system.
Your job: provide concrete, code-level remediation for each vulnerability found.
Give actual code fixes, not hand-wavy advice.
Output format — use these exact headers:
## FIX RECOMMENDATIONS
For each fix:
- Priority: IMMEDIATE/SHORT-TERM/LONG-TERM
- Affected file(s)
- Root cause
- Code fix (show before/after where possible)
- Validation/test to verify the fix works"""

RETEST_SYSTEM = """You are the Re-Test Agent of an AI Red Team system.
Your job: given the original vulnerabilities and proposed fixes, simulate re-testing.
Verify fixes are complete. Find any remaining issues or new issues introduced by fixes.
Output format — use these exact headers:
## RE-TEST RESULTS
For each original vulnerability:
- Status: FIXED / PARTIALLY FIXED / NOT FIXED / NEW ISSUE INTRODUCED
- Verification method
- Residual risk
## OVERALL SECURITY POSTURE
- Before: X/10  After: X/10
- Remaining attack surface
- Recommendations for continuous security"""


def run_red_team(client, model_name, repo_data: dict, manual_code: str, placeholder_dict: dict, progress_bar, auto_pr: bool = False, github_token: str = ""):
    """Run streamlined agents with minimal API calls to respect free tier quotas."""

    # MINIMAL CONTEXT - Free tier must be highly aggressive
    if repo_data and "file_contents" in repo_data:
        # Only top 2 most important files to limit prompt size
        tree_str = "\n".join(repo_data.get("file_tree", [])[:15])
        files_str = "\n\n".join(
            [f"### {path}\n```\n{content[:400]}\n```"
             for path, content in list(repo_data["file_contents"].items())[:2]]
        )
        context = f"Repo: {repo_data['owner']}/{repo_data['repo']}\n\nFiles:\n{files_str}"
    else:
        context = f"Code:\n```\n{manual_code[:1000]}\n```"

    results = {}
    call_count = 0

    # ── Agent 1: ATTACK + EXPLOIT combined (saves 1 API call)
    progress_bar.progress(0.2, text="🔍 Analyzing vulnerabilities...")
    placeholder_dict["attack"].markdown(
        f'<div class="agent-card active"><span class="badge badge-running">▶ RUNNING</span><br>'
        f'<strong>⚔️ Attack & Exploit Analysis</strong><br><em>Scanning...</em></div>',
        unsafe_allow_html=True
    )

    combined_system = """You are a security analyst. Your job: 
1. Generate 3-4 attack scenarios for this codebase
2. Identify ACTUAL exploitable vulnerabilities
Format:
## ATTACK SCENARIOS
- [Name]: [description]

## VULNERABILITIES FOUND
- [CVE/CWE]: [details]"""

    attack_prompt = f"Analyze this codebase for vulnerabilities:\n\n{context}\n\nBe concise. Only list REAL exploitable issues."
    
    try:
        attack_exploit_output = call_agent(client, model_name, combined_system, attack_prompt)
        results["attack"] = attack_exploit_output
        results["exploit"] = attack_exploit_output
        call_count += 1
        
        placeholder_dict["attack"].markdown(
            f'<div class="agent-card done"><span class="badge badge-attack">✓ Analysis</span>'
            f'<br>{attack_exploit_output[:500]}</div>',
            unsafe_allow_html=True
        )
        placeholder_dict["exploit"].markdown(
            f'<div class="agent-card done"><span class="badge badge-exploit">✓ Vulnerabilities</span>'
            f'<br>{attack_exploit_output[500:1000]}</div>',
            unsafe_allow_html=True
        )
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        results["attack"] = error_msg
        results["exploit"] = error_msg
        placeholder_dict["attack"].markdown(f'<div class="agent-card error"><span class="badge badge-attack">✗ ERROR</span><br>{str(e)[:100]}</div>', unsafe_allow_html=True)
        placeholder_dict["exploit"].markdown(f'<div class="agent-card error"><span class="badge badge-exploit">✗ ERROR</span><br>{str(e)[:100]}</div>', unsafe_allow_html=True)

    # ── Agent 2: IMPACT + FIX combined (saves 1 API call)
    progress_bar.progress(0.5, text="💥 Assessing impact and fixes...")
    placeholder_dict["impact"].markdown(
        f'<div class="agent-card active"><span class="badge badge-running">▶ RUNNING</span><br>'
        f'<strong>💥 Impact & Fixes</strong><br><em>Processing...</em></div>',
        unsafe_allow_html=True
    )

    combined_system2 = """You are a security remediator.
1. Assess business impact (severity score X/10)
2. Provide minimal code fixes

Format:
## IMPACT: [severity score]
[brief analysis]

## FIXES
- [fix 1]
- [fix 2]"""

    impact_prompt = f"For these vulnerabilities:\n\n{attack_exploit_output[:600]}\n\nProvide impact and fixes. Be extremely concise."
    
    try:
        impact_fix_output = call_agent(client, model_name, combined_system2, impact_prompt, delay=15)
        results["impact"] = impact_fix_output
        results["fix"] = impact_fix_output
        call_count += 1
        
        placeholder_dict["impact"].markdown(
            f'<div class="agent-card done"><span class="badge badge-impact">✓ Impact</span>'
            f'<br>{impact_fix_output[:400]}</div>',
            unsafe_allow_html=True
        )
        placeholder_dict["fix"].markdown(
            f'<div class="agent-card done"><span class="badge badge-fix">✓ Fixes</span>'
            f'<br>{impact_fix_output[400:800]}</div>',
            unsafe_allow_html=True
        )
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        results["impact"] = error_msg
        results["fix"] = error_msg
        placeholder_dict["impact"].markdown(f'<div class="agent-card error"><span class="badge badge-impact">✗ ERROR</span><br>{str(e)[:100]}</div>', unsafe_allow_html=True)
        placeholder_dict["fix"].markdown(f'<div class="agent-card error"><span class="badge badge-fix">✗ ERROR</span><br>{str(e)[:100]}</div>', unsafe_allow_html=True)

    # ── Agent 3: RETEST (minimal single call)
    progress_bar.progress(0.8, text="🔄 Re-testing...")
    placeholder_dict["retest"].markdown(
        f'<div class="agent-card active"><span class="badge badge-running">▶ RUNNING</span><br>'
        f'<strong>🔄 Re-Test</strong><br><em>Verifying...</em></div>',
        unsafe_allow_html=True
    )

    retest_system = """You are a security re-tester. 
Verify if proposed fixes would resolve vulnerabilities.
Format:
## RE-TEST RESULTS
- [vuln]: FIXED / NOT FIXED"""

    retest_prompt = f"Fixes:\n{impact_fix_output[:400]}\n\nAgainst:\n{attack_exploit_output[:400]}\n\nVerify status."
    
    try:
        retest_output = call_agent(client, model_name, retest_system, retest_prompt, delay=15)
        results["retest"] = retest_output
        call_count += 1
        
        placeholder_dict["retest"].markdown(
            f'<div class="agent-card done"><span class="badge badge-retest">✓ Re-Test</span>'
            f'<br>{retest_output[:500]}</div>',
            unsafe_allow_html=True
        )
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        results["retest"] = error_msg
        placeholder_dict["retest"].markdown(f'<div class="agent-card error"><span class="badge badge-retest">✗ ERROR</span><br>{str(e)[:100]}</div>', unsafe_allow_html=True)

    # ── Agent 4: Auto PR
    if auto_pr and repo_data and github_token:
        progress_bar.progress(0.9, text="🚀 Generating Patch & PR...")
        placeholder_dict["pr"].markdown(
            f'<div class="agent-card active"><span class="badge badge-running">▶ RUNNING</span><br>'
            f'<strong>🚀 Patch & PR</strong><br><em>Generating fixes...</em></div>',
            unsafe_allow_html=True
        )

        pr_system = """You are the Auto-Patch Agent.
Generate a valid JSON object containing full repaired code for affected files based on the suggested fixes. 
Response MUST be valid JSON format:
{
  "files": [
    {"path": "exact/file/path.py", "content": "full updated code including all original unmodified parts"}
  ]
}
Return raw JSON ONLY. No markdown block backticks."""

        pr_prompt = f"Original Files:\n{context}\n\nApply these fixes:\n{impact_fix_output[:500]}\n\nReturn JSON ONLY."

        try:
            pr_output = call_agent(client, model_name, pr_system, pr_prompt, delay=15, max_tokens=2500)
            call_count += 1
            
            json_str = pr_output.strip()
            if json_str.startswith("```json"): json_str = json_str[7:-3]
            elif json_str.startswith("```"): json_str = json_str[3:-3]
            
            pr_data = json.loads(json_str)
            new_files = {f["path"]: f["content"] for f in pr_data.get("files", [])}
            
            if new_files:
                pr_url = create_github_pr(
                    owner=repo_data["owner"], 
                    repo=repo_data["repo"], 
                    token=github_token, 
                    new_files=new_files, 
                    commit_msg="Auto-fix vulnerabilities from AI Red Team", 
                    pr_title="🔴 AI Red Team: Vulnerability Auto-Fix", 
                    pr_body="This PR contains automated security fixes generated by the AI Red Team System.\n\n### Fix Details\n" + impact_fix_output[:1000]
                )
                
                if pr_url.startswith("http"):
                    results["pr"] = f"✅ Pull Request Created: {pr_url}"
                    placeholder_dict["pr"].markdown(f'<div class="agent-card done"><span class="badge badge-pr">✓ PR Created</span><br><a href="{pr_url}" target="_blank" style="color:#00ff88;">View Pull Request</a></div>', unsafe_allow_html=True)
                else:
                    results["pr"] = f"❌ PR Error: {pr_url}"
                    placeholder_dict["pr"].markdown(f'<div class="agent-card error"><span class="badge badge-pr">✗ ERROR</span><br>{pr_url}</div>', unsafe_allow_html=True)
            else:
                results["pr"] = "❌ Failed to generate any file changes."
                placeholder_dict["pr"].markdown(f'<div class="agent-card error"><span class="badge badge-pr">✗ ERROR</span><br>No valid changes generated.</div>', unsafe_allow_html=True)
                
        except Exception as e:
            results["pr"] = f"❌ PR Error: {str(e)}"
            placeholder_dict["pr"].markdown(f'<div class="agent-card error"><span class="badge badge-pr">✗ ERROR</span><br>{str(e)[:100]}</div>', unsafe_allow_html=True)
            
    elif auto_pr:
        placeholder_dict["pr"].markdown(f'<div class="agent-card error"><span class="badge badge-pr">✗ SKIPPED</span><br>Missing GitHub token or repo context.</div>', unsafe_allow_html=True)
    else:
        results["pr"] = "Auto PR disabled."
        placeholder_dict["pr"].markdown(f'<div class="agent-card done"><span class="badge badge-pr">✓ SKIPPED</span><br>Auto PR disabled.</div>', unsafe_allow_html=True)

    progress_bar.progress(1.0, text=f"✅ Complete ({call_count} API calls)")
    return results


# ── Sidebar ───────────────────────────────────────────────────────────────────

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


# ── Main Layout ───────────────────────────────────────────────────────────────

st.markdown("""
<h1>⬡ AI RED TEAM AGENT</h1>
<div class='status-banner'>
    AUTONOMOUS ADVERSARIAL TESTING SYSTEM  ·  5-AGENT PIPELINE  ·  REAL-WORLD EXPLOITABILITY FOCUS
</div>
""", unsafe_allow_html=True)

# Input area
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

# Run button
st.markdown("")
col_btn, col_clear = st.columns([2, 8])
with col_btn:
    run_btn = st.button("🚀 LAUNCH SCAN", use_container_width=True)

st.markdown("---")

# ── Agent Pipeline Display ────────────────────────────────────────────────────

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

# Results placeholders
progress_placeholder = st.empty()
results_area = st.container()

with results_area:
    st.markdown("### 📋 Assessment Results")
    ph_attack  = st.empty()
    ph_exploit = st.empty()
    ph_impact  = st.empty()
    ph_fix     = st.empty()
    ph_retest  = st.empty()
    ph_pr      = st.empty()

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


# ── Run ───────────────────────────────────────────────────────────────────────

if run_btn:
    if not api_key:
        st.error("⚠️ Please set your DEEPSEEK_API_KEY in the .env file.")
        st.stop()

    if target_mode == "GitHub Repository" and not repo_url:
        st.error("⚠️ Please enter a GitHub repository URL.")
        st.stop()

    if target_mode == "Paste Code" and not manual_code.strip():
        st.error("⚠️ Please paste some code to analyze.")
        st.stop()

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )
    model = "deepseek-chat"

    repo_data = None
    if target_mode == "GitHub Repository":
        with st.spinner("📡 Fetching repository contents..."):
            repo_data = get_github_contents(repo_url, github_token)
            if "error" in repo_data:
                st.error(f"GitHub error: {repo_data['error']}")
                st.stop()
            st.success(
                f"✅ Loaded `{repo_data['owner']}/{repo_data['repo']}` — "
                f"{len(repo_data['file_tree'])} files found, "
                f"{len(repo_data['file_contents'])} files analyzed"
            )

    progress = progress_placeholder.progress(0, text="Initializing agents...")

    placeholder_dict = {
        "attack":  ph_attack,
        "exploit": ph_exploit,
        "impact":  ph_impact,
        "fix":     ph_fix,
        "retest":  ph_retest,
        "pr":      ph_pr,
    }

    final_results = run_red_team(
        client, model, repo_data, manual_code, placeholder_dict, progress, auto_pr, github_token
    )

    # ── Summary Metrics ───────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📊 Scan Summary")

    # Quick parse for severity counts (rough heuristic)
    combined = " ".join(final_results.values()).upper()
    c_crit   = combined.count("CRITICAL")
    c_high   = combined.count("HIGH")
    c_med    = combined.count("MEDIUM")
    c_low    = combined.count("LOW")

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("🔴 Critical", c_crit)
    m2.metric("🟠 High",     c_high)
    m3.metric("🟡 Medium",   c_med)
    m4.metric("🟢 Low",      c_low)
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
