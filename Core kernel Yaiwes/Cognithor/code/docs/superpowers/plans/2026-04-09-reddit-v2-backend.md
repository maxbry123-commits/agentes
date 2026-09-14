# Reddit Lead Hunter v2 Backend — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add LLM reply refinement, performance tracking, subreddit discovery, reply templates, and feedback learning to the Reddit Lead Hunter — making it a self-improving system.

**Architecture:** 5 new modules in `src/jarvis/social/` (refiner, tracker, discovery, templates, learner) extending the existing store with 3 new tables. Scanner gets few-shot + style profile injection. 3 new MCP tools, ~8 new REST endpoints, 2 new cron jobs.

**Tech Stack:** Python, SQLite (SQLCipher), httpx, Cognithor UnifiedLLMClient, CronEngine

**Depends on:** Reddit Lead Hunter v1 (Plan A+B from earlier today). Plan B (Flutter v2) follows separately.

---

## File Structure

| File | Responsibility |
|------|---------------|
| `src/jarvis/social/refiner.py` | **New** — LLM reply refinement + variant generation |
| `src/jarvis/social/tracker.py` | **New** — performance re-scanning + engagement scoring |
| `src/jarvis/social/discovery.py` | **New** — smart subreddit discovery via LLM + Reddit JSON |
| `src/jarvis/social/templates.py` | **New** — reply template store + matching |
| `src/jarvis/social/learner.py` | **New** — feedback learning loop + style profiles |
| `src/jarvis/social/store.py` | Extend with 3 new tables |
| `src/jarvis/social/scanner.py` | Inject few-shot + style profile into REPLY_PROMPT |
| `src/jarvis/social/reply.py` | Wire Playwright auto-post with cookie persistence |
| `src/jarvis/mcp/reddit_tools.py` | Add 3 new MCP tools |
| `src/jarvis/channels/config_routes.py` | ~8 new REST endpoints |
| `src/jarvis/gateway/gateway.py` | 2 new cron jobs |
| `tests/test_social/test_refiner.py` | **New** |
| `tests/test_social/test_tracker.py` | **New** |
| `tests/test_social/test_discovery.py` | **New** |
| `tests/test_social/test_templates.py` | **New** |
| `tests/test_social/test_learner.py` | **New** |

---

### Task 1: Extend store.py with 3 new tables

**Files:**
- Modify: `src/jarvis/social/store.py`
- Create: `tests/test_social/test_store_v2.py`

- [ ] **Step 1: Write tests for new tables**

Create `tests/test_social/test_store_v2.py`:

```python
"""Tests for v2 store tables: reply_performance, reply_templates, subreddit_profiles."""

from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.social.store import LeadStore


@pytest.fixture()
def store(tmp_path: Path) -> LeadStore:
    return LeadStore(str(tmp_path / "leads.db"))


class TestReplyPerformance:
    def test_save_and_get_performance(self, store: LeadStore):
        store.save_performance(
            lead_id="lead1",
            reply_text="Great post! Check out Cognithor",
            subreddit="LocalLLaMA",
        )
        perf = store.get_performance("lead1")
        assert perf is not None
        assert perf["reply_text"] == "Great post! Check out Cognithor"
        assert perf["reply_upvotes"] == 0
        assert perf["feedback_tag"] == ""

    def test_update_performance_metrics(self, store: LeadStore):
        store.save_performance(lead_id="lead2", reply_text="text", subreddit="SaaS")
        store.update_performance("lead2", reply_upvotes=5, reply_replies=2, author_replied=True)
        perf = store.get_performance("lead2")
        assert perf["reply_upvotes"] == 5
        assert perf["reply_replies"] == 2
        assert perf["author_replied"] == 1

    def test_set_feedback(self, store: LeadStore):
        store.save_performance(lead_id="lead3", reply_text="text", subreddit="SaaS")
        store.set_feedback("lead3", tag="converted", note="User signed up")
        perf = store.get_performance("lead3")
        assert perf["feedback_tag"] == "converted"
        assert perf["feedback_note"] == "User signed up"

    def test_get_top_performers(self, store: LeadStore):
        for i in range(5):
            store.save_performance(lead_id=f"p{i}", reply_text=f"Reply {i}", subreddit="SaaS")
            store.update_performance(f"p{i}", reply_upvotes=i * 3, reply_replies=i)
        top = store.get_top_performers("SaaS", limit=3)
        assert len(top) == 3
        assert top[0]["reply_upvotes"] >= top[1]["reply_upvotes"]

    def test_get_replied_leads_for_tracking(self, store: LeadStore):
        from jarvis.social.models import Lead, LeadStatus
        lead = Lead(post_id="tr1", subreddit="SaaS", title="T", url="u", intent_score=70,
                    status=LeadStatus.REPLIED)
        store.save_lead(lead)
        replied = store.get_replied_leads_for_tracking(max_age_days=7)
        assert len(replied) == 1


class TestReplyTemplates:
    def test_save_and_list(self, store: LeadStore):
        store.save_template(
            name="Technical Intro",
            template_text="Hey, {product_name} does exactly this...",
            subreddit="LocalLLaMA",
            style="technical",
        )
        templates = store.list_templates()
        assert len(templates) == 1
        assert templates[0]["name"] == "Technical Intro"

    def test_list_by_subreddit(self, store: LeadStore):
        store.save_template(name="Generic", template_text="text", subreddit="", style="casual")
        store.save_template(name="LLaMA-specific", template_text="text", subreddit="LocalLLaMA", style="technical")
        llama = store.list_templates(subreddit="LocalLLaMA")
        assert len(llama) == 2  # specific + universal (empty subreddit)

    def test_delete_template(self, store: LeadStore):
        tid = store.save_template(name="ToDelete", template_text="x", subreddit="", style="")
        store.delete_template(tid)
        assert len(store.list_templates()) == 0

    def test_increment_use_count(self, store: LeadStore):
        tid = store.save_template(name="Used", template_text="x", subreddit="", style="")
        store.increment_template_use(tid)
        store.increment_template_use(tid)
        templates = store.list_templates()
        assert templates[0]["use_count"] == 2


class TestSubredditProfiles:
    def test_save_and_get_profile(self, store: LeadStore):
        store.save_profile(
            subreddit="LocalLLaMA",
            what_works="Technical depth, code examples",
            what_fails="Sales pitch, generic advice",
            optimal_length=120,
            optimal_tone="technically detailed",
            best_openings='["Your point about...", "Have you tried..."]',
            avoid_patterns='["Check out my...", "I built..."]',
            sample_size=15,
        )
        profile = store.get_profile("LocalLLaMA")
        assert profile is not None
        assert profile["what_works"] == "Technical depth, code examples"
        assert profile["optimal_length"] == 120
        assert profile["sample_size"] == 15

    def test_get_nonexistent_profile(self, store: LeadStore):
        assert store.get_profile("NonExistent") is None

    def test_update_profile(self, store: LeadStore):
        store.save_profile(subreddit="SaaS", what_works="v1", what_fails="v1",
                           optimal_length=100, optimal_tone="casual", sample_size=5)
        store.save_profile(subreddit="SaaS", what_works="v2 updated", what_fails="v2",
                           optimal_length=150, optimal_tone="detailed", sample_size=20)
        profile = store.get_profile("SaaS")
        assert profile["what_works"] == "v2 updated"
        assert profile["sample_size"] == 20
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_social/test_store_v2.py -x -q --tb=short`
Expected: FAIL — methods not found

- [ ] **Step 3: Add 3 new tables to store.py schema**

In `src/jarvis/social/store.py`, append to the `_SCHEMA` string (after the `lead_scans` table):

```sql
CREATE TABLE IF NOT EXISTS reply_performance (
    lead_id           TEXT PRIMARY KEY,
    reply_text        TEXT NOT NULL,
    subreddit         TEXT NOT NULL,
    reply_upvotes     INTEGER DEFAULT 0,
    reply_replies     INTEGER DEFAULT 0,
    author_replied    INTEGER DEFAULT 0,
    post_upvotes_delta INTEGER DEFAULT 0,
    feedback_tag      TEXT DEFAULT '',
    feedback_note     TEXT DEFAULT '',
    first_tracked_at  REAL NOT NULL,
    last_tracked_at   REAL NOT NULL,
    tracking_count    INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS reply_templates (
    id            TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    template_text TEXT NOT NULL,
    subreddit     TEXT DEFAULT '',
    style         TEXT DEFAULT '',
    use_count     INTEGER DEFAULT 0,
    avg_engagement REAL DEFAULT 0,
    created_from_lead TEXT DEFAULT '',
    created_at    REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS subreddit_profiles (
    subreddit       TEXT PRIMARY KEY,
    what_works      TEXT DEFAULT '',
    what_fails      TEXT DEFAULT '',
    optimal_length  INTEGER DEFAULT 0,
    optimal_tone    TEXT DEFAULT '',
    best_openings   TEXT DEFAULT '[]',
    avoid_patterns  TEXT DEFAULT '[]',
    sample_size     INTEGER DEFAULT 0,
    updated_at      REAL NOT NULL
);
```

- [ ] **Step 4: Add store methods for reply_performance**

Add to `LeadStore` class:

```python
    def save_performance(self, lead_id: str, reply_text: str, subreddit: str) -> None:
        now = time.time()
        self.conn.execute(
            """INSERT INTO reply_performance
                (lead_id, reply_text, subreddit, first_tracked_at, last_tracked_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(lead_id) DO UPDATE SET last_tracked_at=?, tracking_count=tracking_count+1""",
            (lead_id, reply_text, subreddit, now, now, now),
        )
        self.conn.commit()

    def get_performance(self, lead_id: str) -> dict[str, Any] | None:
        row = self.conn.execute("SELECT * FROM reply_performance WHERE lead_id = ?", (lead_id,)).fetchone()
        return dict(row) if row else None

    def update_performance(
        self, lead_id: str, *,
        reply_upvotes: int | None = None,
        reply_replies: int | None = None,
        author_replied: bool | None = None,
        post_upvotes_delta: int | None = None,
    ) -> None:
        sets, params = [], []
        if reply_upvotes is not None:
            sets.append("reply_upvotes = ?"); params.append(reply_upvotes)
        if reply_replies is not None:
            sets.append("reply_replies = ?"); params.append(reply_replies)
        if author_replied is not None:
            sets.append("author_replied = ?"); params.append(int(author_replied))
        if post_upvotes_delta is not None:
            sets.append("post_upvotes_delta = ?"); params.append(post_upvotes_delta)
        sets.append("last_tracked_at = ?"); params.append(time.time())
        params.append(lead_id)
        if sets:
            self.conn.execute(f"UPDATE reply_performance SET {', '.join(sets)} WHERE lead_id = ?", params)
            self.conn.commit()

    def set_feedback(self, lead_id: str, tag: str, note: str = "") -> None:
        self.conn.execute(
            "UPDATE reply_performance SET feedback_tag = ?, feedback_note = ? WHERE lead_id = ?",
            (tag, note, lead_id),
        )
        self.conn.commit()

    def get_top_performers(self, subreddit: str, limit: int = 5) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """SELECT * FROM reply_performance WHERE subreddit = ?
            ORDER BY (reply_upvotes * 3 + reply_replies * 5 + author_replied * 10) DESC
            LIMIT ?""",
            (subreddit, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_replied_leads_for_tracking(self, max_age_days: int = 7) -> list[dict[str, Any]]:
        cutoff = time.time() - (max_age_days * 86400)
        rows = self.conn.execute(
            """SELECT l.* FROM leads l
            LEFT JOIN reply_performance rp ON l.id = rp.lead_id
            WHERE l.status = 'replied' AND l.replied_at > ?
            AND (rp.lead_id IS NULL OR rp.tracking_count < 10)""",
            (cutoff,),
        ).fetchall()
        return [dict(r) for r in rows]
```

- [ ] **Step 5: Add store methods for reply_templates**

```python
    def save_template(
        self, name: str, template_text: str, subreddit: str = "",
        style: str = "", created_from_lead: str = "",
    ) -> str:
        tid = str(uuid4())
        self.conn.execute(
            """INSERT INTO reply_templates (id, name, template_text, subreddit, style, created_from_lead, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (tid, name, template_text, subreddit, style, created_from_lead, time.time()),
        )
        self.conn.commit()
        return tid

    def list_templates(self, subreddit: str | None = None) -> list[dict[str, Any]]:
        if subreddit:
            rows = self.conn.execute(
                "SELECT * FROM reply_templates WHERE subreddit = ? OR subreddit = '' ORDER BY use_count DESC",
                (subreddit,),
            ).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM reply_templates ORDER BY use_count DESC").fetchall()
        return [dict(r) for r in rows]

    def delete_template(self, template_id: str) -> None:
        self.conn.execute("DELETE FROM reply_templates WHERE id = ?", (template_id,))
        self.conn.commit()

    def increment_template_use(self, template_id: str) -> None:
        self.conn.execute(
            "UPDATE reply_templates SET use_count = use_count + 1 WHERE id = ?", (template_id,),
        )
        self.conn.commit()
```

- [ ] **Step 6: Add store methods for subreddit_profiles**

```python
    def save_profile(
        self, subreddit: str, what_works: str = "", what_fails: str = "",
        optimal_length: int = 0, optimal_tone: str = "",
        best_openings: str = "[]", avoid_patterns: str = "[]", sample_size: int = 0,
    ) -> None:
        self.conn.execute(
            """INSERT INTO subreddit_profiles
                (subreddit, what_works, what_fails, optimal_length, optimal_tone,
                 best_openings, avoid_patterns, sample_size, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(subreddit) DO UPDATE SET
                what_works=excluded.what_works, what_fails=excluded.what_fails,
                optimal_length=excluded.optimal_length, optimal_tone=excluded.optimal_tone,
                best_openings=excluded.best_openings, avoid_patterns=excluded.avoid_patterns,
                sample_size=excluded.sample_size, updated_at=excluded.updated_at""",
            (subreddit, what_works, what_fails, optimal_length, optimal_tone,
             best_openings, avoid_patterns, sample_size, time.time()),
        )
        self.conn.commit()

    def get_profile(self, subreddit: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT * FROM subreddit_profiles WHERE subreddit = ?", (subreddit,)
        ).fetchone()
        return dict(row) if row else None
```

Add `from uuid import uuid4` to imports if not already present.

- [ ] **Step 7: Run tests**

Run: `cd "D:/Jarvis/jarvis complete v20" && ruff check src/jarvis/social/store.py tests/test_social/test_store_v2.py && ruff format src/jarvis/social/store.py tests/test_social/test_store_v2.py && python -m pytest tests/test_social/ -x -q --tb=short`
Expected: All pass

- [ ] **Step 8: Commit**

```bash
git add src/jarvis/social/store.py tests/test_social/test_store_v2.py
git commit -m "feat(social): extend store with performance, templates, profiles tables"
```

---

### Task 2: ReplyRefiner — LLM refinement + variants

**Files:**
- Create: `src/jarvis/social/refiner.py`
- Create: `tests/test_social/test_refiner.py`

- [ ] **Step 1: Write tests**

Create `tests/test_social/test_refiner.py`:

```python
"""Tests for social.refiner — LLM reply refinement + variants."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from jarvis.social.refiner import ReplyRefiner, RefinedReply


@pytest.fixture()
def refiner():
    llm_fn = AsyncMock(return_value={
        "message": {"content": "Improved reply with more technical depth."}
    })
    return ReplyRefiner(llm_fn=llm_fn)


class TestReplyRefiner:
    @pytest.mark.asyncio
    async def test_refine_returns_refined_reply(self, refiner: ReplyRefiner):
        result = await refiner.refine(
            post={"title": "Need local AI", "selftext": "Looking for tools", "subreddit": "LocalLLaMA"},
            current_draft="Check out Cognithor",
            product_name="Cognithor",
        )
        assert isinstance(result, RefinedReply)
        assert result.text == "Improved reply with more technical depth."
        assert result.style == "refined"

    @pytest.mark.asyncio
    async def test_refine_with_hint(self, refiner: ReplyRefiner):
        result = await refiner.refine(
            post={"title": "T", "selftext": "", "subreddit": "SaaS"},
            current_draft="Draft",
            product_name="X",
            user_hint="make it shorter",
        )
        assert result.text  # LLM was called
        # Verify hint was in the prompt
        call_args = refiner._llm_fn.call_args
        messages = call_args[1].get("messages") or call_args[0][0] if call_args[0] else call_args[1]["messages"]
        prompt_text = messages[0]["content"]
        assert "shorter" in prompt_text

    @pytest.mark.asyncio
    async def test_generate_variants(self):
        call_count = 0
        async def mock_llm(**kwargs):
            nonlocal call_count
            call_count += 1
            styles = ["Technical deep-dive reply", "Short casual reply", "Question-based reply"]
            return {"message": {"content": styles[call_count - 1] if call_count <= 3 else "fallback"}}

        refiner = ReplyRefiner(llm_fn=mock_llm)
        variants = await refiner.generate_variants(
            post={"title": "T", "selftext": "", "subreddit": "SaaS"},
            product_name="X",
            count=3,
        )
        assert len(variants) == 3
        assert variants[0].text != variants[1].text

    @pytest.mark.asyncio
    async def test_refine_with_style_profile(self, refiner: ReplyRefiner):
        profile = {
            "what_works": "Technical depth",
            "what_fails": "Sales pitch",
            "optimal_length": 120,
        }
        result = await refiner.refine(
            post={"title": "T", "selftext": "", "subreddit": "LLaMA"},
            current_draft="Draft",
            product_name="X",
            style_profile=profile,
        )
        assert result.text
        call_args = refiner._llm_fn.call_args
        messages = call_args[1].get("messages") or call_args[0][0] if call_args[0] else call_args[1]["messages"]
        prompt_text = messages[0]["content"]
        assert "Technical depth" in prompt_text

    @pytest.mark.asyncio
    async def test_refine_with_few_shot(self, refiner: ReplyRefiner):
        few_shot = [
            {"reply_text": "Great example reply", "reply_upvotes": 8},
        ]
        result = await refiner.refine(
            post={"title": "T", "selftext": "", "subreddit": "X"},
            current_draft="Draft",
            product_name="X",
            few_shot_examples=few_shot,
        )
        assert result.text
        call_args = refiner._llm_fn.call_args
        messages = call_args[1].get("messages") or call_args[0][0] if call_args[0] else call_args[1]["messages"]
        prompt_text = messages[0]["content"]
        assert "Great example reply" in prompt_text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd "D:/Jarvis/jarvis complete v20" && python -m pytest tests/test_social/test_refiner.py -x -q --tb=short`
Expected: FAIL — module not found

- [ ] **Step 3: Implement ReplyRefiner**

Create `src/jarvis/social/refiner.py`:

```python
"""LLM-based reply refinement and variant generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from jarvis.utils.logging import get_logger

log = get_logger(__name__)

LLMFn = Callable[..., Awaitable[dict[str, Any]]]

REFINE_PROMPT = """
You are an expert Reddit reply editor. Improve this draft reply.

PRODUCT: {product_name}
SUBREDDIT: r/{subreddit}

ORIGINAL POST:
Title: {title}
Text: {body}

CURRENT DRAFT:
{current_draft}

{style_context}
{few_shot_context}
{hint_context}

Rewrite the reply to be more effective. Keep it under {max_words} words.
Maintain a {tone} tone. No meta-commentary, output ONLY the improved reply.
""".strip()

VARIANT_PROMPT = """
You are an expert Reddit reply writer. Write a {style_name} reply.

PRODUCT: {product_name}
SUBREDDIT: r/{subreddit}

ORIGINAL POST:
Title: {title}
Text: {body}

Style: {style_description}
Max length: {max_words} words.
Tone: {tone}

{style_context}

Output ONLY the reply text, no meta-commentary.
""".strip()

VARIANT_STYLES = [
    ("technical", "Technically detailed with specific features, code examples or architecture details"),
    ("casual", "Short, casual, reddit-native. Conversational tone, like talking to a friend"),
    ("question", "Start with a question that shows understanding, then suggest the product as one option"),
]


@dataclass
class RefinedReply:
    text: str
    style: str
    changes_summary: str = ""


class ReplyRefiner:
    """Refines reply drafts via LLM with style profile and few-shot context."""

    def __init__(self, llm_fn: LLMFn | None = None) -> None:
        self._llm_fn = llm_fn

    async def refine(
        self,
        post: dict[str, Any],
        current_draft: str,
        product_name: str,
        *,
        user_hint: str = "",
        style_profile: dict[str, Any] | None = None,
        few_shot_examples: list[dict[str, Any]] | None = None,
        tone: str = "helpful, technically credible",
        max_words: int = 150,
    ) -> RefinedReply:
        if not self._llm_fn:
            return RefinedReply(text=current_draft, style="original", changes_summary="No LLM available")

        style_ctx = ""
        if style_profile:
            style_ctx = (
                f"STYLE PROFILE for r/{post.get('subreddit', '')}:\n"
                f"- What works: {style_profile.get('what_works', '')}\n"
                f"- What fails: {style_profile.get('what_fails', '')}\n"
                f"- Optimal length: ~{style_profile.get('optimal_length', 150)} words"
            )
            max_words = style_profile.get("optimal_length", max_words)

        few_shot_ctx = ""
        if few_shot_examples:
            lines = ["TOP PERFORMING REPLIES in this subreddit:"]
            for i, ex in enumerate(few_shot_examples[:3], 1):
                lines.append(f'{i}. [{ex.get("reply_upvotes", 0)} upvotes] "{ex.get("reply_text", "")[:200]}"')
            few_shot_ctx = "\n".join(lines)

        hint_ctx = f"USER REQUEST: {user_hint}" if user_hint else ""

        prompt = REFINE_PROMPT.format(
            product_name=product_name,
            subreddit=post.get("subreddit", ""),
            title=post.get("title", ""),
            body=(post.get("selftext") or "")[:500],
            current_draft=current_draft,
            style_context=style_ctx,
            few_shot_context=few_shot_ctx,
            hint_context=hint_ctx,
            max_words=max_words,
            tone=tone,
        )

        try:
            response = await self._llm_fn(messages=[{"role": "user", "content": prompt}], temperature=0.4)
            text = response.get("message", {}).get("content", "").strip()
            return RefinedReply(text=text or current_draft, style="refined", changes_summary=hint_ctx or "General improvement")
        except Exception as exc:
            log.warning("refine_failed", error=str(exc))
            return RefinedReply(text=current_draft, style="original", changes_summary=f"Refinement failed: {exc}")

    async def generate_variants(
        self,
        post: dict[str, Any],
        product_name: str,
        count: int = 3,
        *,
        style_profile: dict[str, Any] | None = None,
        tone: str = "helpful, technically credible",
        max_words: int = 150,
    ) -> list[RefinedReply]:
        if not self._llm_fn:
            return []

        style_ctx = ""
        if style_profile:
            style_ctx = (
                f"STYLE PROFILE:\n"
                f"- What works: {style_profile.get('what_works', '')}\n"
                f"- Avoid: {style_profile.get('what_fails', '')}"
            )

        variants = []
        for i in range(min(count, len(VARIANT_STYLES))):
            style_name, style_desc = VARIANT_STYLES[i]
            prompt = VARIANT_PROMPT.format(
                product_name=product_name,
                subreddit=post.get("subreddit", ""),
                title=post.get("title", ""),
                body=(post.get("selftext") or "")[:500],
                style_name=style_name,
                style_description=style_desc,
                max_words=max_words,
                tone=tone,
                style_context=style_ctx,
            )
            try:
                response = await self._llm_fn(messages=[{"role": "user", "content": prompt}], temperature=0.6)
                text = response.get("message", {}).get("content", "").strip()
                if text:
                    variants.append(RefinedReply(text=text, style=style_name))
            except Exception as exc:
                log.warning("variant_failed", style=style_name, error=str(exc))

        return variants
```

- [ ] **Step 4: Run tests**

Run: `cd "D:/Jarvis/jarvis complete v20" && ruff check src/jarvis/social/refiner.py tests/test_social/test_refiner.py && ruff format src/jarvis/social/refiner.py tests/test_social/test_refiner.py && python -m pytest tests/test_social/test_refiner.py -x -q --tb=short`
Expected: All pass

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/social/refiner.py tests/test_social/test_refiner.py
git commit -m "feat(social): add ReplyRefiner — LLM refinement + variant generation"
```

---

### Task 3: PerformanceTracker — re-scanning + engagement scoring

**Files:**
- Create: `src/jarvis/social/tracker.py`
- Create: `tests/test_social/test_tracker.py`

- [ ] **Step 1: Write tests**

Create `tests/test_social/test_tracker.py`:

```python
"""Tests for social.tracker — performance re-scanning."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jarvis.social.store import LeadStore
from jarvis.social.tracker import PerformanceTracker, engagement_score


class TestEngagementScore:
    def test_zero_engagement(self):
        assert engagement_score(0, 0, False, "") == 0

    def test_upvotes_only(self):
        assert engagement_score(5, 0, False, "") == 15  # 5*3

    def test_full_engagement(self):
        score = engagement_score(5, 2, True, "converted")
        assert score == 15 + 10 + 10 + 20  # 5*3 + 2*5 + 10 + 20 = 55

    def test_capped_at_100(self):
        score = engagement_score(50, 20, True, "converted")
        assert score <= 100


class TestPerformanceTracker:
    @pytest.fixture()
    def store(self, tmp_path: Path) -> LeadStore:
        return LeadStore(str(tmp_path / "leads.db"))

    def test_create(self, store: LeadStore):
        tracker = PerformanceTracker(store=store)
        assert tracker is not None

    def test_find_reply_in_comments(self):
        comments = [
            {"data": {"body": "Some random comment", "author": "user1", "score": 2, "replies": ""}},
            {"data": {"body": "Check out Cognithor — it does exactly this", "author": "our_user", "score": 5,
                       "replies": {"data": {"children": [{"data": {}}]}}}},
        ]
        from jarvis.social.tracker import _find_our_reply
        match = _find_our_reply(comments, "Check out Cognithor")
        assert match is not None
        assert match["score"] == 5

    def test_find_reply_fuzzy_match(self):
        comments = [
            {"data": {"body": "Check out Cognithor - it does exactly this thing", "author": "u", "score": 3, "replies": ""}},
        ]
        from jarvis.social.tracker import _find_our_reply
        match = _find_our_reply(comments, "Check out Cognithor — it does exactly this")
        assert match is not None  # fuzzy match should find it
```

- [ ] **Step 2: Implement PerformanceTracker**

Create `src/jarvis/social/tracker.py`:

```python
"""Reply performance tracking — re-scans Reddit for engagement metrics."""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any

import httpx

from jarvis.social.store import LeadStore
from jarvis.utils.logging import get_logger

log = get_logger(__name__)

_USER_AGENT = "cognithor:reply_tracker:v1.0 (by u/cognithor-bot)"


def engagement_score(
    upvotes: int, replies: int, author_replied: bool, feedback_tag: str,
) -> int:
    raw = upvotes * 3 + replies * 5 + (10 if author_replied else 0) + (20 if feedback_tag == "converted" else 0)
    return min(100, raw)


def _find_our_reply(
    comments: list[dict[str, Any]], reply_text: str, threshold: float = 0.75,
) -> dict[str, Any] | None:
    """Find our reply in a list of Reddit comments using fuzzy matching."""
    reply_lower = reply_text.lower()[:200]
    for comment in comments:
        data = comment.get("data", {})
        body = (data.get("body") or "").lower()[:200]
        if not body:
            continue
        ratio = SequenceMatcher(None, reply_lower, body).ratio()
        if ratio >= threshold:
            # Count direct replies to our comment
            reply_data = data.get("replies")
            reply_count = 0
            if isinstance(reply_data, dict):
                children = reply_data.get("data", {}).get("children", [])
                reply_count = len(children)
            return {
                "score": data.get("score", 0),
                "reply_count": reply_count,
                "author": data.get("author", ""),
                "ratio": ratio,
            }
    return None


class PerformanceTracker:
    """Tracks reply performance by re-scanning Reddit posts."""

    def __init__(self, store: LeadStore) -> None:
        self._store = store
        self._http = httpx.Client(
            timeout=15,
            headers={"User-Agent": _USER_AGENT},
            follow_redirects=True,
        )

    async def track_all(self, max_age_days: int = 7) -> dict[str, Any]:
        """Re-scan all replied leads for engagement metrics."""
        import asyncio

        leads = self._store.get_replied_leads_for_tracking(max_age_days=max_age_days)
        tracked = 0
        errors = 0

        for lead_dict in leads:
            lead_id = lead_dict.get("id", "")
            post_id = lead_dict.get("post_id", "")
            subreddit = lead_dict.get("subreddit", "")

            perf = self._store.get_performance(lead_id)
            if perf is None:
                # First tracking — save initial record
                self._store.save_performance(
                    lead_id=lead_id,
                    reply_text=lead_dict.get("reply_final") or lead_dict.get("reply_draft", ""),
                    subreddit=subreddit,
                )
                perf = self._store.get_performance(lead_id)

            try:
                # Fetch post comments
                url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.json"
                resp = self._http.get(url, params={"raw_json": 1, "limit": 100})
                resp.raise_for_status()
                data = resp.json()

                # Post data
                post_data = data[0]["data"]["children"][0]["data"] if data else {}
                current_upvotes = post_data.get("score", 0)

                # Comments
                comments = data[1]["data"]["children"] if len(data) > 1 else []
                reply_text = perf.get("reply_text", "") if perf else ""

                match = _find_our_reply(comments, reply_text)

                if match:
                    # Check if post author replied to our comment
                    post_author = post_data.get("author", "")
                    author_replied = any(
                        c.get("data", {}).get("author") == post_author
                        for c in (match.get("replies_data", []) if isinstance(match.get("replies_data"), list) else [])
                    )

                    self._store.update_performance(
                        lead_id,
                        reply_upvotes=match["score"],
                        reply_replies=match["reply_count"],
                        author_replied=author_replied,
                    )
                    tracked += 1
                    log.info("tracked_reply", lead_id=lead_id, upvotes=match["score"], replies=match["reply_count"])
                else:
                    tracked += 1  # Still counts as tracked even if reply not found

                # Rate limit
                await asyncio.sleep(1.0)

            except Exception as exc:
                errors += 1
                log.debug("tracking_failed", lead_id=lead_id, error=str(exc))

        return {"tracked": tracked, "errors": errors, "total": len(leads)}

    def close(self) -> None:
        self._http.close()
```

- [ ] **Step 3: Run tests**

Run: `cd "D:/Jarvis/jarvis complete v20" && ruff check src/jarvis/social/tracker.py tests/test_social/test_tracker.py && ruff format src/jarvis/social/tracker.py tests/test_social/test_tracker.py && python -m pytest tests/test_social/test_tracker.py -x -q --tb=short`
Expected: All pass

- [ ] **Step 4: Commit**

```bash
git add src/jarvis/social/tracker.py tests/test_social/test_tracker.py
git commit -m "feat(social): add PerformanceTracker — re-scanning + engagement scoring"
```

---

### Task 4: SubredditDiscovery

**Files:**
- Create: `src/jarvis/social/discovery.py`
- Create: `tests/test_social/test_discovery.py`

- [ ] **Step 1: Write tests**

Create `tests/test_social/test_discovery.py`:

```python
"""Tests for social.discovery — smart subreddit discovery."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from jarvis.social.discovery import SubredditDiscovery, SubredditSuggestion


class TestSubredditDiscovery:
    @pytest.mark.asyncio
    async def test_discover_returns_suggestions(self):
        llm_fn = AsyncMock(return_value={
            "message": {"content": '["LocalLLaMA", "SaaS", "Python", "agentframework", "MachineLearning"]'}
        })
        discovery = SubredditDiscovery(llm_fn=llm_fn)

        mock_about = MagicMock()
        mock_about.status_code = 200
        mock_about.json.return_value = {
            "data": {"subscribers": 50000, "active_user_count": 200, "display_name": "LocalLLaMA"}
        }

        with patch.object(discovery._http, "get", return_value=mock_about):
            results = await discovery.discover("Cognithor", "Open-source Agent OS")

        assert len(results) > 0
        assert all(isinstance(r, SubredditSuggestion) for r in results)

    @pytest.mark.asyncio
    async def test_discover_handles_nonexistent_subreddit(self):
        llm_fn = AsyncMock(return_value={
            "message": {"content": '["NonExistentSub12345"]'}
        })
        discovery = SubredditDiscovery(llm_fn=llm_fn)

        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.raise_for_status.side_effect = Exception("404")

        with patch.object(discovery._http, "get", side_effect=Exception("404")):
            results = await discovery.discover("X", "Y")

        assert len(results) == 0

    def test_suggestion_model(self):
        s = SubredditSuggestion(
            name="LocalLLaMA", subscribers=50000, posts_per_day=25.0,
            relevance_score=85, reasoning="Active LLM community",
            sample_posts=["Post 1", "Post 2"],
        )
        assert s.name == "LocalLLaMA"
        assert s.relevance_score == 85
```

- [ ] **Step 2: Implement SubredditDiscovery**

Create `src/jarvis/social/discovery.py`:

```python
"""Smart subreddit discovery via LLM + Reddit JSON validation."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

import httpx

from jarvis.utils.logging import get_logger

log = get_logger(__name__)

LLMFn = Callable[..., Awaitable[dict[str, Any]]]

_USER_AGENT = "cognithor:subreddit_discovery:v1.0 (by u/cognithor-bot)"

DISCOVER_PROMPT = """
You are an expert in Reddit communities. Given a product, suggest 15-20 subreddits where potential users might discuss related problems.

PRODUCT: {product_name}
DESCRIPTION: {product_description}

Rules:
- Include both large (>100k) and niche (<50k) subreddits
- Focus on subreddits where people ask for help, not just news
- Include technology-specific and use-case-specific subreddits
- NO NSFW subreddits

Reply ONLY with a JSON array of subreddit names (without r/ prefix):
["SubredditName1", "SubredditName2", ...]
""".strip()


@dataclass
class SubredditSuggestion:
    name: str
    subscribers: int = 0
    posts_per_day: float = 0.0
    relevance_score: int = 0
    reasoning: str = ""
    sample_posts: list[str] = field(default_factory=list)


class SubredditDiscovery:
    """Discovers relevant subreddits for a product via LLM + Reddit validation."""

    def __init__(self, llm_fn: LLMFn | None = None) -> None:
        self._llm_fn = llm_fn
        self._http = httpx.Client(
            timeout=15,
            headers={"User-Agent": _USER_AGENT},
            follow_redirects=True,
        )

    async def discover(
        self,
        product_name: str,
        product_description: str,
        max_results: int = 10,
    ) -> list[SubredditSuggestion]:
        if not self._llm_fn:
            return []

        # Step 1: LLM generates candidates
        prompt = DISCOVER_PROMPT.format(
            product_name=product_name,
            product_description=product_description,
        )
        try:
            response = await self._llm_fn(messages=[{"role": "user", "content": prompt}], temperature=0.3)
            raw = response.get("message", {}).get("content", "")
            start = raw.find("[")
            end = raw.rfind("]") + 1
            if start == -1 or end == 0:
                return []
            candidates = json.loads(raw[start:end])
        except Exception as exc:
            log.warning("discovery_llm_failed", error=str(exc))
            return []

        # Step 2: Validate each candidate via Reddit JSON
        suggestions = []
        for name in candidates[:20]:
            try:
                about = self._http.get(
                    f"https://www.reddit.com/r/{name}/about.json",
                    params={"raw_json": 1},
                )
                about.raise_for_status()
                data = about.json().get("data", {})

                subscribers = data.get("subscribers", 0)
                active = data.get("active_user_count", 0)

                # Estimate posts per day from active users
                posts_per_day = max(1.0, active * 0.1)

                # Get sample posts
                sample_posts = []
                try:
                    posts_resp = self._http.get(
                        f"https://www.reddit.com/r/{name}/new.json",
                        params={"limit": 5, "raw_json": 1},
                    )
                    if posts_resp.status_code == 200:
                        children = posts_resp.json().get("data", {}).get("children", [])
                        sample_posts = [c["data"]["title"] for c in children[:3]]
                except Exception:
                    pass

                # Rank score
                rank = posts_per_day * math.log(max(subscribers, 1))

                suggestions.append(SubredditSuggestion(
                    name=name,
                    subscribers=subscribers,
                    posts_per_day=round(posts_per_day, 1),
                    relevance_score=0,  # Set after sorting
                    reasoning=f"{subscribers:,} subscribers, ~{posts_per_day:.0f} posts/day",
                    sample_posts=sample_posts,
                ))

                import asyncio
                await asyncio.sleep(0.5)  # Rate limit

            except Exception as exc:
                log.debug("discovery_validation_failed", subreddit=name, error=str(exc))

        # Sort by rank, assign relevance scores
        suggestions.sort(key=lambda s: s.posts_per_day * math.log(max(s.subscribers, 1)), reverse=True)
        for i, s in enumerate(suggestions[:max_results]):
            s.relevance_score = max(10, 100 - i * 8)

        return suggestions[:max_results]

    def close(self) -> None:
        self._http.close()
```

- [ ] **Step 3: Run tests + commit**

Run: `cd "D:/Jarvis/jarvis complete v20" && ruff check src/jarvis/social/discovery.py tests/test_social/test_discovery.py && ruff format src/jarvis/social/discovery.py tests/test_social/test_discovery.py && python -m pytest tests/test_social/test_discovery.py -x -q --tb=short`

```bash
git add src/jarvis/social/discovery.py tests/test_social/test_discovery.py
git commit -m "feat(social): add SubredditDiscovery — LLM + Reddit validation"
```

---

### Task 5: Reply Templates

**Files:**
- Create: `src/jarvis/social/templates.py`
- Create: `tests/test_social/test_templates.py`

- [ ] **Step 1: Write tests**

Create `tests/test_social/test_templates.py`:

```python
"""Tests for social.templates — reply template management."""

from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.social.store import LeadStore
from jarvis.social.templates import TemplateManager


@pytest.fixture()
def manager(tmp_path: Path) -> TemplateManager:
    store = LeadStore(str(tmp_path / "leads.db"))
    return TemplateManager(store=store)


class TestTemplateManager:
    def test_create_template(self, manager: TemplateManager):
        tid = manager.create(
            name="Tech Intro",
            template_text="Hey, {product_name} solves this — it has {feature}.",
            subreddit="LocalLLaMA",
            style="technical",
        )
        assert tid
        templates = manager.list_for_subreddit("LocalLLaMA")
        assert len(templates) == 1
        assert templates[0]["name"] == "Tech Intro"

    def test_apply_template(self, manager: TemplateManager):
        manager.create(name="T", template_text="Check out {product_name} for r/{subreddit}!")
        templates = manager.list_for_subreddit("SaaS")
        applied = manager.apply(templates[0]["id"], product_name="Cognithor", subreddit="SaaS")
        assert applied == "Check out Cognithor for r/SaaS!"

    def test_should_auto_save(self, manager: TemplateManager):
        assert manager.should_auto_save(engagement_score=90) is True
        assert manager.should_auto_save(engagement_score=50) is False
        assert manager.should_prompt_save(engagement_score=75) is True
        assert manager.should_prompt_save(engagement_score=60) is False

    def test_delete(self, manager: TemplateManager):
        tid = manager.create(name="X", template_text="text")
        manager.delete(tid)
        assert len(manager.list_for_subreddit("")) == 0
```

- [ ] **Step 2: Implement TemplateManager**

Create `src/jarvis/social/templates.py`:

```python
"""Reply template management — save, match, apply successful reply patterns."""

from __future__ import annotations

from typing import Any

from jarvis.social.store import LeadStore
from jarvis.utils.logging import get_logger

log = get_logger(__name__)

AUTO_SAVE_THRESHOLD = 85
PROMPT_SAVE_THRESHOLD = 70


class TemplateManager:
    """Manages reply templates with auto-save from high-performing replies."""

    def __init__(self, store: LeadStore) -> None:
        self._store = store

    def create(
        self,
        name: str,
        template_text: str,
        subreddit: str = "",
        style: str = "",
        created_from_lead: str = "",
    ) -> str:
        return self._store.save_template(
            name=name,
            template_text=template_text,
            subreddit=subreddit,
            style=style,
            created_from_lead=created_from_lead,
        )

    def list_for_subreddit(self, subreddit: str) -> list[dict[str, Any]]:
        return self._store.list_templates(subreddit=subreddit or None)

    def apply(self, template_id: str, **variables: str) -> str:
        templates = self._store.list_templates()
        for t in templates:
            if t["id"] == template_id:
                self._store.increment_template_use(template_id)
                text = t["template_text"]
                for key, val in variables.items():
                    text = text.replace(f"{{{key}}}", val)
                return text
        return ""

    def delete(self, template_id: str) -> None:
        self._store.delete_template(template_id)

    @staticmethod
    def should_auto_save(engagement_score: int) -> bool:
        return engagement_score >= AUTO_SAVE_THRESHOLD

    @staticmethod
    def should_prompt_save(engagement_score: int) -> bool:
        return PROMPT_SAVE_THRESHOLD <= engagement_score < AUTO_SAVE_THRESHOLD
```

- [ ] **Step 3: Run tests + commit**

Run: `cd "D:/Jarvis/jarvis complete v20" && ruff check src/jarvis/social/templates.py tests/test_social/test_templates.py && ruff format src/jarvis/social/templates.py tests/test_social/test_templates.py && python -m pytest tests/test_social/test_templates.py -x -q --tb=short`

```bash
git add src/jarvis/social/templates.py tests/test_social/test_templates.py
git commit -m "feat(social): add TemplateManager — reply template save/match/apply"
```

---

### Task 6: ReplyLearner — feedback learning loop + style profiles

**Files:**
- Create: `src/jarvis/social/learner.py`
- Create: `tests/test_social/test_learner.py`

- [ ] **Step 1: Write tests**

Create `tests/test_social/test_learner.py`:

```python
"""Tests for social.learner — feedback learning loop."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from jarvis.social.learner import ReplyLearner
from jarvis.social.store import LeadStore


@pytest.fixture()
def store(tmp_path: Path) -> LeadStore:
    return LeadStore(str(tmp_path / "leads.db"))


class TestReplyLearner:
    @pytest.mark.asyncio
    async def test_analyze_subreddit(self, store: LeadStore):
        # Seed performance data
        for i in range(6):
            store.save_performance(
                lead_id=f"l{i}", reply_text=f"Reply {i} about technical details", subreddit="LocalLLaMA",
            )
            store.update_performance(f"l{i}", reply_upvotes=i * 2, reply_replies=i)

        llm_fn = AsyncMock(return_value={
            "message": {"content": '{"what_works": "Technical depth", "what_fails": "Generic advice", "optimal_length": 120, "optimal_tone": "technically detailed", "best_openings": ["Your point about..."], "avoid_patterns": ["Check out my..."]}'}
        })
        learner = ReplyLearner(store=store, llm_fn=llm_fn)
        profile = await learner.analyze_subreddit("LocalLLaMA")

        assert profile is not None
        assert "Technical depth" in profile["what_works"]

    @pytest.mark.asyncio
    async def test_run_learning_cycle(self, store: LeadStore):
        # Seed data for 2 subreddits
        for sub in ["LocalLLaMA", "SaaS"]:
            for i in range(5):
                store.save_performance(
                    lead_id=f"{sub}_{i}", reply_text=f"Reply {i}", subreddit=sub,
                )
                store.update_performance(f"{sub}_{i}", reply_upvotes=i * 3)

        llm_fn = AsyncMock(return_value={
            "message": {"content": '{"what_works": "X", "what_fails": "Y", "optimal_length": 100, "optimal_tone": "casual", "best_openings": [], "avoid_patterns": []}'}
        })
        learner = ReplyLearner(store=store, llm_fn=llm_fn)
        result = await learner.run_learning_cycle(min_sample_size=3)

        assert result["subreddits_analyzed"] == 2
        # Profiles should be saved
        assert store.get_profile("LocalLLaMA") is not None
        assert store.get_profile("SaaS") is not None

    def test_get_few_shot_examples(self, store: LeadStore):
        for i in range(5):
            store.save_performance(lead_id=f"fs{i}", reply_text=f"Reply {i}", subreddit="X")
            store.update_performance(f"fs{i}", reply_upvotes=i * 5)

        learner = ReplyLearner(store=store, llm_fn=AsyncMock())
        examples = learner.get_few_shot_examples("X", limit=3)
        assert len(examples) == 3
        assert examples[0]["reply_upvotes"] >= examples[1]["reply_upvotes"]
```

- [ ] **Step 2: Implement ReplyLearner**

Create `src/jarvis/social/learner.py`:

```python
"""Feedback learning loop — analyzes reply performance and builds style profiles."""

from __future__ import annotations

import json
from typing import Any, Awaitable, Callable

from jarvis.social.store import LeadStore
from jarvis.utils.logging import get_logger

log = get_logger(__name__)

LLMFn = Callable[..., Awaitable[dict[str, Any]]]

ANALYZE_PROMPT = """
You are an expert at analyzing Reddit engagement patterns. Analyze these replies and their performance.

SUBREDDIT: r/{subreddit}

TOP PERFORMING REPLIES (high engagement):
{top_replies}

WORST PERFORMING REPLIES (low engagement):
{bottom_replies}

Analyze what makes replies successful vs unsuccessful in this subreddit.
Reply in this exact JSON format:
{{
    "what_works": "<2-3 sentence summary of successful patterns>",
    "what_fails": "<2-3 sentence summary of unsuccessful patterns>",
    "optimal_length": <int, average word count of top performers>,
    "optimal_tone": "<tone description, e.g. 'technically detailed, with code examples'>",
    "best_openings": ["<opening phrase 1>", "<opening phrase 2>"],
    "avoid_patterns": ["<pattern to avoid 1>", "<pattern to avoid 2>"]
}}
""".strip()


class ReplyLearner:
    """Learns from reply engagement data to improve future drafts."""

    def __init__(self, store: LeadStore, llm_fn: LLMFn | None = None) -> None:
        self._store = store
        self._llm_fn = llm_fn

    def get_few_shot_examples(self, subreddit: str, limit: int = 3) -> list[dict[str, Any]]:
        """Get top performing replies for a subreddit as few-shot examples."""
        return self._store.get_top_performers(subreddit, limit=limit)

    async def analyze_subreddit(self, subreddit: str, min_samples: int = 5) -> dict[str, Any] | None:
        """Analyze top vs bottom replies for a subreddit, generate style profile."""
        if not self._llm_fn:
            return None

        top = self._store.get_top_performers(subreddit, limit=5)
        # Get bottom performers
        all_perf = self._store.conn.execute(
            """SELECT * FROM reply_performance WHERE subreddit = ?
            ORDER BY (reply_upvotes * 3 + reply_replies * 5 + author_replied * 10) ASC
            LIMIT 5""",
            (subreddit,),
        ).fetchall()
        bottom = [dict(r) for r in all_perf]

        if len(top) + len(bottom) < min_samples:
            log.debug("insufficient_data", subreddit=subreddit, samples=len(top) + len(bottom))
            return None

        def format_replies(replies: list[dict]) -> str:
            lines = []
            for r in replies:
                lines.append(
                    f'- [{r.get("reply_upvotes", 0)} upvotes, {r.get("reply_replies", 0)} replies] '
                    f'"{r.get("reply_text", "")[:200]}"'
                )
            return "\n".join(lines) or "(none)"

        prompt = ANALYZE_PROMPT.format(
            subreddit=subreddit,
            top_replies=format_replies(top),
            bottom_replies=format_replies(bottom),
        )

        try:
            response = await self._llm_fn(messages=[{"role": "user", "content": prompt}], temperature=0.3)
            raw = response.get("message", {}).get("content", "")
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start == -1 or end == 0:
                return None
            profile_data = json.loads(raw[start:end])

            # Save to store
            self._store.save_profile(
                subreddit=subreddit,
                what_works=profile_data.get("what_works", ""),
                what_fails=profile_data.get("what_fails", ""),
                optimal_length=profile_data.get("optimal_length", 0),
                optimal_tone=profile_data.get("optimal_tone", ""),
                best_openings=json.dumps(profile_data.get("best_openings", [])),
                avoid_patterns=json.dumps(profile_data.get("avoid_patterns", [])),
                sample_size=len(top) + len(bottom),
            )

            log.info("profile_updated", subreddit=subreddit, sample_size=len(top) + len(bottom))
            return profile_data

        except Exception as exc:
            log.warning("analysis_failed", subreddit=subreddit, error=str(exc))
            return None

    async def run_learning_cycle(self, min_sample_size: int = 5) -> dict[str, Any]:
        """Run the weekly learning cycle across all tracked subreddits."""
        # Find all subreddits with enough data
        rows = self._store.conn.execute(
            """SELECT subreddit, COUNT(*) as cnt FROM reply_performance
            GROUP BY subreddit HAVING cnt >= ?""",
            (min_sample_size,),
        ).fetchall()

        analyzed = 0
        for row in rows:
            sub = row[0] if isinstance(row, tuple) else row["subreddit"]
            profile = await self.analyze_subreddit(sub, min_samples=min_sample_size)
            if profile:
                analyzed += 1

        log.info("learning_cycle_complete", subreddits_analyzed=analyzed)
        return {"subreddits_analyzed": analyzed, "total_subreddits": len(rows)}
```

- [ ] **Step 3: Run tests + commit**

Run: `cd "D:/Jarvis/jarvis complete v20" && ruff check src/jarvis/social/learner.py tests/test_social/test_learner.py && ruff format src/jarvis/social/learner.py tests/test_social/test_learner.py && python -m pytest tests/test_social/test_learner.py -x -q --tb=short`

```bash
git add src/jarvis/social/learner.py tests/test_social/test_learner.py
git commit -m "feat(social): add ReplyLearner — feedback loop + style profiles"
```

---

### Task 7: Inject few-shot + style profiles into scanner.py

**Files:**
- Modify: `src/jarvis/social/scanner.py`
- Modify: `src/jarvis/social/service.py`

- [ ] **Step 1: Extend REPLY_PROMPT with injection points**

In `src/jarvis/social/scanner.py`, replace `REPLY_PROMPT` with:

```python
REPLY_PROMPT = """
You are a helpful expert replying on Reddit.

PRODUCT: {product_name}
YOUR TONE: {reply_tone}

REDDIT POST:
Subreddit: r/{subreddit}
Title: {title}
Text: {body}

{style_context}
{few_shot_context}

Write a short, helpful Reddit reply (max {max_words} words):
- Acknowledge the user's problem
- Briefly explain how {product_name} can help
- No hard sales pitch
- Subreddit-native tone (informal, direct)
- End with the GitHub link: github.com/Alex8791-cyber/cognithor

Reply ONLY with the response text, no meta-comments.
""".strip()
```

- [ ] **Step 2: Update `draft_reply` to accept profile + few-shot**

In `scanner.py`, update `draft_reply` signature and implementation:

```python
    async def draft_reply(
        self,
        post: dict[str, Any],
        config: ScanConfig,
        *,
        style_profile: dict[str, Any] | None = None,
        few_shot_examples: list[dict[str, Any]] | None = None,
    ) -> str:
        if not self._llm_fn:
            return "[No LLM available for reply drafting]"

        style_ctx = ""
        if style_profile:
            style_ctx = (
                f"STYLE PROFILE for r/{post.get('subreddit', '')}:\n"
                f"- What works: {style_profile.get('what_works', '')}\n"
                f"- Avoid: {style_profile.get('what_fails', '')}\n"
                f"- Optimal tone: {style_profile.get('optimal_tone', config.reply_tone)}"
            )

        few_shot_ctx = ""
        if few_shot_examples:
            lines = ["PROVEN REPLIES that performed well in this subreddit:"]
            for i, ex in enumerate(few_shot_examples[:3], 1):
                lines.append(f'{i}. [{ex.get("reply_upvotes", 0)} upvotes] "{ex.get("reply_text", "")[:150]}"')
            few_shot_ctx = "\n".join(lines)

        max_words = style_profile.get("optimal_length", 150) if style_profile else 150

        prompt = REPLY_PROMPT.format(
            product_name=config.product_name,
            reply_tone=style_profile.get("optimal_tone", config.reply_tone) if style_profile else config.reply_tone,
            subreddit=post.get("subreddit", ""),
            title=post.get("title", ""),
            body=(post.get("selftext") or "")[:1000],
            style_context=style_ctx,
            few_shot_context=few_shot_ctx,
            max_words=max_words,
        )
        try:
            response = await self._llm_fn(messages=[{"role": "user", "content": prompt}], temperature=0.4)
            return response.get("message", {}).get("content", "").strip()
        except Exception as exc:
            log.warning("draft_failed", post_id=post.get("id"), error=str(exc))
            return "[Reply draft failed]"
```

- [ ] **Step 3: Update service.py to inject learning data**

In `src/jarvis/social/service.py`, in the `scan()` method, before calling `self._scanner.draft_reply()`, fetch the style profile and few-shot examples:

```python
                # Fetch learning context for this subreddit
                style_profile = self._store.get_profile(sub)
                few_shot = self._store.get_top_performers(sub, limit=3) if style_profile else []

                # 4. Reply-Draft with learning context
                draft = await self._scanner.draft_reply(
                    post, config,
                    style_profile=style_profile,
                    few_shot_examples=few_shot,
                )
```

Also wire `ReplyRefiner`, `PerformanceTracker`, `TemplateManager`, `ReplyLearner` into the service constructor and expose them as methods. Add to `__init__`:

```python
        from jarvis.social.refiner import ReplyRefiner
        from jarvis.social.templates import TemplateManager

        self._refiner = ReplyRefiner(llm_fn=llm_fn)
        self._template_mgr = TemplateManager(self._store)
```

Add service methods:

```python
    async def refine_reply(self, lead_id: str, hint: str = "", variants: int = 0) -> Any:
        lead = self._store.get_lead(lead_id)
        if not lead:
            return None
        post = {"title": lead.title, "selftext": lead.body, "subreddit": lead.subreddit}
        profile = self._store.get_profile(lead.subreddit)
        few_shot = self._store.get_top_performers(lead.subreddit, limit=3)

        if variants > 0:
            return await self._refiner.generate_variants(
                post, self._scan_config.product_name, count=variants,
                style_profile=profile,
            )
        return await self._refiner.refine(
            post, lead.reply_final or lead.reply_draft,
            self._scan_config.product_name,
            user_hint=hint, style_profile=profile, few_shot_examples=few_shot,
        )

    def get_templates(self, subreddit: str = "") -> list[dict[str, Any]]:
        return self._template_mgr.list_for_subreddit(subreddit)

    def apply_template(self, template_id: str, **variables: str) -> str:
        return self._template_mgr.apply(template_id, **variables)

    def create_template(self, name: str, text: str, subreddit: str = "", style: str = "") -> str:
        return self._template_mgr.create(name, text, subreddit, style)

    def delete_template(self, template_id: str) -> None:
        self._template_mgr.delete(template_id)

    def set_feedback(self, lead_id: str, tag: str, note: str = "") -> None:
        self._store.set_feedback(lead_id, tag, note)

    def get_performance(self, lead_id: str) -> dict[str, Any] | None:
        return self._store.get_performance(lead_id)
```

- [ ] **Step 4: Run all social tests**

Run: `cd "D:/Jarvis/jarvis complete v20" && ruff check src/jarvis/social/ tests/test_social/ && ruff format src/jarvis/social/ tests/test_social/ && python -m pytest tests/test_social/ -x -q --tb=short`
Expected: All pass

- [ ] **Step 5: Commit**

```bash
git add src/jarvis/social/scanner.py src/jarvis/social/service.py
git commit -m "feat(social): inject few-shot + style profiles into reply drafting"
```

---

### Task 8: MCP tools + REST endpoints + Cron jobs

**Files:**
- Modify: `src/jarvis/mcp/reddit_tools.py`
- Modify: `src/jarvis/channels/config_routes.py`
- Modify: `src/jarvis/gateway/gateway.py`

- [ ] **Step 1: Add 3 new MCP tools**

In `src/jarvis/mcp/reddit_tools.py`, add after the existing 3 tool registrations:

```python
    async def _reddit_refine(lead_id: str = "", hint: str = "", variants: int = 0) -> str:
        if lead_service is None:
            return json.dumps({"error": "Reddit Lead Service not initialized"})
        if not lead_id:
            return json.dumps({"error": "lead_id is required"})
        result = await lead_service.refine_reply(lead_id, hint=hint, variants=variants)
        if result is None:
            return json.dumps({"error": "Lead not found"})
        if isinstance(result, list):
            return json.dumps({"variants": [{"text": r.text, "style": r.style} for r in result]}, ensure_ascii=False)
        return json.dumps({"text": result.text, "style": result.style, "changes": result.changes_summary}, ensure_ascii=False)

    async def _reddit_discover_subreddits(product_name: str = "", product_description: str = "") -> str:
        if lead_service is None:
            return json.dumps({"error": "Reddit Lead Service not initialized"})
        from jarvis.social.discovery import SubredditDiscovery
        discovery = SubredditDiscovery(llm_fn=lead_service._scanner._llm_fn)
        name = product_name or lead_service._scan_config.product_name
        desc = product_description or lead_service._scan_config.product_description
        results = await discovery.discover(name, desc)
        discovery.close()
        return json.dumps({"suggestions": [
            {"name": s.name, "subscribers": s.subscribers, "posts_per_day": s.posts_per_day,
             "relevance_score": s.relevance_score, "reasoning": s.reasoning, "sample_posts": s.sample_posts}
            for s in results
        ]}, ensure_ascii=False)

    async def _reddit_templates(action: str = "list", subreddit: str = "", name: str = "", text: str = "", template_id: str = "") -> str:
        if lead_service is None:
            return json.dumps({"error": "Reddit Lead Service not initialized"})
        if action == "list":
            return json.dumps({"templates": lead_service.get_templates(subreddit)}, ensure_ascii=False)
        elif action == "create":
            tid = lead_service.create_template(name, text, subreddit)
            return json.dumps({"id": tid, "status": "created"})
        elif action == "delete":
            lead_service.delete_template(template_id)
            return json.dumps({"status": "deleted"})
        return json.dumps({"error": f"Unknown action: {action}"})

    mcp_client.register_builtin_handler(
        "reddit_refine", _reddit_refine,
        description="Refine a reply draft via LLM. Set variants>0 to generate multiple options.",
        parameters={
            "lead_id": {"type": "string", "description": "Lead ID"},
            "hint": {"type": "string", "description": "Optional: direction for refinement"},
            "variants": {"type": "integer", "description": "Generate N variants (0=refine only)"},
        },
    )
    mcp_client.register_builtin_handler(
        "reddit_discover_subreddits", _reddit_discover_subreddits,
        description="Discover relevant subreddits for a product via LLM + Reddit validation.",
        parameters={
            "product_name": {"type": "string", "description": "Product name (default: config)"},
            "product_description": {"type": "string", "description": "Product description (default: config)"},
        },
    )
    mcp_client.register_builtin_handler(
        "reddit_templates", _reddit_templates,
        description="Manage reply templates. Actions: list, create, delete.",
        parameters={
            "action": {"type": "string", "description": "list, create, or delete"},
            "subreddit": {"type": "string", "description": "Filter by subreddit (list) or assign (create)"},
            "name": {"type": "string", "description": "Template name (create)"},
            "text": {"type": "string", "description": "Template text (create)"},
            "template_id": {"type": "string", "description": "Template ID (delete)"},
        },
    )
    log.info("reddit_tools_registered", tools=6)
```

Update the final log line from `tools=3` to `tools=6`.

Add the new tools to gatekeeper GREEN set:

In `src/jarvis/core/gatekeeper.py`, add `"reddit_refine"`, `"reddit_discover_subreddits"`, `"reddit_templates"` to the `green_tools` set (near the existing `reddit_scan`, `reddit_leads` entries).

- [ ] **Step 2: Add REST endpoints**

In `src/jarvis/channels/config_routes.py`, inside `_register_social_routes`, add after the existing 6 endpoints:

```python
    @app.post("/api/v1/leads/{lead_id}/refine", dependencies=deps)
    async def refine_lead(lead_id: str, request: Request) -> dict[str, Any]:
        svc = _get_service()
        if not svc:
            return {"error": "Reddit Lead Service not initialized", "status": 503}
        try:
            body = await request.json()
        except Exception:
            body = {}
        hint = body.get("hint", "")
        variants = body.get("variants", 0)
        result = await svc.refine_reply(lead_id, hint=hint, variants=variants)
        if result is None:
            raise HTTPException(404, "Lead not found")
        if isinstance(result, list):
            return {"variants": [{"text": r.text, "style": r.style} for r in result]}
        return {"text": result.text, "style": result.style, "changes": result.changes_summary}

    @app.get("/api/v1/leads/{lead_id}/performance", dependencies=deps)
    async def get_lead_performance(lead_id: str) -> dict[str, Any]:
        svc = _get_service()
        if not svc:
            return {"error": "Reddit Lead Service not initialized", "status": 503}
        perf = svc.get_performance(lead_id)
        if perf is None:
            return {"performance": None}
        from jarvis.social.tracker import engagement_score
        perf["engagement_score"] = engagement_score(
            perf.get("reply_upvotes", 0), perf.get("reply_replies", 0),
            bool(perf.get("author_replied", 0)), perf.get("feedback_tag", ""),
        )
        return {"performance": perf}

    @app.patch("/api/v1/leads/{lead_id}/feedback", dependencies=deps)
    async def set_lead_feedback(lead_id: str, request: Request) -> dict[str, Any]:
        svc = _get_service()
        if not svc:
            return {"error": "Reddit Lead Service not initialized", "status": 503}
        body = await request.json()
        svc.set_feedback(lead_id, tag=body.get("tag", ""), note=body.get("note", ""))
        return {"status": "ok"}

    @app.post("/api/v1/leads/discover-subreddits", dependencies=deps)
    async def discover_subreddits(request: Request) -> dict[str, Any]:
        svc = _get_service()
        if not svc:
            return {"error": "Reddit Lead Service not initialized", "status": 503}
        try:
            body = await request.json()
        except Exception:
            body = {}
        from jarvis.social.discovery import SubredditDiscovery
        discovery = SubredditDiscovery(llm_fn=svc._scanner._llm_fn)
        name = body.get("product_name", svc._scan_config.product_name)
        desc = body.get("product_description", svc._scan_config.product_description)
        results = await discovery.discover(name, desc)
        discovery.close()
        return {"suggestions": [
            {"name": s.name, "subscribers": s.subscribers, "posts_per_day": s.posts_per_day,
             "relevance_score": s.relevance_score, "reasoning": s.reasoning, "sample_posts": s.sample_posts}
            for s in results
        ]}

    @app.get("/api/v1/leads/templates", dependencies=deps)
    async def list_templates(subreddit: str = "") -> dict[str, Any]:
        svc = _get_service()
        if not svc:
            return {"error": "Reddit Lead Service not initialized", "status": 503}
        return {"templates": svc.get_templates(subreddit)}

    @app.post("/api/v1/leads/templates", dependencies=deps)
    async def create_template(request: Request) -> dict[str, Any]:
        svc = _get_service()
        if not svc:
            return {"error": "Reddit Lead Service not initialized", "status": 503}
        body = await request.json()
        tid = svc.create_template(
            name=body.get("name", ""),
            text=body.get("text", ""),
            subreddit=body.get("subreddit", ""),
            style=body.get("style", ""),
        )
        return {"id": tid, "status": "created"}

    @app.delete("/api/v1/leads/templates/{template_id}", dependencies=deps)
    async def delete_template(template_id: str) -> dict[str, Any]:
        svc = _get_service()
        if not svc:
            return {"error": "Reddit Lead Service not initialized", "status": 503}
        svc.delete_template(template_id)
        return {"status": "deleted"}
```

IMPORTANT: Put `/leads/discover-subreddits` and `/leads/templates` BEFORE `/leads/{lead_id}` routes to avoid path parameter capture.

- [ ] **Step 3: Add 2 new cron jobs**

In `src/jarvis/gateway/gateway.py`, after the existing `reddit_lead_scan` cron block, add:

```python
            # Reddit Reply Performance Tracker (every 6h)
            try:
                self._cron_engine.add_system_job(
                    name="reddit_reply_tracker",
                    schedule="0 */6 * * *",
                    callback=self._track_reddit_replies,
                )
                log.info("reddit_tracker_cron_registered")
            except Exception:
                log.debug("reddit_tracker_cron_failed", exc_info=True)

            # Reddit Style Learner (weekly, Sunday 3am)
            try:
                self._cron_engine.add_system_job(
                    name="reddit_style_learner",
                    schedule="0 3 * * 0",
                    callback=self._run_reddit_learner,
                )
                log.info("reddit_learner_cron_registered")
            except Exception:
                log.debug("reddit_learner_cron_failed", exc_info=True)
```

Add the callback methods to the Gateway class:

```python
    async def _track_reddit_replies(self) -> None:
        svc = getattr(self, "_reddit_lead_service", None)
        if not svc:
            return
        from jarvis.social.tracker import PerformanceTracker
        tracker = PerformanceTracker(store=svc._store)
        try:
            result = await tracker.track_all()
            log.info("reddit_tracking_complete", **result)
        finally:
            tracker.close()

    async def _run_reddit_learner(self) -> None:
        svc = getattr(self, "_reddit_lead_service", None)
        if not svc:
            return
        from jarvis.social.learner import ReplyLearner
        learner = ReplyLearner(store=svc._store, llm_fn=svc._scanner._llm_fn)
        result = await learner.run_learning_cycle()
        log.info("reddit_learning_complete", **result)
```

- [ ] **Step 4: Run lint + all tests**

Run: `cd "D:/Jarvis/jarvis complete v20" && ruff check src/ tests/ && ruff format src/ tests/ && python -m pytest tests/ -x -q --tb=short --ignore=tests/test_channels/test_voice_ws_bridge.py`
Expected: All 13,000+ tests pass

- [ ] **Step 5: Run flutter analyze**

Run: `cd "D:/Jarvis/jarvis complete v20/flutter_app" && flutter analyze`
Expected: No issues found

- [ ] **Step 6: Commit**

```bash
git add src/jarvis/mcp/reddit_tools.py src/jarvis/channels/config_routes.py src/jarvis/gateway/gateway.py src/jarvis/core/gatekeeper.py
git commit -m "feat(social): MCP tools + REST endpoints + cron jobs for v2 intelligence layer

3 new MCP tools (refine, discover, templates), 8 new REST endpoints,
2 new cron jobs (tracker 6h, learner weekly). Gatekeeper GREEN for new tools."
```

---

## Self-Review

**Spec coverage:**
- [x] Component 1 (LLM Refinement) → Task 2 + Task 7 (service wiring)
- [x] Component 2 (Queue/Wizard) → Plan B (Flutter)
- [x] Component 3 (Performance Tracking) → Task 3 + Task 8 (cron)
- [x] Component 4 (Subreddit Discovery) → Task 4 + Task 8 (MCP + REST)
- [x] Component 5 (Reply Templates) → Task 5 + Task 8 (MCP + REST)
- [x] Component 6 (Feedback Learning) → Task 6 + Task 7 (injection) + Task 8 (cron)
- [x] Auto-Post behavior → existing toggle, wired in wizard (Plan B)

**Placeholder scan:** No TBDs. All code blocks complete.

**Type consistency:** `RefinedReply`, `SubredditSuggestion`, `TemplateManager`, `ReplyLearner`, `PerformanceTracker` used consistently. `engagement_score()` function used in both tracker.py and config_routes.py.
