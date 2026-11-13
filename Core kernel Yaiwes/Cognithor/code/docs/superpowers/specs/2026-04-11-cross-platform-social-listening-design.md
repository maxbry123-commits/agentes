# Cross-Platform Social Listening — Design Spec

**Goal:** Extend Cognithor's social listening from Reddit-only to Reddit + Hacker News + Discord. Unified Lead model, separate scanners per platform, 2 new MCP tools, shared LLM scoring.

**Package:** Extends `src/cognithor/social/` with new scanner files. No rename of existing files.

---

## 1. Architecture (Hybrid)

**Shared across platforms:**
- `Lead` model gains `platform` field (`"reddit"` | `"hackernews"` | `"discord"`)
- `LeadStore` stores all leads in same tables with platform-aware queries
- LLM scoring prompt adapted per platform via context injection
- Flutter Leads-Tab shows all platforms with filter dropdown
- 2 new unified MCP tools: `social_scan`, `social_leads`

**Separate per platform:**
- `RedditScanner` — existing, unchanged
- `HackerNewsScanner` — Firebase + Algolia API, zero auth
- `DiscordScanner` — Bot-token based, message history fetch

---

## 2. New/Modified Files

### New files
```
src/cognithor/social/hn_scanner.py       # HackerNewsScanner
src/cognithor/social/discord_scanner.py  # DiscordScanner
src/cognithor/mcp/social_tools.py       # 2 unified MCP tools (social_scan, social_leads)
tests/social/test_hn_scanner.py
tests/social/test_discord_scanner.py
tests/social/test_social_tools.py
```

### Modified files
```
src/cognithor/social/models.py    — Lead gets platform, platform_id, platform_url fields
src/cognithor/social/store.py     — platform-aware queries, migration for existing leads
src/cognithor/social/service.py   — RedditLeadService becomes multi-platform orchestrator
src/cognithor/config.py           — SocialConfig gets HN + Discord fields
src/cognithor/gateway/gateway.py  — Wire HN/Discord scanners in post-init
src/cognithor/core/gatekeeper.py  — Add social_scan, social_leads to GREEN
```

### NOT modified
```
src/cognithor/mcp/reddit_tools.py — stays as-is (6 reddit-specific tools unchanged)
```

---

## 3. Lead Model Extension (`models.py`)

Add 3 fields to the existing `Lead` dataclass:

```python
platform: str = "reddit"       # "reddit" | "hackernews" | "discord"
platform_id: str = ""          # Original ID on the platform (HN story ID, Discord message ID)
platform_url: str = ""         # Direct link to original post/message
```

Store migration: `ALTER TABLE leads ADD COLUMN platform TEXT DEFAULT 'reddit'` + `platform_id` + `platform_url`. Existing Reddit leads get `platform='reddit'` automatically via default.

---

## 4. HackerNewsScanner (`hn_scanner.py`)

### APIs used
- **Firebase**: `https://hacker-news.firebaseio.com/v0/` — story IDs + details, zero auth
- **Algolia**: `https://hn.algolia.com/api/v1/` — full-text search, zero auth

### Interface

```python
class HackerNewsScanner:
    def __init__(self, llm_fn: Callable | None = None) -> None: ...
    
    async def fetch_stories(
        self,
        category: str = "top",  # "top" | "new" | "best" | "ask" | "show"
        limit: int = 30,
    ) -> list[dict]: ...
    
    async def search_stories(
        self,
        query: str,
        limit: int = 20,
    ) -> list[dict]: ...
    
    async def score_story(
        self,
        story: dict,
        config: ScanConfig,
    ) -> tuple[int, str]: ...
    
    async def scan(
        self,
        product_name: str,
        product_description: str = "",
        categories: list[str] | None = None,
        min_score: int = 60,
    ) -> ScanResult: ...
```

### Scoring prompt (adapted for HN culture)

```
You are a B2B lead qualification expert for Hacker News.
PRODUCT: {product_name}
DESCRIPTION: {product_description}

HACKER NEWS STORY:
Title: {title}
URL: {url}
Points: {points}
Comments: {num_comments}

Score 0-100:
- 0-20: No relation to product
- 21-40: Vaguely related topic
- 41-60: Relevant discussion, no buying signal
- 61-80: Clear problem our product solves
- 81-100: Active search for exactly this solution

IMPORTANT: Hacker News values technical depth, not marketing.
Only score high if the post genuinely needs this product.

Reply ONLY: {"score": <int>, "reasoning": "<1 sentence>"}
```

### No reply drafts
HN culture is anti-marketing. Instead of drafts, the scanner produces **insight reports**: "This topic is trending, here's how Cognithor is relevant." The user decides whether/how to engage.

### Rate limiting
- 2-second delay between Firebase item fetches
- Algolia: no documented limit, max 1 request/second as courtesy

---

## 5. DiscordScanner (`discord_scanner.py`)

### Requirements
- Bot token from config (`COGNITHOR_DISCORD_TOKEN` — already supported by existing Discord channel)
- Channel IDs to monitor (user configures in config.yaml or Flutter UI)
- `discord.py` or raw HTTP via httpx (use httpx to avoid heavy dependency)

### Interface

```python
class DiscordScanner:
    DISCORD_API = "https://discord.com/api/v10"
    
    def __init__(
        self,
        bot_token: str,
        llm_fn: Callable | None = None,
    ) -> None: ...
    
    async def fetch_messages(
        self,
        channel_id: str,
        limit: int = 100,
    ) -> list[dict]: ...
    
    async def score_message(
        self,
        message: dict,
        config: ScanConfig,
    ) -> tuple[int, str]: ...
    
    async def scan(
        self,
        channel_ids: list[str],
        product_name: str,
        product_description: str = "",
        min_score: int = 60,
    ) -> ScanResult: ...
```

### API calls (raw httpx, no discord.py needed)
```
GET /channels/{channel_id}/messages?limit=100
Headers: Authorization: Bot {token}
```

### Scoring prompt

```
You are a B2B lead qualification expert for Discord communities.
PRODUCT: {product_name}
DESCRIPTION: {product_description}

DISCORD MESSAGE:
Server: {guild_name}
Channel: #{channel_name}
Author: {author}
Content: {content}

Score 0-100 for purchase/adoption intent.
Reply ONLY: {"score": <int>, "reasoning": "<1 sentence>"}
```

### Rate limiting
- Discord API: 50 requests/second per bot token
- Cognithor: 1 request/second per channel (conservative)

---

## 6. Unified MCP Tools (`social_tools.py`)

### `social_scan`

```python
async def social_scan(
    platform: str = "",          # "reddit" | "hackernews" | "discord" | "" (all enabled)
    product: str = "",           # Override product name
    subreddits: str = "",        # Reddit-specific
    categories: str = "",        # HN-specific: "top,new,best"
    channel_ids: str = "",       # Discord-specific
    min_score: int = 0,
) -> str:
```

Dispatches to the correct scanner based on `platform`. If empty, scans all enabled platforms.

Input schema (JSON Schema format for Planner visibility):
```json
{
    "type": "object",
    "properties": {
        "platform": {"type": "string", "description": "reddit, hackernews, discord, or empty for all"},
        "product": {"type": "string", "description": "Product name to search for"},
        "subreddits": {"type": "string", "description": "Reddit: comma-separated subreddit names"},
        "categories": {"type": "string", "description": "HN: comma-separated categories (top,new,best)"},
        "channel_ids": {"type": "string", "description": "Discord: comma-separated channel IDs"},
        "min_score": {"type": "integer", "description": "Minimum intent score 0-100"}
    }
}
```

### `social_leads`

```python
async def social_leads(
    platform: str = "",          # Filter by platform, empty = all
    status: str = "",            # Filter: new, reviewed, replied, archived
    min_score: int = 0,
    limit: int = 20,
) -> str:
```

Returns leads from all platforms, filterable.

### Gatekeeper classification
Both tools: GREEN (read-only scanning, no write actions)

---

## 7. Config Extension (`config.py`)

Add to existing `SocialConfig`:

```python
# Hacker News
hn_enabled: bool = Field(default=False, description="Enable HN scanning")
hn_categories: list[str] = Field(default_factory=lambda: ["top", "new"])
hn_min_score: int = Field(default=60, ge=0, le=100)
hn_scan_interval_minutes: int = Field(default=60, ge=10, le=1440)

# Discord
discord_scanner_enabled: bool = Field(default=False, description="Enable Discord scanning")
discord_scan_channels: list[str] = Field(default_factory=list, description="Channel IDs to monitor")
discord_min_score: int = Field(default=60, ge=0, le=100)
discord_scan_interval_minutes: int = Field(default=30, ge=5, le=1440)
```

---

## 8. Service Extension (`service.py`)

`RedditLeadService` becomes platform-aware. Add methods:

```python
async def scan_hackernews(self, categories=None, min_score=60) -> ScanResult: ...
async def scan_discord(self, channel_ids=None, min_score=60) -> ScanResult: ...
async def scan_all(self, min_score=60) -> dict[str, ScanResult]: ...
async def get_leads(self, platform=None, status=None, min_score=0, limit=20) -> list[Lead]: ...
```

### Cron integration
If `hn_enabled`: register cron job `social_hn_scan` at `hn_scan_interval_minutes`
If `discord_scanner_enabled`: register cron job `social_discord_scan`

---

## 9. Gateway Wiring (`gateway.py`)

In post-init block (after Reddit wiring):

```python
# Hacker News Scanner
if getattr(social_cfg, "hn_enabled", False):
    from cognithor.social.hn_scanner import HackerNewsScanner
    self._reddit_lead_service._hn_scanner = HackerNewsScanner(llm_fn=_reddit_llm_fn)
    log.info("hn_scanner_initialized")

# Discord Scanner
if getattr(social_cfg, "discord_scanner_enabled", False):
    discord_token = os.environ.get("COGNITHOR_DISCORD_TOKEN", "")
    if discord_token:
        from cognithor.social.discord_scanner import DiscordScanner
        self._reddit_lead_service._discord_scanner = DiscordScanner(
            bot_token=discord_token, llm_fn=_reddit_llm_fn
        )
        log.info("discord_scanner_initialized")
```

---

## 10. Flutter UI Changes

### Leads Screen
- Add platform filter dropdown: "All" | "Reddit" | "Hacker News" | "Discord"
- Lead cards show platform icon (Reddit alien, HN Y-logo, Discord icon)
- Platform-specific actions: Reddit has "Reply", HN has "View Discussion", Discord has "View Channel"

### Config > Social Listening
- Add HN section: enable toggle, categories multi-select, min score, interval
- Add Discord section: enable toggle, channel IDs input, min score, interval

---

## 11. Store Migration

SQL migration for existing `leads` table:

```sql
ALTER TABLE leads ADD COLUMN platform TEXT DEFAULT 'reddit';
ALTER TABLE leads ADD COLUMN platform_id TEXT DEFAULT '';
ALTER TABLE leads ADD COLUMN platform_url TEXT DEFAULT '';
CREATE INDEX IF NOT EXISTS idx_leads_platform ON leads(platform);
```

Runs automatically on first access after upgrade. Existing leads get `platform='reddit'`.

---

## 12. Tests

```
tests/social/test_hn_scanner.py       # Mocked Firebase + Algolia, scoring, scan lifecycle
tests/social/test_discord_scanner.py  # Mocked Discord API, message fetch, scoring
tests/social/test_social_tools.py     # social_scan dispatches correctly, social_leads filters
tests/social/test_store_migration.py  # platform field migration, backward compat
```

All tests mock HTTP calls (httpx). No real API calls. Discord bot token mocked.

---

## 13. Implementation Order

1. Lead model + store migration (platform field)
2. HackerNewsScanner + tests
3. DiscordScanner + tests
4. social_tools.py (2 MCP tools) + gatekeeper GREEN
5. service.py extension (scan_hackernews, scan_discord, scan_all)
6. gateway.py wiring
7. config.py extension
8. Flutter UI: platform filter + config pages
9. Full test suite verification
