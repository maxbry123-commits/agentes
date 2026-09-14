# Cross-Platform Social Listening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend social listening from Reddit-only to Reddit + Hacker News + Discord with unified Lead model, separate scanners, and 2 new MCP tools.

**Architecture:** Add `platform` field to existing Lead model + store. Create HackerNewsScanner (Firebase+Algolia, zero auth) and DiscordScanner (bot token, httpx). Add `social_scan` and `social_leads` unified MCP tools. Wire into gateway + config. Existing reddit_tools.py unchanged.

**Tech Stack:** httpx (existing), asyncio, SQLite (existing store), existing LLM provider abstraction

---

### Task 1: Lead Model + Store Migration

**Files:**
- Modify: `src/cognithor/social/models.py`
- Modify: `src/cognithor/social/store.py`

**Scope:** Add `platform`, `platform_id`, `platform_url` fields to Lead. Migrate store with ALTER TABLE. Make queries platform-aware.

- [ ] **Step 1:** Add 3 fields to `Lead` dataclass in models.py: `platform: str = "reddit"`, `platform_id: str = ""`, `platform_url: str = ""`
- [ ] **Step 2:** In store.py, add migration in `_init_db()`: `ALTER TABLE leads ADD COLUMN platform TEXT DEFAULT 'reddit'`, `ALTER TABLE leads ADD COLUMN platform_id TEXT DEFAULT ''`, `ALTER TABLE leads ADD COLUMN platform_url TEXT DEFAULT ''`, `CREATE INDEX IF NOT EXISTS idx_leads_platform ON leads(platform)`. Wrap each ALTER in try/except (column may already exist).
- [ ] **Step 3:** Update `_insert_lead()` to include platform/platform_id/platform_url in INSERT
- [ ] **Step 4:** Update `_row_to_lead()` to read platform/platform_id/platform_url from row
- [ ] **Step 5:** Add `platform` filter to `get_leads()`: if platform param given, add `WHERE platform = ?`
- [ ] **Step 6:** Run existing Reddit tests to verify no regression
- [ ] **Step 7:** Commit: `feat(social): add platform field to Lead model + store migration`

---

### Task 2: HackerNewsScanner

**Files:**
- Create: `src/cognithor/social/hn_scanner.py`
- Create: `tests/social/test_hn_scanner.py`

**Scope:** Firebase API for story IDs + details, Algolia for search. LLM scoring adapted for HN culture. No reply drafts.

- [ ] **Step 1:** Write `test_hn_scanner.py`:
  - `test_fetch_stories_top`: mock Firebase topstories.json + item fetches → returns list of dicts with id, title, url, score, descendants, time, by
  - `test_fetch_stories_empty`: mock empty response → empty list
  - `test_search_stories`: mock Algolia search → returns list with objectID, title, points
  - `test_score_story`: mock LLM returns `{"score": 75, "reasoning": "relevant"}` → (75, "relevant")
  - `test_score_story_low`: mock LLM returns low score → filtered out in scan
  - `test_scan_lifecycle`: mock fetch + score → ScanResult with correct leads_found count
  - `test_platform_field`: leads created with platform="hackernews"

- [ ] **Step 2:** Implement `HackerNewsScanner`:
  - `HN_API = "https://hacker-news.firebaseio.com/v0"`, `ALGOLIA_API = "https://hn.algolia.com/api/v1"`
  - `__init__(llm_fn=None)` — stores llm_fn, creates httpx client config
  - `async fetch_stories(category="top", limit=30)` — GET topstories/newstories/beststories.json, then batch GET item/{id}.json with 2s delay, return dicts
  - `async search_stories(query, limit=20)` — GET Algolia search?query=...&tags=story
  - `async score_story(story, config)` — HN-specific scoring prompt, parse JSON response
  - `async scan(product_name, product_description, categories, min_score)` — fetch→score→return ScanResult
  - HN scoring prompt emphasizes technical depth, no marketing language

- [ ] **Step 3:** Run tests, verify pass
- [ ] **Step 4:** Commit: `feat(social): add Hacker News scanner`

---

### Task 3: DiscordScanner

**Files:**
- Create: `src/cognithor/social/discord_scanner.py`
- Create: `tests/social/test_discord_scanner.py`

**Scope:** Fetch message history via Discord REST API (httpx, no discord.py dependency). Bot token required. LLM scoring for messages.

- [ ] **Step 1:** Write `test_discord_scanner.py`:
  - `test_fetch_messages`: mock Discord API response → list of message dicts with id, content, author, timestamp
  - `test_fetch_messages_no_token`: raises ValueError("Discord bot token required")
  - `test_score_message`: mock LLM → (score, reasoning)
  - `test_scan_channels`: mock fetch + score → ScanResult with leads
  - `test_platform_field`: leads have platform="discord"
  - `test_rate_limiting`: verify 1s delay between channel fetches
  - `test_empty_channel`: returns empty list gracefully

- [ ] **Step 2:** Implement `DiscordScanner`:
  - `DISCORD_API = "https://discord.com/api/v10"`
  - `__init__(bot_token, llm_fn=None)` — validate token not empty
  - `async fetch_messages(channel_id, limit=100)` — GET /channels/{id}/messages with Bot auth header
  - `async score_message(message, config)` — Discord-specific scoring prompt
  - `async scan(channel_ids, product_name, product_description, min_score)` — iterate channels, fetch→score→ScanResult
  - 1-second delay between channel requests

- [ ] **Step 3:** Run tests, verify pass
- [ ] **Step 4:** Commit: `feat(social): add Discord scanner`

---

### Task 4: Unified MCP Tools

**Files:**
- Create: `src/cognithor/mcp/social_tools.py`
- Modify: `src/cognithor/core/gatekeeper.py` — add social_scan, social_leads to GREEN

**Scope:** 2 new tools: `social_scan` (dispatches to correct scanner), `social_leads` (unified listing with platform filter).

- [ ] **Step 1:** Implement `social_tools.py`:
  - `register_social_tools(mcp_client, lead_service)` — registers 2 tools
  - `social_scan(platform, product, subreddits, categories, channel_ids, min_score)`:
    - If platform="" → scan all enabled platforms
    - If "reddit" → delegate to lead_service.scan()
    - If "hackernews" → delegate to lead_service.scan_hackernews()
    - If "discord" → delegate to lead_service.scan_discord()
    - Return JSON summary
  - `social_leads(platform, status, min_score, limit)`:
    - Delegate to lead_service.get_leads(platform=platform, ...)
    - Return JSON list
  - Both tools use proper JSON Schema `input_schema` with `"type": "object", "properties": {...}`

- [ ] **Step 2:** Add `"social_scan"` and `"social_leads"` to Gatekeeper GREEN list

- [ ] **Step 3:** Create `tests/social/test_social_tools.py`:
  - `test_social_scan_reddit`: platform="reddit" dispatches correctly
  - `test_social_scan_hackernews`: dispatches to hn scanner
  - `test_social_scan_all`: empty platform scans all enabled
  - `test_social_leads_filter`: platform filter works
  - `test_social_leads_no_filter`: returns all platforms

- [ ] **Step 4:** Run tests, verify pass
- [ ] **Step 5:** Commit: `feat(social): add unified social_scan and social_leads MCP tools`

---

### Task 5: Service Extension + Config + Gateway

**Files:**
- Modify: `src/cognithor/social/service.py`
- Modify: `src/cognithor/config.py`
- Modify: `src/cognithor/gateway/gateway.py`

**Scope:** Extend RedditLeadService with HN/Discord scan methods. Add config fields. Wire scanners in gateway.

- [ ] **Step 1:** Add to `SocialConfig` in config.py:
  ```python
  hn_enabled: bool = Field(default=False)
  hn_categories: list[str] = Field(default_factory=lambda: ["top", "new"])
  hn_min_score: int = Field(default=60, ge=0, le=100)
  hn_scan_interval_minutes: int = Field(default=60, ge=10, le=1440)
  discord_scanner_enabled: bool = Field(default=False)
  discord_scan_channels: list[str] = Field(default_factory=list)
  discord_min_score: int = Field(default=60, ge=0, le=100)
  discord_scan_interval_minutes: int = Field(default=30, ge=5, le=1440)
  ```

- [ ] **Step 2:** Add to `RedditLeadService` in service.py:
  - `_hn_scanner: HackerNewsScanner | None = None` attribute
  - `_discord_scanner: DiscordScanner | None = None` attribute
  - `async def scan_hackernews(self, categories=None, min_score=60) -> ScanResult`
  - `async def scan_discord(self, channel_ids=None, min_score=60) -> ScanResult`
  - `async def scan_all(self, min_score=60) -> dict[str, ScanResult]`
  - Modify `get_leads()` to accept optional `platform` parameter

- [ ] **Step 3:** In gateway.py post-init, after Reddit wiring, add:
  ```python
  if getattr(social_cfg, "hn_enabled", False):
      from cognithor.social.hn_scanner import HackerNewsScanner
      self._reddit_lead_service._hn_scanner = HackerNewsScanner(llm_fn=_reddit_llm_fn)
      log.info("hn_scanner_initialized")
  
  if getattr(social_cfg, "discord_scanner_enabled", False):
      _discord_token = os.environ.get("COGNITHOR_DISCORD_TOKEN", "")
      if _discord_token:
          from cognithor.social.discord_scanner import DiscordScanner
          self._reddit_lead_service._discord_scanner = DiscordScanner(
              bot_token=_discord_token, llm_fn=_reddit_llm_fn
          )
          log.info("discord_scanner_initialized")
  ```
  Also register social_tools:
  ```python
  from cognithor.mcp.social_tools import register_social_tools
  register_social_tools(self._mcp_client, self._reddit_lead_service)
  ```

- [ ] **Step 4:** Commit: `feat(social): wire HN + Discord into service, config, and gateway`

---

### Task 6: Flutter UI + Final Verification

**Files:**
- Modify: `flutter_app/lib/providers/reddit_leads_provider.dart`
- Modify: `flutter_app/lib/screens/reddit_leads_screen.dart`
- Modify: `flutter_app/lib/l10n/app_en.arb`, `app_de.arb`

**Scope:** Platform filter in Leads screen, i18n keys, config UI for HN/Discord.

- [ ] **Step 1:** Add `platform` field to `RedditLead` model in provider
- [ ] **Step 2:** Add platform filter dropdown to leads screen header (All / Reddit / HN / Discord)
- [ ] **Step 3:** Add i18n keys: `hackerNews`, `discord`, `allPlatforms`, `platformFilter`
- [ ] **Step 4:** Add HN + Discord config sections in social_page.dart (enable toggle, interval, min score)
- [ ] **Step 5:** `flutter build web --release`
- [ ] **Step 6:** `ruff format src/cognithor/social/ src/cognithor/mcp/social_tools.py`
- [ ] **Step 7:** `ruff check src/ tests/ --select=F821,F811 --no-fix`
- [ ] **Step 8:** `pytest tests/social/ -v` — ALL PASS
- [ ] **Step 9:** Commit: `feat(social): complete cross-platform social listening`
