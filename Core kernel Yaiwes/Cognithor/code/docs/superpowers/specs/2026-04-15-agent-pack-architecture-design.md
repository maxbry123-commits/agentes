# Agent Pack Architecture — Design Spec

**Date:** 2026-04-15
**Author:** Alexander Söllner (with Claude)
**Status:** Draft, pending user review
**Related issues:** —

---

## 1. Executive Summary

Cognithor is growing a paid-pack ecosystem on top of its Apache-2.0 core. This spec defines the architecture: a plugin interface for agent packs, a private GitHub source-of-truth repository for pack code and marketing content, an auto-syncing website that fetches the pack catalog at build time, and a Lemon-Squeezy-based commerce pipeline that delivers zip downloads after purchase.

The first real pack is **Reddit Lead Hunter Pro** ($79, one-time), extracted from the current `src/cognithor/social/` module. Three bundled free packs (HN, Discord, RSS Lead Hunter) are extracted at the same time so all lead sources flow through the same pack interface. The extraction is accompanied by a refactor of the `social/` code into a generic `cognithor.leads.sdk` that exposes a `LeadSource` registry; packs register themselves as sources.

The design is explicitly forward-compatible with the Q4 2026 community creator marketplace (70/30 revenue share) that the website already markets. MVP does not ship creator self-service, but the pack manifest, publisher model, and repository layout are designed so that Q4 work is a feature addition, not a rewrite.

## 2. Problem Statement

**Current state.** All lead-generation code lives in `src/cognithor/social/` inside the Apache-2.0 Cognithor core repo. The code works, ships with Core, and includes Reddit-specific assets (50 reply templates, a Playwright auto-poster, a style learner) that the website markets as a $79 paid pack called "Reddit Lead Hunter Pro." The marketing copy is published; the code is free and open.

**Conflicts this causes.**

- Anyone reading the public Core repo can see the code they are being asked to pay for.
- Any contribution to `src/cognithor/social/` by an outside contributor must be Apache-2.0 — making it harder to later relicense or monetize.
- There is no infrastructure for installing, updating, or verifying third-party code. The community skill marketplace (`src/cognithor/skills/community/`) handles a different use case (free user-contributed skills) and is not a substitute.
- The website lists four "coming-soon" packs but has no code path that would install them if built.

**Goal.** Cleanly separate paid packs from Core, provide a plugin architecture that all packs (free and paid) flow through, and build the commerce and auto-sync pipelines required to operate a small-scale pack store without ongoing manual work.

## 3. High-Level Architecture

Three repositories work together:

```
┌─────────────────────────────┐      ┌──────────────────────────────┐
│ cognithor (public, Apache)  │      │ cognithor-packs (PRIVATE)    │
│                             │      │                              │
│  cognithor.packs.interface  │◄─────┤  reddit-lead-hunter-pro/     │
│  cognithor.packs.loader     │ load │    pack.py  manifest  eula   │
│  cognithor.packs.installer  │      │    src/...  catalog/*.mdx    │
│  cognithor.leads.sdk        │      │  hn-lead-hunter/  (free)     │
│                             │      │  discord-lead-hunter/ (free) │
│  CLI: cognithor pack ...    │      │  rss-lead-hunter/     (free) │
└─────────────┬───────────────┘      │  index.json (CI-generated)   │
              │                      └──────────────┬───────────────┘
              │                                     │ GH API
              │ zip from LS CDN                     │ (build-time)
              ▼                                     ▼
        ┌──────────┐                    ┌────────────────────────┐
        │  USER    │◄──────thank-you────│ cognithor-site (public)│
        │  machine │    page + zip URL  │ Next.js on Vercel      │
        └──────────┘                    │ /packs, /packs/[slug]  │
              ▲                         └────────────────────────┘
              │ LS checkout                         ▲
              └─────────────────────────────────────┘
                 Lemon Squeezy (Merchant of Record)
```

**Flows:**

- **Site build flow.** A GitHub Action in `cognithor-packs` regenerates `index.json` on every push, then calls a Vercel Deploy Hook. Vercel rebuilds `cognithor-site`. At build time, Next.js fetches `index.json` + each pack's `catalog/catalog.mdx` via the GitHub REST API using a fine-grained PAT (build-time only; never exposed to the browser). The pack listing on `/packs` and each `/packs/[slug]` detail page are fully statically generated.

- **Purchase flow.** The user clicks "Install Pack" on `/packs/reddit-lead-hunter`. The button links to a Lemon Squeezy checkout URL. After successful payment, Lemon Squeezy redirects to `https://cognithor.com/packs/reddit-lead-hunter/installed?order_id={order_id}&token={token}`. The Next.js route reads the query params and renders a thank-you page with a copy-to-clipboard install command. Lemon Squeezy also emails the customer the same info.

- **Install flow.** The user runs `cognithor pack install <url>` in their terminal. The CLI streams the zip, extracts it to `~/.cognithor/packs/<namespace>/<pack_id>/`, validates `pack_manifest.json`, verifies the EULA SHA-256, prompts the user to accept the EULA, persists acceptance, and registers the pack with the running Cognithor instance (if any). On next Cognithor startup, the pack loader imports the pack's `pack.py`, calls `Pack.register(context)`, and the pack's `LeadSource` (or other contributions) becomes available to the Gateway and the Flutter UI.

## 4. Core Components

### 4.1 `cognithor.packs.interface` — AgentPack base class and PackManifest

**`cognithor/packs/interface.py`** defines the contract packs implement.

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field


class Publisher(BaseModel):
    """Publisher metadata. For MVP every pack is published by cognithor-official.
    The model is already multi-publisher so the Q4 community marketplace can
    add new publishers without a schema change.
    """
    id: str                       # e.g. "cognithor-official"
    display_name: str
    website: str | None = None
    contact_email: str | None = None
    payout_provider: str | None = None  # "lemonsqueezy" | "stripe-connect" (Phase 2)


class RevenueShare(BaseModel):
    """How sales revenue is split. For own packs this is cosmetic; for future
    community packs the loader enforces it when wiring payout records.
    """
    creator: int = 70   # percentage
    platform: int = 30  # percentage


class PricingTier(BaseModel):
    """One pricing tier (indie, commercial, ...). Used for price anchoring."""
    list_price: int               # visually struck-through, e.g. 149
    launch_price: int             # active sale price, e.g. 79
    post_launch_price: int        # what it rises to after launch_cap hit
    currency: str = "USD"
    launch_cap: int               # seats available at launch_price


class PackManifest(BaseModel):
    """Validated manifest stored as pack_manifest.json at the pack root."""
    schema_version: int = 1
    namespace: str                # "cognithor-official" | "community-<id>"
    pack_id: str                  # "reddit-lead-hunter-pro" (unique within namespace)
    version: str                  # semver, "1.2.0"
    display_name: str
    description: str
    license: str                  # "proprietary" | "apache-2.0" | "mit" | ...
    min_cognithor_version: str    # ">=0.82.0"
    max_cognithor_version: str | None = None
    entrypoint: str = "pack.py"   # relative path to the module with a Pack class
    eula_sha256: str              # hex digest of the eula.md bundled with the pack
    publisher: Publisher
    revenue_share: RevenueShare = Field(default_factory=RevenueShare)
    # Declarative UI contributions for the generic LeadsScreen (see 4.5).
    lead_sources: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)   # MCP tool names registered
    # Commerce — one checkout URL per pricing tier. None for free packs.
    checkout_url: str | None = None              # primary (indie) tier
    commercial_checkout_url: str | None = None
    pricing: dict[str, PricingTier] = Field(default_factory=dict)   # keys: "indie", "commercial"


class PackContext(BaseModel):
    """What a pack's register() call can touch. A narrow facade over Gateway."""
    class Config:
        arbitrary_types_allowed = True
    gateway: Any                  # the running Gateway instance
    config: Any                   # the Cognithor runtime config
    mcp_client: Any | None        # for register_tool
    leads: Any                    # cognithor.leads.sdk.LeadService


class AgentPack(ABC):
    """Base class all packs inherit from."""

    manifest: PackManifest

    def __init__(self, manifest: PackManifest) -> None:
        self.manifest = manifest

    @abstractmethod
    def register(self, context: PackContext) -> None:
        """Wire the pack into a running Cognithor instance.

        Called once at startup after the loader has validated the pack.
        Implementations typically register MCP tools, a LeadSource, or REST
        routes here. Must be idempotent (loader may call it again on reload).
        """

    def unregister(self, context: PackContext) -> None:
        """Cleanup on unload. Default is no-op. Subclasses override if they
        hold resources (database connections, background tasks, etc.)."""
```

**Why a `PackContext` facade:** we want packs to have a stable API even as the Gateway internals get refactored. Directly passing `gateway` would mean every Gateway change breaks all packs. The context exposes only the documented interfaces.

### 4.2 `cognithor.packs.loader` — discovery, validation, and lifecycle

**`cognithor/packs/loader.py`** scans `~/.cognithor/packs/` for installed packs and loads them at Cognithor startup.

```python
class PackLoadError(Exception):
    """Raised when a pack fails to load. Never propagated — always logged and
    swallowed so one broken pack cannot crash Core."""


class PackLoader:
    def __init__(self, packs_dir: Path, cognithor_version: str) -> None:
        self._packs_dir = packs_dir
        self._cognithor_version = cognithor_version
        self._loaded: dict[str, AgentPack] = {}   # qualified_id -> instance

    def discover(self) -> list[PackManifest]:
        """Walk packs_dir, return a validated list of manifests.

        Layout: packs_dir/<namespace>/<pack_id>/pack_manifest.json
        Invalid manifests are logged and skipped, not raised.
        """

    def load_all(self, context: PackContext) -> None:
        """Discover, validate, sort by dependency order, call register() on each.
        Errors in one pack never prevent others from loading."""

    def unload_all(self, context: PackContext) -> None:
        """Call unregister() on each loaded pack in reverse order."""

    def reload(self, qualified_id: str, context: PackContext) -> None:
        """Unload + load a specific pack by '<namespace>/<pack_id>'."""
```

**Validation steps, in order:**

1. `pack_manifest.json` exists and parses as `PackManifest`.
2. `eula.md` exists and its SHA-256 matches `manifest.eula_sha256`. Mismatch → skip with loud warning (`pack_eula_hash_mismatch`).
3. `manifest.min_cognithor_version` ≤ running version ≤ `manifest.max_cognithor_version`. Version-range failure → skip with explicit upgrade/downgrade hint.
4. `.eula_accepted` file exists in the pack directory. Missing → skip with hint to run `cognithor pack accept-eula <pack>`. (Installer creates this file during install; loader never prompts.)
5. Python import of `entrypoint` module succeeds, the module exposes a top-level `Pack` class, and that class inherits from `AgentPack`.
6. Instantiate `Pack(manifest)` and call `register(context)`.

All failures are logged via `cognithor.utils.logging.get_logger("cognithor.packs.loader")` with structured fields (`pack_id`, `namespace`, `version`, `reason`, `exc_info`). **None of them raise.** A broken third-party pack must never take down Core.

**Import isolation.** Packs are imported via `importlib.util.spec_from_file_location` with a unique module name per pack (`cognithor_packs.<ns_sanitized>.<id_sanitized>`). Packs share the same Python interpreter and can therefore, in theory, import arbitrary modules. This is NOT a security boundary in MVP; packs are trusted because (a) `cognithor-official` packs are written by us, (b) community packs are gated by manual review pre-Q4, (c) the Gatekeeper already audits tool calls. Sandboxing is explicitly out of scope (see § 11).

**Dependency order.** MVP does not support pack-to-pack dependencies. The loader sorts alphabetically for determinism. Inter-pack dependencies are Phase 2 scope.

### 4.3 `cognithor.packs.installer` — CLI + zip extraction + EULA click-through

**`cognithor/packs/installer.py`** implements the install/upgrade/remove primitives. The `cognithor pack` CLI surface is a thin wrapper over this module.

```
cognithor pack install <path-or-url>   # install from local zip or HTTPS URL
cognithor pack list                    # show installed packs
cognithor pack remove <pack_id>        # remove an installed pack
cognithor pack update <pack_id>        # MVP: prints "re-install with new url"
                                       # Phase 2: auto-fetch via license key
cognithor pack accept-eula <pack_id>   # re-accept EULA after update
```

**Install flow:**

1. Resolve source. Local path → open. URL → stream via `httpx.stream(...)` with progress bar; write to a temp file under `tempfile.gettempdir()`.
2. Compute SHA-256 of the downloaded zip; log it.
3. Open as zip, extract to a temp directory, verify `pack_manifest.json` and `eula.md` exist at the zip root.
4. Parse manifest, validate as in § 4.2.
5. Check for existing install at `~/.cognithor/packs/<namespace>/<pack_id>/`. If present and newer or equal, print "already installed" and abort. If older, this is an upgrade: proceed but warn.
6. **EULA click-through.** Read `eula.md`, compare SHA-256 to `manifest.eula_sha256`. Print the EULA text to the terminal, then prompt `Accept these terms? [y/N]`. Abort on `N`.
7. Move the validated directory to `~/.cognithor/packs/<namespace>/<pack_id>/` (atomic rename where possible; fall back to copy+delete).
8. Write `.eula_accepted` next to the manifest with: current timestamp, user identity (`getpass.getuser()`), EULA SHA-256, installer version.
9. Print success message with `namespace/pack_id@version` and a hint to restart Cognithor.

**Upgrade handling.** If a newer version replaces an older one, the installer:
- Preserves any per-pack user data under `~/.cognithor/packs/<namespace>/<pack_id>/_data/` (if the pack writes data there — a convention, not enforced).
- Requires re-acceptance of the EULA if the new manifest's `eula_sha256` differs from the old acceptance record.
- Does NOT trigger a hot-reload inside a running Cognithor instance (MVP: restart required). Hot reload is Phase 2.

### 4.4 EULA handling

Every pack ships an `eula.md` file (can be a symlink to a shared template in `_template/`, but gets inlined into the zip at packaging time so the on-disk hash is stable). The manifest pins the SHA-256. The installer refuses to install packs where the hash does not match, and the loader refuses to load packs whose `.eula_accepted` record does not match the current EULA hash.

**EULA content for MVP:** one shared template at `cognithor-packs/_template/eula.md` that `cognithor-official` packs inherit. The template covers:
- License scope (one user / one commercial entity)
- Allowed use (local-first, no redistribution)
- No warranty
- Refund window (14 days, per Lemon Squeezy defaults)
- Telemetry (none)
- Forward-compat clause: the EULA version is embedded, updates may issue new versions

**Community packs (Phase 2)** will submit their own EULA; the review process includes an EULA review step.

### 4.5 `cognithor.leads.sdk` — the generic Lead SDK in Core

This is the single biggest refactor in MVP scope. The current `src/cognithor/social/` module has the right **capability set** but the wrong **shape**: `RedditLeadService.__init__` hardcodes `RedditScanner`, the service methods are Reddit-shaped (`scan(subreddits=...)`), and the Flutter screen is `RedditLeadsScreen`. After the refactor, the shape becomes source-agnostic and Reddit lives in a pack.

**New module layout:**

```
src/cognithor/leads/
├── __init__.py
├── models.py           # Lead, LeadStatus, LeadStats, ScanResult (from social/models.py)
├── store.py            # LeadStore (from social/store.py, unchanged)
├── service.py          # LeadService (rewrite of social/service.py, source-agnostic)
├── source.py           # LeadSource abstract base class (new)
└── registry.py         # SourceRegistry (new)
```

**`LeadSource` interface:**

```python
class LeadSource(ABC):
    """A lead source — Reddit, HN, Discord, RSS, etc."""
    source_id: str           # "reddit" | "hn" | "discord" | "rss" | ...
    display_name: str        # "Reddit" (for UI)
    icon: str                # Material icon name OR data URL
    color: str               # hex, for UI accent
    capabilities: set[str]   # {"scan", "draft_reply", "auto_post", ...}

    @abstractmethod
    async def scan(
        self,
        *,
        config: dict[str, Any],     # source-specific config dict from ConfigProvider
        product: str,
        product_description: str,
        min_score: int,
    ) -> list[Lead]:
        ...

    # Optional capabilities — default implementations raise NotImplementedError.
    async def draft_reply(self, lead: Lead, *, tone: str) -> str: ...
    async def refine_reply(self, lead: Lead, draft: str) -> str: ...
    async def post_reply(self, lead: Lead, text: str) -> None: ...
```

**`LeadService` becomes source-agnostic:**

```python
class LeadService:
    def __init__(self, store: LeadStore, llm_fn: Any | None = None) -> None:
        self._store = store
        self._llm_fn = llm_fn
        self._registry = SourceRegistry()

    def register_source(self, source: LeadSource) -> None: ...
    def unregister_source(self, source_id: str) -> None: ...
    def list_sources(self) -> list[LeadSource]: ...

    async def scan(
        self,
        *,
        source_id: str | None = None,   # None = all registered
        min_score: int = 60,
        trigger: str = "cli",
    ) -> ScanResult: ...
```

**Registration happens via `PackContext.leads`.** A pack's `register(context)` method does:

```python
class Pack(AgentPack):
    def register(self, context: PackContext) -> None:
        from .reddit_source import RedditLeadSource
        context.leads.register_source(RedditLeadSource(llm_fn=context.gateway._ollama.chat))
```

**REST surface** in Core becomes source-agnostic:

```
GET  /api/v1/leads/sources                      # list registered sources + capabilities
POST /api/v1/leads/scan                         # {source_id?: str, min_score?: int}
GET  /api/v1/leads                              # existing, unchanged
GET  /api/v1/leads/stats                        # unchanged
POST /api/v1/leads/{lead_id}/reply              # routes to source.draft_reply by lead.source_id
POST /api/v1/leads/{lead_id}/refine             # routes to source.refine_reply
```

The existing `/api/v1/leads/scan/rss`, `/api/v1/leads/scan/hn`, `/api/v1/leads/scan/discord` endpoints from Issue #113 are replaced by the single `/scan?source_id=rss` form. The old forms stay as thin aliases for one release cycle (deprecation warning logged) so existing integrations don't break mid-flight.

**`/api/v1/leads/engine-status`** (from #113) is replaced by `/api/v1/leads/sources` — if the list is empty, the Flutter sidebar gating in `main_shell.dart` continues to hide the Leads tab exactly as today.

**Flutter LeadsScreen refactor.** The current `reddit_leads_screen.dart` becomes `leads_screen.dart`. It fetches `/api/v1/leads/sources` on mount, renders a source-filter chip row (`All • Reddit • HN • Discord • RSS`), and uses source metadata (icon, color, capabilities) to show per-source scan buttons and per-lead action buttons. Source-specific advanced configuration (e.g., Reddit's subreddit discovery wizard) lives in `config/social_page.dart` as today; the config keys become namespaced (`social.reddit.*`, `social.hn.*`, `social.rss.*`, `social.discord.*`) and the UI renders a section per registered source.

**No Flutter code ships from packs.** Flutter is ahead-of-time compiled; dynamic UI from a third-party pack is not possible without a rebuild. Core Flutter knows the generic rendering contract, packs provide only backend + metadata.

**Pack-catalog + upsell UX.** Core Flutter ships with a **hardcoded pack catalog** (`lib/data/known_packs.dart`) that lists every pack Cognithor knows about — including paid ones the current user has not purchased. The catalog entry for each pack contains: `qualified_id`, `display_name`, `tagline`, `feature_list`, `price_display`, `pack_detail_url` (points at `cognithor.com/packs/<slug>`), `icon`, `accent_color`. The catalog is updated in Core releases; it is not dynamically fetched.

At runtime, the Flutter UI merges the hardcoded catalog with the live `/api/v1/leads/sources` response to produce three states per pack:

1. **Installed + loaded** — pack backend is running. Full config UI is rendered. For Reddit Lead Hunter Pro, this means the existing subreddit/template/auto-post config section in `config/social_page.dart` is shown, wired to live backend state.
2. **Installed but not yet configured** — pack is present but source isn't registered (e.g., missing credentials). Render the config form but mark "Not yet active" and show an "Activate" CTA.
3. **Not installed (upsell)** — pack appears in the catalog but is absent from the sources response. Render a **locked upsell card** instead of the config form. The card shows: pack icon, name, tagline, three feature bullets, price badge, and a prominent "Get Reddit Lead Hunter Pro — from $79" button. The button opens `https://cognithor.com/packs/reddit-lead-hunter` in the system browser via `url_launcher`. Same behavior on the LeadsScreen — locked sources appear as ghost cards with "Install this source" CTAs.

This gives Cognithor a **professional, consistent upsell funnel** directly inside the product (what JetBrains does for Community vs. Ultimate, what 1Password does for personal vs. business tiers) without any dynamic code loading into Flutter. It also avoids the grandfathered-UI compromise: there is no "special case" for Reddit — Reddit is just the first paid pack to use the locked-state pattern, and future packs reuse the same widget.

The hardcoded catalog is a **duplicate source of truth** (the private pack repo's `index.json` is the primary). This is acceptable because (a) the Flutter catalog only needs basic metadata for the upsell card, not the full pack details, (b) Flutter ships infrequently compared to site updates, so stale Flutter catalog entries just mean a user sees an outdated price for ~2-4 weeks until the next Core release, which is fine for an indie product, and (c) the `pack_detail_url` always opens the live site, so the authoritative pricing/features are one click away. A Phase 2 improvement is to cache the catalog from a signed `cognithor.com/api/packs/catalog` endpoint at first run, so prices stay fresh without Core rebuilds.

## 5. Initial Pack Catalog

Four packs are created in MVP. All live in the private `cognithor-packs` repository, all ship their own manifest + EULA + code.

### 5.1 `cognithor-official/reddit-lead-hunter-pro`

**License:** proprietary
**Min Cognithor version:** `>=0.83.0` (the version that ships the pack SDK).
**Checkout:** Lemon Squeezy, one product per tier (Indie / Commercial).

#### Pricing strategy — three-tier price-anchor

The site shows a visibly-struck-through "list price" next to the active launch price, plus a scarcity cap. This is honest price-anchoring: the list price reflects the realistic long-term value given SaaS alternatives cost `$49-499/month`, and the post-launch price is the actual ladder we commit to.

| Tier | List price (struck) | **Launch price** | Post-launch target | Scarcity |
|---|---|---|---|---|
| **Indie** | ~~$149~~ | **$79** | $99 (after first 100 sales) | "First 100 customers" badge |
| **Commercial** | ~~$399~~ | **$199** | $249 (after first 25 sales) | "First 25 teams" badge |
| **Early-bird launch** (optional, first 48h) | ~~$149~~ | **$59** | — | "Product Hunt / Twitter launch only" |

**On the site**, the pack card and detail page render the list price with a strike-through, the launch price in the brand accent color, and a small caption: "Launch pricing · 73 of 100 seats left" (live counter updated at build time from LS Sales API; stale counter is fine for anchoring purposes).

**The scarcity counter is real.** We commit to raising the price once the launch batch sells out — LS has a `variant` feature that can swap the active pricing automatically when the first variant reaches its sales cap. The rising-price-ladder is documented publicly on the roadmap page so buyers trust the cap. Pirates of the first 100 are acceptable social proof.

**Value-comparison framing on the detail page.** The `catalog.mdx` for RLH Pro is updated to explicitly anchor against SaaS alternatives:
- "One-time $79. SaaS alternatives charge $49-499/month. Break-even: 0.16 months for agency use."
- "Lifetime updates included. SaaS alternatives bill updates monthly."
- "Your data stays on your machine. SaaS alternatives ship conversations to their servers."

These framings already exist in the current mdx file (I read it in § 1 context-gathering). The pricing overhaul just leans into them harder.

#### Pack manifest fields

```json
{
  "checkout_url": "https://cognithor.lemonsqueezy.com/buy/<indie-variant-id>",
  "commercial_checkout_url": "https://cognithor.lemonsqueezy.com/buy/<commercial-variant-id>",
  "pricing": {
    "indie": { "list_price": 149, "launch_price": 79, "post_launch_price": 99, "currency": "USD", "launch_cap": 100 },
    "commercial": { "list_price": 399, "launch_price": 199, "post_launch_price": 249, "currency": "USD", "launch_cap": 25 }
  }
}
```

**Contents** (extracted from current `src/cognithor/social/`):
- `src/scanner.py` — `RedditScanner` (public JSON API + LLM scoring)
- `src/reply.py` — `ReplyPoster` with Playwright browser automation
- `src/refiner.py` — `ReplyRefiner` for tone adjustment
- `src/templates.py` — `TemplateManager` with the 50 curated reply templates
- `src/discovery.py` — subreddit auto-discovery
- `src/learner.py` + `src/tracker.py` — style learning from top performers
- `src/reddit_source.py` — the `LeadSource` adapter that wraps all of the above
- `src/tools.py` — MCP tool definitions (migrated from `mcp/reddit_tools.py`)
- `tests/` — full test suite copied over
- `catalog/catalog.mdx` — marketing copy (migrated from `cognithor-site/content/packs/reddit-lead-hunter.mdx`)
- `catalog/og-image.png`
- `pack_manifest.json`
- `eula.md` (from shared template)
- `pack.py` — the `Pack` class

### 5.2 `cognithor-official/hn-lead-hunter`

**License:** apache-2.0
**Price:** free, bundled with Core
**Min Cognithor version:** `>=0.83.0`

Contents: `src/hn_scanner.py` (migrated from `social/hn_scanner.py`), `src/hn_source.py` adapter, tests, catalog, manifest, EULA.

### 5.3 `cognithor-official/discord-lead-hunter`

**License:** apache-2.0
**Price:** free, bundled
**Min Cognithor version:** `>=0.83.0`

Contents: `src/discord_scanner.py` (migrated), `src/discord_source.py` adapter, tests, catalog, manifest, EULA. User still supplies their own `COGNITHOR_DISCORD_TOKEN`.

### 5.4 `cognithor-official/rss-lead-hunter`

**License:** apache-2.0
**Price:** free, bundled
**Min Cognithor version:** `>=0.83.0`

Contents: `src/rss_scanner.py` (migrated — the file I just wrote for #113), `src/rss_source.py` adapter, tests, catalog, manifest, EULA.

### 5.5 Bundled-default pack delivery

The three free packs are bundled with the Core Python package. On first Cognithor startup, `bootstrap_windows.py` (and the Linux equivalent) copies the bundled packs from `<site-packages>/cognithor/_bundled_packs/` to `~/.cognithor/packs/cognithor-official/`. The copy is idempotent and skipped if the target already exists. User-installed overrides (newer versions installed via `cognithor pack install`) win over bundled defaults on version comparison.

This keeps the free Leads Engine experience zero-setup for new users while routing all source code through the same pack interface as paid packs.

## 6. Repository Layout: `cognithor-packs` (private)

```
cognithor-packs/                    # GitHub Alex8791-cyber/cognithor-packs (private)
├── README.md                       # contribution guide, pack layout reference
├── LICENSE                         # proprietary license for the repo as a whole
├── .github/
│   └── workflows/
│       └── build-index-and-deploy.yml
├── _template/                      # copy-paste starter for new packs
│   ├── pack.py
│   ├── pack_manifest.json
│   ├── eula.md                     # shared EULA template
│   ├── catalog/
│   │   └── catalog.mdx
│   └── src/
│       └── __init__.py
├── reddit-lead-hunter-pro/         # paid
│   ├── pack.py
│   ├── pack_manifest.json
│   ├── eula.md
│   ├── src/
│   ├── tests/
│   └── catalog/
│       ├── catalog.mdx
│       └── og-image.png
├── hn-lead-hunter/                 # free, apache-2.0
│   └── ...
├── discord-lead-hunter/            # free, apache-2.0
│   └── ...
├── rss-lead-hunter/                # free, apache-2.0
│   └── ...
└── index.json                      # CI-generated, committed, site-facing
```

**`index.json` shape** (auto-generated, single source of truth for the site fetcher):

```json
{
  "generated_at": "2026-04-15T20:00:00Z",
  "packs": [
    {
      "qualified_id": "cognithor-official/reddit-lead-hunter-pro",
      "namespace": "cognithor-official",
      "pack_id": "reddit-lead-hunter-pro",
      "version": "1.2.0",
      "display_name": "Reddit Lead Hunter Pro",
      "tagline": "Find high-intent leads on Reddit before your competitors.",
      "license": "proprietary",
      "status": "live",
      "tier": "S",
      "checkout_url": "https://cognithor.lemonsqueezy.com/buy/<id>",
      "commercial_checkout_url": "https://cognithor.lemonsqueezy.com/buy/<id-commercial>",
      "pricing": {
        "indie":      { "list_price": 149, "launch_price":  79, "post_launch_price":  99, "currency": "USD", "launch_cap": 100 },
        "commercial": { "list_price": 399, "launch_price": 199, "post_launch_price": 249, "currency": "USD", "launch_cap":  25 }
      },
      "launch_seats_remaining": 100,
      "catalog_path": "reddit-lead-hunter-pro/catalog/catalog.mdx",
      "og_image_path": "reddit-lead-hunter-pro/catalog/og-image.png",
      "last_updated": "2026-04-15T20:00:00Z"
    },
    { "qualified_id": "cognithor-official/hn-lead-hunter", ... },
    ...
  ]
}
```

The site fetcher reads `index.json` for the listing page metadata and fetches each pack's `catalog.mdx` on demand for the detail page. Only `catalog/*` paths are fetched; the source code directories are never touched by the build.

### 6.1 CI action

**`.github/workflows/build-index-and-deploy.yml`:**

```yaml
name: Build pack index and trigger site deploy
on:
  push:
    branches: [main]
    paths:
      - '*/pack_manifest.json'
      - '*/catalog/**'
      - '_template/**'

jobs:
  build-index:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: actions/setup-python@v5
        with: { python-version: '3.13' }
      - name: Regenerate index.json
        run: python scripts/build_index.py
      - name: Commit index.json if changed
        run: |
          git config user.name "cognithor-bot"
          git config user.email "bot@cognithor.dev"
          git add index.json
          git diff --cached --quiet || git commit -m "chore: regenerate index.json"
          git push
      - name: Trigger Vercel deploy hook
        run: |
          curl -fsSL -X POST "${{ secrets.VERCEL_DEPLOY_HOOK_URL }}"
```

`scripts/build_index.py` walks the repo, finds every `<pack>/pack_manifest.json`, reads a minimal set of fields, and writes `index.json`. No external dependencies beyond the stdlib.

**Secrets required:**
- `VERCEL_DEPLOY_HOOK_URL` — Vercel gives this in the project's Git settings; one URL per hook, bearer-less.

No GitHub PAT is needed in this action because it uses the default `GITHUB_TOKEN` for commit + push.

## 7. Site Integration: `cognithor-site` build-time fetcher

**New module: `lib/data/fetch-packs.ts`.**

```ts
import { Octokit } from '@octokit/rest';

const OWNER = 'Alex8791-cyber';
const REPO = 'cognithor-packs';
const BRANCH = 'main';

export interface PackIndexEntry { /* mirrors the JSON shape in § 6 */ }
export interface PackDetail extends PackIndexEntry { catalog_mdx: string; }

export async function fetchPackIndex(): Promise<PackIndexEntry[]> {
  const token = process.env.COGNITHOR_PACKS_READ_TOKEN;
  if (!token) throw new Error('COGNITHOR_PACKS_READ_TOKEN missing at build time');
  const kit = new Octokit({ auth: token });
  const { data } = await kit.repos.getContent({
    owner: OWNER, repo: REPO, path: 'index.json', ref: BRANCH,
  });
  // data is base64-encoded in GH API
  const raw = Buffer.from((data as any).content, 'base64').toString('utf-8');
  const parsed = JSON.parse(raw);
  return parsed.packs;
}

export async function fetchPackDetail(slug: string): Promise<PackDetail> {
  // 1. find entry in index
  // 2. fetch catalog_mdx content via getContent
  // 3. combine
}
```

**Wire-in points on the site:**

- `components/sections/home/PackSpotlightSection.tsx` — featured pack comes from `fetchPackIndex()` at module scope (Next.js RSC) instead of the hardcoded string. The "Install Pack" button's href comes from the fetched `checkout_url` (not from a relative `/packs/...` path, and not from the obsolete Gumroad URL). Fall back to `/packs/<slug>` only if `checkout_url` is null.
- `components/sections/packs/PackStoreGrid.tsx` — replace `import { HOME_PACKS } from '@/lib/data/home-packs'` with `await fetchPackIndex()`. The file `lib/data/home-packs.ts` is deleted.
- `app/[locale]/(marketing)/packs/[slug]/page.tsx` — `generateStaticParams` iterates the fetched index; the page body calls `fetchPackDetail(slug)`.
- `content/packs/reddit-lead-hunter.mdx` — deleted. Single source of truth is now in the packs repo.
- **New route:** `app/[locale]/(marketing)/packs/[slug]/installed/page.tsx` — post-purchase thank-you page. Reads `order_id` and `token` from query params, renders a big "Thanks!" heading, a download button pointing at `https://assets.lemonsqueezy.com/...{token}...`, and a copy-to-clipboard install command block.

**Local development fallback.** If `COGNITHOR_PACKS_READ_TOKEN` is unset (e.g., a new contributor runs `pnpm dev` locally), `fetchPackIndex()` falls back to reading `lib/data/_packs_cache.json` from the site repo. The cache is written by the last successful Vercel build and committed by the build action (a `.git-check` step verifies no changes beyond timestamps).

Alternative for pure local dev without token: a tiny `pnpm run packs:fetch` script that takes a local path to a `cognithor-packs` checkout and generates `_packs_cache.json`. This is the preferred contributor workflow.

**Environment variables (Vercel project settings):**

- `COGNITHOR_PACKS_READ_TOKEN` — GitHub fine-grained PAT, repository access limited to `Alex8791-cyber/cognithor-packs`, permissions `Contents: read`. **Build-time scope only**, not runtime. Vercel allows this via the "Production + Preview" scope selector and NOT marking it as "Available during runtime."

## 8. Commerce Pipeline: Lemon Squeezy

### 8.1 Setup (one-time, manual, not code scope)

1. Create Lemon Squeezy store under `cognithor.lemonsqueezy.com`. LS is the merchant of record — they handle VAT, sales tax, refunds.
2. For each paid pack, create a **Digital Product** with two variants:
   - Indie: $79 (Reddit Lead Hunter Pro)
   - Commercial: $199
3. Upload the pack zip (`reddit-lead-hunter-pro-1.2.0.zip`) to the LS product's "file" field. LS hosts on their CDN.
4. Configure the product's **Thank You URL** to `https://cognithor.com/packs/reddit-lead-hunter/installed?order_id={order_id}&token={download_token}`. LS substitutes the placeholders automatically.
5. Copy the product's checkout URL into `cognithor-packs/reddit-lead-hunter-pro/pack_manifest.json` as `checkout_url`. Commit. CI rebuilds the site.

### 8.2 Post-purchase UX on the site

The new `/packs/[slug]/installed` page:

```tsx
export default function PackInstalledPage({
  searchParams,
}: {
  searchParams: { order_id?: string; token?: string };
}) {
  const { order_id, token } = searchParams;
  if (!order_id || !token) return <InvalidLinkNotice />;

  const zipUrl = `https://assets.lemonsqueezy.com/${token}`;
  const installCmd = `cognithor pack install ${zipUrl}`;

  return (
    <main className="...">
      <h1>Thanks for buying Reddit Lead Hunter Pro</h1>
      <p>Your order: <code>{order_id}</code></p>

      <section>
        <h2>Option 1 — One-line install</h2>
        <CopyableCodeBlock value={installCmd} />
        <p>Paste this into your Cognithor CLI and hit enter. Done.</p>
      </section>

      <section>
        <h2>Option 2 — Download the zip manually</h2>
        <a href={zipUrl} className="...button">Download reddit-lead-hunter-pro.zip</a>
        <p>Then run <code>cognithor pack install ~/Downloads/reddit-lead-hunter-pro.zip</code></p>
      </section>

      <section>
        <h2>Save this email</h2>
        <p>Lemon Squeezy sent you a copy. Keep it for re-downloading the pack later.</p>
      </section>
    </main>
  );
}
```

### 8.3 `cognithor pack install <url>` supports URLs

The installer uses `httpx.stream('GET', url, follow_redirects=True)` to download, writing to a temp file with a tqdm-style progress bar. Content-Length is honored for ETA. Max download size hard limit: **500 MB** (configurable; aborts with clear error above the limit). Timeout: 10 minutes for large files.

If the URL returns HTML instead of a zip (common LS failure when the link is expired or wrong), the installer detects `Content-Type: text/html` and prints: "That URL returned HTML, not a zip. The LS download link may have expired — check your email and re-purchase support if needed."

## 9. Migration Plan: Extracting `src/cognithor/social/` into Packs

The refactor is staged to keep Core buildable and tests green at every intermediate commit. No single PR; expect 4-6 commits spread over 2 sessions.

### Stage 1 — Create `cognithor.leads.sdk` in Core

- New directory `src/cognithor/leads/` with `models.py`, `store.py`, `source.py`, `registry.py`, `service.py`.
- `models.py` is a near-copy of `social/models.py`; `store.py` is a near-copy of `social/store.py`.
- `source.py` and `registry.py` are new (see § 4.5).
- `service.py` is a rewrite: it no longer instantiates a `RedditScanner`; it works through the registry.
- Old `src/cognithor/social/` stays in place for now. `social/service.py` becomes a thin shim that imports from `cognithor.leads.sdk` and registers `RedditSource`, `HNSource`, etc. internally — so existing tests pass without code changes.
- **All tests green after this stage.**

### Stage 2 — Ship the pack interface, loader, installer

- New `src/cognithor/packs/` directory with `interface.py`, `loader.py`, `installer.py`, `cli.py`.
- Wire the loader into the Gateway's Phase-F initialization (after MCP tools are registered).
- Add the bundled-default pack copy step to `bootstrap_windows.py` and the Linux bootstrap script.
- Unit tests for loader, installer, manifest validation.

### Stage 3 — Build the private packs repo

- Create `Alex8791-cyber/cognithor-packs` via the GitHub API (using the PAT from the credential manager).
- Bootstrap repo layout per § 6. Add the CI workflow and `scripts/build_index.py`.
- Add the `_template/` starter with the shared `eula.md`.

### Stage 4 — Extract RLH Pro

- Copy `src/cognithor/social/scanner.py`, `reply.py`, `refiner.py`, `templates.py`, `discovery.py`, `learner.py`, `tracker.py`, plus `mcp/reddit_tools.py`, into `reddit-lead-hunter-pro/src/` in the packs repo.
- Write `reddit-lead-hunter-pro/src/reddit_source.py` (the `LeadSource` adapter).
- Write `reddit-lead-hunter-pro/pack.py`.
- Write `reddit-lead-hunter-pro/pack_manifest.json` (proprietary, price 79, publisher `cognithor-official`).
- Write `reddit-lead-hunter-pro/catalog/catalog.mdx` (migrate from site).
- Hash `eula.md`, update manifest.
- Run the loader locally against a `~/.cognithor/packs/cognithor-official/reddit-lead-hunter-pro/` symlink; verify all previously-working flows (scan, store, reply draft) still work via the pack path.
- **Delete** `src/cognithor/social/scanner.py`, `reply.py`, `refiner.py`, `templates.py`, `discovery.py`, `learner.py`, `tracker.py`, `mcp/reddit_tools.py` from Core. The shim `social/service.py` is also deleted (replaced by direct use of `cognithor.leads.sdk`).
- Delete `flutter_app/lib/screens/reddit_leads_screen.dart`. Rename to `leads_screen.dart`; rewrite as the generic source-agnostic version per § 4.5.

### Stage 5 — Extract HN, Discord, RSS as bundled free packs

- For each, copy the scanner file into `<pack>/src/<source>_scanner.py`, write a `<source>_source.py` adapter, write `pack.py`, manifest (apache-2.0), catalog mdx, EULA.
- Add to Core's `_bundled_packs/` directory.
- Delete `src/cognithor/social/hn_scanner.py`, `discord_scanner.py`, `rss_scanner.py`.
- The `src/cognithor/social/` directory should now be completely empty and can be deleted.

### Stage 6 — Site migration

- Install `@octokit/rest` in `cognithor-site`.
- Write `lib/data/fetch-packs.ts`.
- Rewire `PackStoreGrid`, `PackSpotlightSection`, `/packs/[slug]/page.tsx` to use the fetcher.
- Add the `/packs/[slug]/installed` route.
- Delete `content/packs/reddit-lead-hunter.mdx`.
- Delete `lib/data/home-packs.ts`.
- Update tests accordingly.
- Add `COGNITHOR_PACKS_READ_TOKEN` to Vercel project settings.

### Stage 7 — Git hygiene commands (printed, not executed)

At the end of the implementation, the plan prints (NOT runs) a summary for the user:

```bash
# In D:\Jarvis\jarvis complete v20
git status
git add -A
git commit -m "refactor(leads): extract Reddit Lead Hunter Pro into agent pack

Extracts all Reddit-specific code into the private cognithor-packs repo
as a paid pack. Introduces cognithor.packs plugin infrastructure and
cognithor.leads.sdk for generic multi-source lead handling. HN, Discord,
and RSS move to bundled free packs delivered via the same interface.

Closes #113 fully, prepares for the Q4 2026 community creator marketplace."
git push origin main

# The proprietary pack code is not in git history — it was only ever a
# copy from src/cognithor/social/, which stays in history as Apache 2.0
# (that's fine; users who checked out older commits see the old layout).
# No history rewrite is required. Force-push is NOT needed.
```

## 10. Test Strategy

**Unit tests (new):**

- `tests/test_packs/test_interface.py` — `PackManifest` validation, schema version check, required fields
- `tests/test_packs/test_loader.py` — discovery, EULA hash mismatch, version-range mismatch, broken entrypoint, missing `.eula_accepted`, unregister cleanup
- `tests/test_packs/test_installer.py` — local zip install, URL install (mocked `httpx`), SHA-256 verification, EULA click-through (monkeypatch `input`), upgrade flow, downgrade warning
- `tests/test_leads_sdk/test_source.py` — abstract base, capability checks
- `tests/test_leads_sdk/test_registry.py` — register/unregister/list
- `tests/test_leads_sdk/test_service.py` — source-agnostic `scan()` with a fake source

**Integration tests:**

- `tests/test_leads_sdk/test_e2e_bundled_packs.py` — spins up a temp `~/.cognithor/packs/` with bundled HN/Discord/RSS packs, loads them, verifies each `LeadSource` is registered and at least the `scan()` signature works

**Existing tests to migrate:**

- Everything under `tests/test_social/` moves to `tests/test_packs/test_reddit_lead_hunter_pro/` **inside the pack repo**, and `tests/test_leads_sdk/`. The Core test suite shrinks; the pack repo grows its own `tests/` directory that runs independently.
- **Test count impact in Core:** ~150 tests move out (Reddit-specific ones) and ~40 new tests move in (SDK + pack infrastructure). Net Core test count drops by ~110.

**What must NOT break:**

- `tests/test_core/test_config.py` (after the SocialConfig adjustments)
- `tests/test_install_language_marker.py`
- `tests/test_skill_tools_coverage.py` (Reddit MCP tools are gone → the expected tool count changes; update the assertion)
- Flutter golden tests for `LeadsScreen` — regenerate after the rename

**CI:**

- Core repo CI: runs unchanged, should report the full suite green after Stage 6.
- Pack repo CI: new. Runs per-pack tests, validates manifests, builds `index.json`, triggers site redeploy.
- Site repo CI: Next.js build with `COGNITHOR_PACKS_READ_TOKEN` set; verifies fetcher doesn't 404 on `index.json`.

## 11. Out-of-Scope — Roadmap Anchor

These items are explicitly **not** in MVP. They are listed here so the implementation plan does not accidentally scope-creep and so the Q3/Q4 roadmap has a written anchor.

### Phase 2 — Commerce maturity (estimated Q2-Q3 2026)

- **License key validation.** `cognithor pack update` talks to a Cognithor-owned Vercel Edge Function that validates a key against LS License API and returns a fresh signed download URL. Machine binding via `hostname`.
- **Hot reload.** Pack changes apply without restarting Cognithor.
- **Refund-driven revocation.** LS webhook → our endpoint → mark key inactive → CLI update check fails.
- **Pack signing.** Ed25519 signatures on `pack_manifest.json`. Core hardcodes a root public key. Installer refuses unsigned packs.
- **Differential downloads.** `cognithor pack update` only downloads changed files instead of the full zip.
- **Launch discount + price ratchet automation.** `$59` for first 50, auto-bump to `$99` after 100 sales.

### Phase 3 — Community creator marketplace (Q4 2026, already promised on the site)

- **Creator self-service portal.** Pack upload UI, preview, approval queue on a new site route.
- **Multi-publisher aggregation.** Site fetcher walks a list of registered source repos instead of one. Each community creator has their own private repo we have read access to.
- **Automated payouts.** Stripe Connect or Wise integration. 70/30 split per `revenue_share` field.
- **Creator dashboards.** Sales, refunds, review metrics.
- **Automated pack security scan.** Static analysis of pack source before approval (import graph, known bad patterns, syscall/subprocess usage).
- **Rating/review system.** 1-5 stars + written reviews on `/packs/[slug]`.
- **Per-creator EULA review.** Community creators submit custom EULAs; we review before certification.
- **Rev-share accounting.** 1099-NEC (US creators), VAT MOSS (EU creators), payout statements.
- **Dispute resolution.** Refund routing to creator; arbitration channel.

### Phase 4 — Pack depth and sandboxing (TBD)

- **Pack sandboxing.** Move from importlib (shared process) to a subprocess-per-pack model with MCP-over-stdio, so pack crashes cannot kill Core and pack permissions can be enforced at the OS level.
- **HN Pro, Discord Pro, Twitter/X Lead Hunter Pro, LinkedIn Lead Hunter Pro** — future Pro variants of free bundled packs, each with their own paid features (HN Pro: auto-comment drafter + trend analysis; Discord Pro: DM automation + server discovery; Twitter Pro: TweetDeck-style listening).
- **EULA localization.** Multi-language EULAs per pack.
- **Pack-to-pack dependencies.** A pack can require another pack to be installed.

### Excluded forever (principle)

- **DRM beyond signing.** We do not run obfuscators, license dongles, anti-debug, or phone-home beacons. These erode the local-first brand and punish paying customers without stopping determined pirates.
- **Cloud-based pack execution.** All packs run on user machines. The value prop is local-first.
- **Telemetry.** No installation telemetry, no usage telemetry, no error phone-home. (Bug reports are explicit, user-initiated.)

## 12. Acceptance Criteria

The MVP is complete when ALL of the following are true:

- [ ] `cognithor.packs.interface`, `cognithor.packs.loader`, `cognithor.packs.installer` exist and have unit tests
- [ ] `cognithor.leads.sdk` exists with `LeadSource`, `SourceRegistry`, `LeadService`, `LeadStore`, models
- [ ] Reddit-specific code is absent from `src/cognithor/` (verified by `grep -r reddit src/cognithor/` returning only comments/docs)
- [ ] `src/cognithor/social/` directory no longer exists
- [ ] The four packs (`reddit-lead-hunter-pro`, `hn-lead-hunter`, `discord-lead-hunter`, `rss-lead-hunter`) exist in `Alex8791-cyber/cognithor-packs`
- [ ] `cognithor-packs` CI generates `index.json` on push and calls the Vercel deploy hook
- [ ] `cognithor pack install <url>` installs RLH Pro into `~/.cognithor/packs/cognithor-official/reddit-lead-hunter-pro/` with EULA click-through
- [ ] `cognithor-site` fetches the pack catalog at build time; `HOME_PACKS` and `/packs/[slug]` routes come from the private repo's `index.json`
- [ ] `/packs/[slug]/installed` thank-you page exists and renders the one-line install command
- [ ] Existing Core test suite is green (with updated assertions for the smaller tool count)
- [ ] Bundled HN/Discord/RSS packs are auto-copied on first Cognithor start; a new user without purchases still sees a working Leads tab
- [ ] Flutter `LeadsScreen` (renamed from `RedditLeadsScreen`) renders source metadata from `/api/v1/leads/sources` and gates the sidebar on an empty source list
- [ ] Flutter ships `lib/data/known_packs.dart` with the hardcoded pack catalog. `config/social_page.dart` and `LeadsScreen` render upsell cards for packs in the catalog that are not installed, opening `cognithor.com/packs/<slug>` via `url_launcher` on tap
- [ ] Site pack cards and detail page render struck-through list price + launch price + "seats remaining" scarcity badge, fed from `index.json` `pricing` field
- [ ] Pack manifest validates the `pricing` map shape for paid packs (at least `indie` tier required, `commercial` optional); free packs may omit the field entirely
- [ ] No new runtime secrets are required on the site (build-time token only)
- [ ] Git-cleanup commands are printed to the user at the end of the implementation run (not executed)

## 13. Open Questions — Deferred to Implementation

These are specific enough to answer during implementation without blocking the design:

- Which Python version minimum? (Current Core is 3.13; packs will match.)
- Does the installer need colors in terminal output for the EULA display? (Nice to have, use `rich` if already a dep.)
- Pack directory ownership on Windows — the installer runs as user, so no elevation needed, but symlink support is uneven pre-Win11.
- Locale for EULA display — MVP is English only.
- Exact shape of the `catalog.mdx` frontmatter vs. free-form body — will mirror the current `content/packs/reddit-lead-hunter.mdx` file for one-to-one migration.
- Should packs declare their Flutter config-form schemas in the manifest (e.g., JSON Schema with UI hints)? For MVP, no: first-party packs use grandfathered UI in `config/social_page.dart`, third-party packs get text-field defaults. For Phase 2, yes: a lightweight schema language (probably Rjsf-subset) powers pack-agnostic config UIs.

---

## Sign-off

This spec is ready for user review. After user approval, the implementation proceeds via the `superpowers:writing-plans` skill to produce a step-by-step plan with explicit checkpoints.
