# 🔴 AI Red Team Agent

An autonomous adversarial testing system powered by Claude claude-sonnet-4-20250514, with a Streamlit UI.

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
streamlit run app.py
```

### 3. Open in browser
Streamlit will open automatically at `http://localhost:8501`

---

## 🤖 Agent Pipeline

| Agent | Role |
|-------|------|
| ⚔️ **Attack Generator** | Generates adversarial attack scenarios from the codebase |
| 🔍 **Exploit Finder** | Identifies real, exploitable vulnerabilities with specific code references |
| 💥 **Impact Analyzer** | Assesses business + technical impact and CVSS-like scoring |
| 🛠️ **Fix Suggestion** | Provides concrete, code-level remediation with before/after examples |
| 🔄 **Re-Test Agent** | Validates fixes and identifies residual risk |

---

## ⚙️ Configuration (Sidebar)

- **Anthropic API Key** — Required. Get one at [console.anthropic.com](https://console.anthropic.com)
- **GitHub Token** — Optional. Required for private repos. Set `repo` scope.
- **Analysis Depth** — Quick / Standard / Deep
- **Focus Areas** — Injection, Auth/AuthZ, Secrets, SSRF, XXE, etc.

---

## 📁 Input Modes

### GitHub Repository
Paste a public GitHub URL like:
```
https://github.com/owner/repo
```
The app fetches up to 10 priority files (Python, JS, config, auth, routes, etc.) for analysis.

### Paste Code
Paste any code, config, or text directly into the text area.

---

## 📥 Output

- **Live agent output** — Each agent streams its results as it completes
- **Summary metrics** — Critical / High / Medium / Low counts
- **Download Report** — Full Markdown report downloadable at the end

---

## ⚠️ Disclaimer

For **authorized security testing only**. Do not use against systems you don't own or have explicit permission to test.
