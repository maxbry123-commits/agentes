# Reddit Lead Hunter v2 — Intelligence Layer

**Date:** 2026-04-09
**Status:** Approved

## Problem

The Reddit Lead Hunter scans and scores posts, but the reply drafts are generic one-shots with no learning. There's no way to refine replies, no performance tracking, no template reuse, no subreddit discovery, and no feedback loop. Users must manually scroll through leads instead of processing them efficiently.

## Design

6 interconnected subsystems that transform the lead workflow into a self-improving system:

```
Scan → Score → Draft → Refine → Queue → Reply → Track → Learn → better Drafts
```

### Component 1: LLM Reply Refinement

**`src/jarvis/social/refiner.py`**

`ReplyRefiner` service with two methods:

- `refine(lead, current_draft, user_hint?) → RefinedReply` — LLM rewrites the draft using: original post context, subreddit style profile (from Component 6), top 3 historical replies as few-shot. Optional `user_hint` steers direction ("make it shorter", "more technical").

- `generate_variants(lead, count=3) → list[RefinedReply]` — generates N reply variants with distinct styles (technical-detailed, casual-short, question-as-answer). User picks the best.

`RefinedReply` model: `text`, `style` (technical/casual/question/refined), `changes_summary`.

MCP tool: `reddit_refine` — Planner can trigger via chat.
REST: `POST /api/v1/leads/{id}/refine` with `{hint?, variants?: int}`

### Component 2: Lead Queue / Wizard Mode

**Flutter: `lib/widgets/leads/lead_wizard.dart`**

Full-screen wizard for sequential lead processing:

- Shows one lead at a time with score, reasoning, reply draft
- Progress bar: "Lead 3/12 — 25%"
- Action buttons: Improve (LLM refine), Variants (3 options), Template (pick from saved)
- Navigation: Archive / Skip / Copy & Post → auto-advance to next lead
- Keyboard shortcuts: A=Archive, S=Skip, R=Reply, I=Improve, V=Variants, Enter=Confirm
- Filters on `status=new`, sorted by score descending
- Summary screen at the end: "12 leads processed: 5 replied, 4 skipped, 3 archived"

Accessed via "Process Queue" button on the main Leads screen.

### Component 3: Reply Performance Tracking

**`src/jarvis/social/tracker.py`**

`PerformanceTracker` service:

**Automatic re-scanning** (Cron every 6h): For all leads with `status=replied`:
1. Fetch original post via Reddit JSON
2. Search comments for our reply (fuzzy text match, 80% threshold)
3. Record: upvotes on our comment, replies to our comment, whether post author responded, post upvote delta since reply

**Manual feedback**: User sets tags via UI: `converted` (user tested product), `conversation` (dialog started), `deleted` (comment removed), `ignored` (no reaction), `negative` (downvotes)

**Engagement score**: `reply_upvotes * 3 + reply_replies * 5 + author_replied * 10 + (converted) * 20`, normalized 0-100.

SQLite table: `reply_performance` with automatic metrics + manual feedback fields.

REST: `GET /api/v1/leads/{id}/performance`, `PATCH /api/v1/leads/{id}/feedback`

Cron: `reddit_reply_tracker` every 6h, tracks leads for 7 days after reply.

### Component 4: Smart Subreddit Discovery

**`src/jarvis/social/discovery.py`**

`SubredditDiscovery` service:

1. LLM generates 20 subreddit candidates from product description
2. For each: Reddit JSON check (`/r/{name}/about.json`) — exists? subscribers? active?
3. Fetch 5 recent posts per candidate, LLM scores relevance 0-100
4. Rank by: relevance × posts_per_day × log(subscribers)
5. Return top 10 with reasoning and sample posts

`SubredditSuggestion` model: `name`, `subscribers`, `posts_per_day`, `relevance_score`, `reasoning`, `sample_posts`.

MCP tool: `reddit_discover_subreddits`
REST: `POST /api/v1/leads/discover-subreddits`
Flutter: "Discover" button in Social Config with checkbox selection.

### Component 5: Reply Templates

**`src/jarvis/social/templates.py`**

SQLite table `reply_templates`: `id`, `name`, `template_text`, `subreddit` (empty=universal), `style`, `use_count`, `avg_engagement`, `created_from_lead`, `created_at`.

- **Auto-generation**: When a reply reaches engagement score > 85, auto-save as template. Score > 70: prompt user to save.
- **Template matching**: During draft generation, check for templates matching the current subreddit. Offer as starting point.
- **Template variables**: `{product_name}`, `{post_title}`, `{author}`, `{subreddit}` — replaced when applied.

REST: `GET /api/v1/leads/templates`, `POST /api/v1/leads/templates`, `DELETE /api/v1/leads/templates/{id}`

### Component 6: Feedback Learning Loop

**`src/jarvis/social/learner.py`**

The core intelligence — `ReplyLearner` service:

**Subreddit Style Profile** (per subreddit):
- `what_works`: LLM-generated summary of successful patterns
- `what_fails`: patterns to avoid
- `optimal_length`: average word count of top performers
- `optimal_tone`: extracted from top replies
- `best_openings`: successful first sentences
- `avoid_patterns`: phrases that correlate with low engagement
- `sample_size`: how many replies analyzed

**Learning cycle** (Cron, weekly):
1. Fetch all leads with engagement data (minimum 10 tracked replies)
2. Group by subreddit
3. Per subreddit: LLM analyzes top-5 vs bottom-5 replies
4. Generate/update `SubredditStyleProfile`
5. Auto-adjust `reply_tone` in SocialConfig if clear trend detected
6. Log: "Tone for r/LocalLLaMA adjusted: 'casual' → 'technically detailed, with code examples'"

**Few-shot injection** into reply drafting prompt:
```
Here are 3 replies that performed well in r/{subreddit}:
1. [Engagement 92] "{reply_text}" → 8 upvotes, 3 replies, author responded
2. [Engagement 85] "{reply_text}" → 5 upvotes, 1 reply
3. [Engagement 78] "{reply_text}" → 4 upvotes

Style profile for r/{subreddit}:
- What works: {what_works}
- Avoid: {what_fails}
- Optimal length: ~{optimal_length} words
```

SQLite table: `subreddit_profiles`.

### Auto-Post Behavior

The existing `reddit_auto_post` toggle in Social Config controls the wizard behavior:
- **Off (default)**: "Post Reply" copies to clipboard + opens browser
- **On**: "Post Reply" uses Playwright to auto-post, with Approval dialog before each post
- In wizard mode with auto-post on: after "Copy & Post" → Playwright posts → auto-advance (no manual browser step)

### Data Flow

```
Scan → Score → Draft
                 ↓
        [Few-Shot from Top Replies]      ← Learner
        [Style Profile injection]        ← Learner
                 ↓
        Queue/Wizard → User reviews
                 ↓
        [Refine] → LLM + Style Profile
        [Variants] → 3 options
        [Template] → proven template
                 ↓
        Reply posted (clipboard or auto)
                 ↓
        Tracker (6h Cron)
            → Upvotes, Replies, Author-Response
            → Manual Feedback Tags
                 ↓
        Learner (weekly Cron)
            → Style Profiles updated
            → Top/Bottom as Few-Shot
            → reply_tone auto-adjusted
                 ↓
        Next scan → better drafts
```

### Cron Jobs

| Job | Schedule | Purpose |
|-----|----------|---------|
| `reddit_lead_scan` | */30 * * * * | Scan subreddits (existing) |
| `reddit_reply_tracker` | 0 */6 * * * | Track reply performance |
| `reddit_style_learner` | 0 3 * * 0 | Weekly learning cycle (Sunday 3am) |

### Files to Create/Modify

**Backend (Plan A):**

| File | Change |
|------|--------|
| `src/jarvis/social/refiner.py` | **New** — LLM refinement + variants |
| `src/jarvis/social/tracker.py` | **New** — performance tracking + re-scanning |
| `src/jarvis/social/discovery.py` | **New** — subreddit discovery |
| `src/jarvis/social/templates.py` | **New** — template store |
| `src/jarvis/social/learner.py` | **New** — feedback learning loop |
| `src/jarvis/social/store.py` | Add 3 tables: reply_performance, reply_templates, subreddit_profiles |
| `src/jarvis/social/scanner.py` | Inject few-shot + style profile into draft prompt |
| `src/jarvis/mcp/reddit_tools.py` | Add: reddit_refine, reddit_discover_subreddits, reddit_templates |
| `src/jarvis/channels/config_routes.py` | ~8 new endpoints |
| `src/jarvis/gateway/gateway.py` | 2 new cron jobs (tracker, learner) |
| `tests/test_social/test_refiner.py` | **New** |
| `tests/test_social/test_tracker.py` | **New** |
| `tests/test_social/test_discovery.py` | **New** |
| `tests/test_social/test_templates.py` | **New** |
| `tests/test_social/test_learner.py` | **New** |

**Flutter (Plan B):**

| File | Change |
|------|--------|
| `lib/widgets/leads/lead_wizard.dart` | **New** — queue wizard UI |
| `lib/widgets/leads/refine_panel.dart` | **New** — refinement + variants UI |
| `lib/widgets/leads/template_picker.dart` | **New** — template selection |
| `lib/widgets/leads/performance_badge.dart` | **New** — engagement score badge |
| `lib/widgets/leads/feedback_dialog.dart` | **New** — manual feedback tags |
| `lib/screens/reddit_leads_screen.dart` | Add "Process Queue" button, performance view |
| `lib/providers/reddit_leads_provider.dart` | Add refine, variants, templates, feedback methods |
| `lib/services/api_client.dart` | ~8 new methods |
| `lib/l10n/app_{en,de,zh,ar}.arb` | ~20 new i18n keys |

### Not In Scope
- A/B testing (multiple replies on same post) — ethically problematic
- Cross-platform (Twitter/HN/Discord) — saved for later, see memory
- Sentiment analysis beyond engagement score
