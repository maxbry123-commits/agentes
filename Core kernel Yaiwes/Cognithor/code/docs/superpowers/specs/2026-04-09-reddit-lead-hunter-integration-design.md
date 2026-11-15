# Reddit Lead Hunter — Full Cognithor Integration

**Date:** 2026-04-09
**Status:** Approved

## Problem

The Reddit Lead Hunter exists as a standalone skill in the skill-registry but is not integrated into Cognithor's runtime. Users cannot trigger it via chat, it doesn't run as a cron job, there's no UI for managing leads, and reply-posting requires manual copy-paste outside of Cognithor.

## Design

### Architecture

Three-layer system:

1. **Skill-Layer** — `.md` skill file with trigger_keywords, activated by Planner via chat
2. **Service-Layer** — `RedditLeadService` with SQLite persistence, cron integration, LLM scoring
3. **UI-Layer** — 7th Flutter tab "Leads" with pipeline view, detail sheet, reply editor, stats

Three trigger paths:
- **Chat**: "Scan Reddit for leads" → Planner matches skill → calls `reddit_scan` MCP tool
- **Cron**: Every 30 min → results sent to configured channel (Telegram/Slack/WebUI)
- **Flutter UI**: "Scan Now" button → REST call → immediate scan

### Component 1: Skill File + MCP Tools

**Skill file** `~/.cognithor/skills/reddit-lead-hunter.md` — installed from skill-registry. Trigger keywords: Reddit, Lead, Leads scannen, Social Listening, Reddit Scan. Body instructs Planner to use the MCP tools.

**3 new MCP tools** in `src/jarvis/mcp/reddit_tools.py`:

| Tool | Description | Parameters |
|------|------------|------------|
| `reddit_scan` | Scan configured subreddits, score posts, save leads | `subreddits?: list`, `min_score?: int` |
| `reddit_reply` | Post/clipboard a reply draft | `lead_id: str`, `mode: "clipboard"\|"browser"\|"auto"` |
| `reddit_leads` | List current leads with filters | `status?: str`, `min_score?: int`, `limit?: int` |

Tools call `RedditLeadService` — no direct Reddit access in MCP layer.

### Component 2: RedditLeadService

**`src/jarvis/social/reddit_lead_service.py`** — new module under `social/`.

**SQLite Schema** (SQLCipher encrypted):

```sql
CREATE TABLE leads (
    id            TEXT PRIMARY KEY,
    post_id       TEXT UNIQUE NOT NULL,
    subreddit     TEXT NOT NULL,
    title         TEXT NOT NULL,
    body          TEXT DEFAULT '',
    url           TEXT NOT NULL,
    author        TEXT DEFAULT '',
    created_utc   REAL DEFAULT 0,
    upvotes       INTEGER DEFAULT 0,
    num_comments  INTEGER DEFAULT 0,
    intent_score  INTEGER DEFAULT 0,
    score_reason  TEXT DEFAULT '',
    reply_draft   TEXT DEFAULT '',
    reply_final   TEXT DEFAULT '',
    status        TEXT DEFAULT 'new',
    replied_at    REAL DEFAULT 0,
    detected_at   REAL NOT NULL,
    content_hash  TEXT DEFAULT '',
    scan_id       TEXT DEFAULT ''
);

CREATE TABLE lead_scans (
    id              TEXT PRIMARY KEY,
    started_at      REAL NOT NULL,
    finished_at     REAL DEFAULT 0,
    posts_checked   INTEGER DEFAULT 0,
    leads_found     INTEGER DEFAULT 0,
    subreddits      TEXT DEFAULT '',
    trigger         TEXT DEFAULT ''
);
```

**Status workflow:** `new` → `reviewed` → `replied` → `archived` (or `new` → `archived` if irrelevant)

**Service methods:**
- `scan(subreddits, min_score, trigger) → ScanResult`
- `get_leads(status, min_score, limit, offset) → list[Lead]`
- `get_lead(id) → Lead`
- `update_lead(id, status?, reply_final?) → Lead`
- `post_reply(id, mode) → ReplyResult`
- `get_stats() → LeadStats`
- `get_scan_history(limit) → list[ScanSummary]`

**Reddit access:** httpx GET to public JSON feeds (`/r/{sub}/new.json`). No API key needed. Rate limit: 1s between subreddits.

**LLM integration:** Uses Cognithor's `UnifiedLLMClient` via the gateway's `llm_fn`. Intent scoring and reply drafting use the same prompt templates as the standalone skill.

### Component 3: Reply Posting (Hybrid)

**Mode: clipboard (default)**
1. Copy reply draft to system clipboard
2. Open post URL in default browser (`webbrowser.open`)
3. Desktop notification: "Reply copied — Ctrl+V to paste"

**Mode: browser**
1. Open post URL in default browser
2. Copy reply draft to clipboard

**Mode: auto (power feature, explicit opt-in)**
1. Playwright browser starts (reuses `BrowserAgent` infrastructure)
2. Navigate to post URL
3. Find comment box (`browse_click` on reply button)
4. Fill draft (`browse_fill`)
5. **Approval dialog**: Gateway shows "Post this reply?" with draft text
6. After approval: submit click
7. Lead status → `replied`, `replied_at` = now

**Prerequisite for auto-post:** One-time Reddit login in Playwright browser. Cookies persist.

### Component 4: Cron Integration

Registration in `gateway/phases/advanced.py`:

```python
cron_engine.add_runtime_job(CronJob(
    name="reddit_lead_scan",
    schedule="*/30 * * * *",
    prompt="[CRON:reddit_lead_scan] Scan Reddit for leads",
    channel=config.default_channel or "webui",
    enabled=config.social.reddit_scan_enabled,
))
```

Cron triggers normal PGE loop → skill matched → `reddit_scan` tool called → leads saved → notification to configured channel.

**Notification format:**
```
🎯 3 new Reddit leads found

r/LocalLLaMA | Score 85 | "Fine-tuning for search-vs-memory gating?"
r/SaaS | Score 72 | "Looking for an AI assistant framework"

→ Details in the Leads tab
```

### Component 5: REST API

6 new endpoints:

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/leads/scan` | Trigger manual scan |
| `GET` | `/api/v1/leads` | List leads with filter/pagination |
| `GET` | `/api/v1/leads/{id}` | Lead detail |
| `PATCH` | `/api/v1/leads/{id}` | Update status/reply draft |
| `POST` | `/api/v1/leads/{id}/reply` | Post reply (mode param) |
| `GET` | `/api/v1/leads/stats` | Stats + scan history |

### Component 6: Flutter Leads Tab (7th Screen)

**Navigation:** New tab in `main_shell.dart` after Kanban. Icon: `Icons.track_changes`, label: "Leads".

**Screen structure:**
- Stats bar: counts per status (New / Reviewed / Replied / Archived)
- Filter row: status dropdown, min-score slider, search field
- Lead cards: score stars, subreddit badge, title, author, age, action buttons
- Detail bottom-sheet: full post text, score reasoning, editable reply draft, action buttons

**Lead Detail Sheet:**
- Post title + body (scrollable)
- Intent score with star rating + LLM reasoning
- Reply draft (editable TextField)
- Actions: "Open on Reddit", "Copy Reply", "Post Reply (Auto)"
- Status chips: New → Reviewed → Replied → Archive

**Config Dialog (gear icon):**
- Subreddit list (editable)
- Min-score slider
- Scan interval
- Auto-scan toggle
- Product description
- Reply tone

**LeadsProvider:**
- Polls `/api/v1/leads` every 30s
- `scanNow()`, `updateLead()`, `postReply()`
- Filter/sort by score, status, subreddit

### Component 7: Config Extension

New section in `config.py`:

```python
class SocialConfig(BaseModel):
    reddit_scan_enabled: bool = False
    reddit_subreddits: list[str] = ["LocalLLaMA", "SaaS"]
    reddit_min_score: int = 60
    reddit_scan_interval_minutes: int = 30
    reddit_product_name: str = ""
    reddit_product_description: str = ""
    reddit_reply_tone: str = "helpful, technically credible, no sales pitch"
    reddit_auto_post: bool = False
```

### Data Flow

```
User: "Scan Reddit"     Cron (30min)     Flutter: "Scan Now"
         |                    |                    |
         v                    v                    v
    Planner matches     CronEngine fires    POST /leads/scan
    skill keywords      IncomingMessage           |
         |                    |                    |
         v                    v                    v
    reddit_scan MCP --> RedditLeadService.scan()
                              |
                    +---------+----------+
                    v         v          v
              Reddit JSON   LLM Score   SQLite Save
              (httpx GET)   (Unified)   (leads table)
                                             |
                              +--------------+
                              v              v
                         Notification    Flutter UI
                         (Telegram/      (LeadsProvider
                          Slack/WebUI)    polls API)
```

### Files to Create/Modify

| File | Change |
|------|--------|
| `src/jarvis/social/__init__.py` | **New** package |
| `src/jarvis/social/reddit_lead_service.py` | **New** — core service |
| `src/jarvis/social/reddit_reply.py` | **New** — reply posting |
| `src/jarvis/mcp/reddit_tools.py` | **New** — 3 MCP tools |
| `src/jarvis/channels/config_routes.py` | 6 REST endpoints |
| `src/jarvis/config.py` | SocialConfig section |
| `src/jarvis/gateway/phases/advanced.py` | Init service + cron |
| `data/procedures/reddit-lead-hunter.md` | Skill file |
| `flutter_app/lib/providers/leads_provider.dart` | **New** |
| `flutter_app/lib/screens/leads_screen.dart` | **New** — 7th tab |
| `flutter_app/lib/widgets/leads/lead_card.dart` | **New** |
| `flutter_app/lib/widgets/leads/lead_detail_sheet.dart` | **New** |
| `flutter_app/lib/widgets/leads/leads_config_dialog.dart` | **New** |
| `flutter_app/lib/screens/main_shell.dart` | Add 7th tab |
| `flutter_app/lib/services/api_client.dart` | 6 API methods |
| `flutter_app/lib/l10n/app_{en,de,zh,ar}.arb` | ~20 i18n keys |
| `tests/test_social/test_reddit_lead_service.py` | **New** |
| `tests/test_mcp/test_reddit_tools.py` | **New** |

### Not In Scope (saved for later)

- Reddit OAuth (public JSON feed sufficient for v1)
- Multi-product support (one product per config)
- Sentiment analysis beyond intent score
- Competitor tracking
