# Cognithor Retrieval Extensions – Implementation Prompt

## Mission

Erweitere das Cognithor Memory- und Retrieval-System um **zwei neue Subsysteme**, ohne die bestehende 6-Tier-Memory-Architektur, das 3-Kanal-Hybrid-Search-System oder die ~13.000 bestehenden Tests zu brechen. Beide Features müssen sich nahtlos in die existierende `MemoryManager`-API einfügen, GDPR-konform und vollständig lokal lauffähig sein.

Die zwei Subsysteme sind:

1. **CAG Layer** – KV-Cache-Preloading für Core Memory und weitere stabile Wissensdomänen
2. **Hierarchical Document Reasoning** – ein vektorloses, baumbasiertes Retrieval für lange strukturierte Dokumente (PageIndex-Pattern)

---

## Bestehender Kontext – ABSOLUT zu respektieren

Bevor du eine Zeile Code schreibst, lies und verstehe folgende Module:

- `src/jarvis/memory/manager.py` – zentrale Memory-API, Einstiegspunkt
- `src/jarvis/memory/search.py` – 3-Kanal-Hybrid-Search mit Score-Fusion
- `src/jarvis/memory/indexer.py` – SQLite/FTS5-Persistenz
- `src/jarvis/memory/vector_index.py` – Vector-Embeddings-Layer
- `src/jarvis/memory/embeddings.py` – Embedding-Client (Ollama)
- `src/jarvis/memory/chunker.py` – aktuelles Chunking
- `src/jarvis/memory/enhanced_retrieval.py` – Retrieval-Pipeline
- Alle Module der 6 Memory-Tiers: Core, Episodic, Semantic, Procedural, Working, **Tactical**

Du arbeitest in einem System mit:

- **6-Tier Cognitive Memory**: Core, Episodic, Semantic, Procedural, Working, Tactical
- **3-Kanal Hybrid Search**: BM25/FTS5, Vector (Cosine), Graph-Traversierung
- **Storage**: SQLite + Markdown mit YAML-Frontmatter, keine externen Server
- **Local-first, GDPR**: keine Cloud-Calls, keine Telemetrie, kein externer State
- **Python (modernes Python)**, type-hinted, async-aware
- **Test-Suite**: ~13.000 Tests, ~89% Coverage – muss nach jedem Push grün bleiben
- **Pre-Push-Workflow**: lokales Test-Skript läuft vor jedem Push

**Nicht erlaubt**: Externe Datenbanken (Redis, Elasticsearch, Postgres). Cloud-only-Dependencies. Network-Calls außerhalb existierender LLM-Provider-Abstraktionen. Breaking Changes an `MemoryManager`-Public-API.

---

# FEATURE 1: CAG Layer – KV-Cache Preloading

## Ziel

Eliminiere Retrieval-Latenz und Embedding-Drift für **stabile, hochwertige Wissensdomänen**, indem die Aufmerksamkeits-Berechnungen über diese Wissensblöcke einmalig vom Backend-LLM berechnet und als KV-Cache persistent gespeichert werden. Bei jeder neuen Anfrage wird der Cache geladen statt das Wissen neu zu prozessieren.

## Scope

**In Scope:**
- Cache-Erstellung, Persistenz, Laden, Invalidierung
- Backend-Adapter für lokale Inferenz-Engines: `llama.cpp`, `vLLM`, `Ollama` (sofern unterstützt)
- Integration mit Core Memory (immer gecached) und optional mit Semantic Memory für markierte Wissensbereiche
- Fallback auf Standard-Inferenz, wenn Backend kein KV-Cache-Preloading unterstützt
- Telemetrie nur lokal: Cache-Hit-Rate, Lade-Latenz, Cache-Größe

**Out of Scope:**
- Cloud-Provider (Anthropic, OpenAI, Google) – diese unterstützen kein User-seitiges KV-Caching
- Distributed Caching über mehrere Maschinen
- Inkrementelles Cache-Update (Cache wird bei Änderung komplett neu berechnet)

## Architektur

Erstelle ein neues Submodul: `src/jarvis/memory/cag/`

Mit folgender Struktur:

```
cag/
├── __init__.py
├── manager.py           # CAGManager – orchestriert Cache-Lifecycle
├── cache_store.py       # CacheStore – Persistenz auf Disk
├── builders/
│   ├── __init__.py
│   ├── base.py          # CacheBuilder ABC
│   ├── llamacpp.py      # llama.cpp KV-Cache via state save/load
│   ├── vllm.py          # vLLM Prefix-Caching API
│   └── ollama.py        # Ollama context reuse (best-effort)
├── invalidation.py      # ContentHasher, InvalidationPolicy
├── selectors.py         # CAGSelector – entscheidet, was gecached wird
└── metrics.py           # lokale Cache-Metriken
```

## Klassen und Interfaces

### `CAGManager` (manager.py)

```python
class CAGManager:
    """Orchestriert KV-Cache-Lifecycle für Cognithor Memory."""
    
    def __init__(
        self,
        backend: str,                    # "llamacpp" | "vllm" | "ollama"
        cache_dir: Path,                 # ~/.cognithor/cag_cache/
        max_cache_size_bytes: int,       # Default: 8 GB
        memory_manager: "MemoryManager",
    ) -> None: ...
    
    async def build_cache(
        self,
        cache_id: str,                   # z.B. "core_memory", "tariff_book_2026"
        content: str,                    # vollständiger Text
        model_id: str,                   # exakter Modell-Identifier
        metadata: dict[str, Any] | None = None,
    ) -> CacheHandle: ...
    
    async def load_cache(
        self,
        cache_id: str,
        model_id: str,
    ) -> CacheHandle | None: ...
    
    async def invalidate(self, cache_id: str) -> None: ...
    
    async def list_caches(self) -> list[CacheMetadata]: ...
    
    async def get_metrics(self) -> CAGMetrics: ...
```

### `CacheBuilder` ABC (builders/base.py)

```python
class CacheBuilder(ABC):
    """Backend-spezifischer KV-Cache-Builder."""
    
    @abstractmethod
    async def is_supported(self, model_id: str) -> bool: ...
    
    @abstractmethod
    async def build(
        self,
        content: str,
        model_id: str,
        target_path: Path,
    ) -> CacheArtifact: ...
    
    @abstractmethod
    async def load(
        self,
        artifact: CacheArtifact,
        model_id: str,
    ) -> LoadedCache: ...
    
    @abstractmethod
    async def estimate_size(self, content: str, model_id: str) -> int: ...
```

### `CacheStore` (cache_store.py)

- Persistiert Caches als Binär-Files unter `cache_dir/<model_hash>/<cache_id>.bin`
- Sidecar-File `<cache_id>.meta.json` mit:
  - `cache_id`
  - `model_id`
  - `model_hash` (sha256 des Modell-Identifiers)
  - `content_hash` (sha256 des Inhalts)
  - `created_at` (ISO 8601 UTC)
  - `size_bytes`
  - `token_count`
  - `backend`
  - `backend_version_hash` (für Kompatibilitäts-Checks)
- LRU-Eviction wenn `max_cache_size_bytes` überschritten wird
- Atomare Writes via temp-file + rename

### `ContentHasher` (invalidation.py)

- Berechnet `content_hash` über normalisierten Text (whitespace-collapsed, BOM-stripped)
- `should_invalidate(stored_meta, current_content) -> bool`
- Invalidierungs-Trigger:
  - Content-Hash hat sich geändert
  - Model-ID hat sich geändert
  - Backend-Version-Hash hat sich geändert
  - TTL überschritten (optional, default: nie)

### `CAGSelector` (selectors.py)

Entscheidet automatisch, welche Memory-Inhalte für Caching qualifiziert sind:

- **Immer gecached**: Core Memory (alle Inhalte)
- **Auf Anforderung gecached**: Semantic Memory Items mit `cag: true` im YAML-Frontmatter
- **Niemals gecached**: Working Memory, Episodic Memory, Tactical Memory (zu volatil)
- **Konditional**: Procedural Memory mit `times_used >= 10` und `confidence >= 0.9`

Selektor liefert eine Liste `CacheCandidate(cache_id, content, priority, estimated_tokens)`.

## Backend-Adapter – Implementierungs-Details

### `LlamaCppCacheBuilder`

- Nutzt llama.cpp's `state_save_file` / `state_load_file` API
- Erstellt einen Inferenz-Kontext, prozessiert den vollen Content (kein Output-Generation), speichert den State
- Beim Laden: neuer Inferenz-Kontext, `state_load_file`, dann ist das Modell "primed" mit dem Wissen
- Falls `llama-cpp-python` nicht installiert: `is_supported` returnt `False`, kein Crash
- Token-Count via Tokenizer des geladenen Modells
- Speicher-Limit-Check: Wenn `estimate_size` > verfügbarer Disk-Space, raise `CAGCapacityError`

### `VLLMCacheBuilder`

- Nutzt vLLM's Prefix-Caching-API (Automatic Prefix Caching, APC)
- Registriert den Content als "prefix" mit stabiler Hash-ID
- Beim Inferenz-Call wird der Prefix automatisch wiederverwendet
- Cache-Persistenz über vLLM's Disk-Cache-Funktionalität (sofern aktiviert)
- Falls vLLM nicht erreichbar: `is_supported` returnt `False`

### `OllamaCacheBuilder`

- Ollama unterstützt aktuell nur Context-Reuse innerhalb einer Session, kein persistentes KV-Caching
- Implementiere "Context-Pinning": Halte einen Long-running Ollama-Request offen mit dem Core Memory als initialen Prompt
- Bei jeder neuen Anfrage wird die Anfrage an diesen pre-warmed Context angehängt
- Wenn Ollama-Session verloren geht: automatischer Rebuild
- Markiere diesen Builder klar als "soft caching" mit reduziertem Performance-Gewinn gegenüber echtem KV-Cache

## Integration mit MemoryManager

Erweitere `MemoryManager` um folgende Methoden, **ohne bestehende Signaturen zu ändern**:

```python
async def enable_cag(self, backend: str | None = None) -> None: ...

async def refresh_cag_cache(self, cache_id: str | None = None) -> CAGRefreshReport:
    """Wenn cache_id None: alle qualifizierten Caches refreshen."""

async def get_cag_status(self) -> CAGStatus: ...
```

Beim `MemoryManager.__init__()`:
- Wenn `cag_enabled` in der Config `True`: instantiiere `CAGManager`, registriere Hooks
- Hook auf Core-Memory-Änderungen: triggert automatisches Cache-Rebuild im Hintergrund (asyncio task, non-blocking)
- Hook auf Semantic-Memory-Änderungen: prüft `cag` Frontmatter, triggert ggf. Rebuild

## Inferenz-Pfad

Erweitere die Inferenz-Aufruf-Schicht so, dass:

1. Vor jedem LLM-Call wird `CAGManager.load_cache(...)` für relevante Caches versucht
2. Wenn Cache gefunden → LLM wird mit pre-loaded KV-State gestartet, Prompt enthält **nur die User-Anfrage und Working Memory**
3. Wenn kein Cache → klassischer Pfad, Core Memory wird in den Prompt eingefügt
4. Cache-Hit/Miss wird in `CAGMetrics` geloggt

## Konfiguration

Erweitere die Cognithor-Konfigurationsdatei (`config.toml` oder äquivalent) um:

```toml
[memory.cag]
enabled = false                          # default off, opt-in
backend = "auto"                         # "auto" | "llamacpp" | "vllm" | "ollama"
cache_dir = "~/.cognithor/cag_cache"
max_cache_size_bytes = 8589934592        # 8 GB
auto_rebuild_on_change = true
rebuild_debounce_seconds = 30
fallback_to_standard_inference = true
```

## Edge Cases – ALLE müssen abgedeckt sein

1. **Backend nicht installiert** → `is_supported() == False`, MemoryManager fällt auf Standard zurück, log warning, kein Crash
2. **Modell-Wechsel zur Laufzeit** → alle Caches mit altem `model_id` werden als invalid markiert, NICHT gelöscht (anderer Use-Case könnte sie noch brauchen)
3. **Disk voll** → LRU-Eviction, dann `CAGCapacityError` wenn immer noch nicht genug Platz
4. **Korrupter Cache-File** → Hash-Mismatch beim Laden, automatisches Rebuild, log warning
5. **Concurrent Cache-Build für selben `cache_id`** → File-Lock via `fcntl` (Unix) / msvcrt (Windows), zweiter Caller wartet
6. **Cache älter als Modell-Update** → Backend-Version-Hash-Check, automatisches Rebuild
7. **Content leer oder unter 50 Tokens** → kein Cache erstellt (nicht lohnenswert), log info
8. **Async-Cancellation während Build** → temp-file wird gelöscht, kein partieller Cache
9. **Cache-File von anderer Cognithor-Version** → Schema-Version im Meta-File, bei Mismatch Rebuild

## Tests

Erstelle Tests unter `tests/memory/cag/`:

- `test_cache_store.py` – Persistenz, LRU-Eviction, atomare Writes, korrupte Files
- `test_invalidation.py` – Hash-Berechnung, Invalidierungs-Trigger
- `test_selectors.py` – Selektion-Logik für alle 6 Memory-Tiers
- `test_manager_lifecycle.py` – Build/Load/Invalidate/Refresh
- `test_llamacpp_builder.py` – mit gemocktem llama.cpp (nutze pytest fixtures)
- `test_vllm_builder.py` – mit gemocktem vLLM
- `test_ollama_builder.py` – mit gemocktem Ollama
- `test_concurrent_builds.py` – File-Locking, Race-Conditions
- `test_integration_with_memory_manager.py` – End-to-End mit dem echten MemoryManager
- `test_edge_cases.py` – alle 9 Edge Cases oben

Jeder Test muss deterministisch sein, keine echten LLM-Calls, keine echten Disk-Caches außerhalb von `tmp_path`.

---

# FEATURE 2: Hierarchical Document Reasoning

## Ziel

Ergänze das 3-Kanal-Hybrid-Search-System um einen **vierten Retrieval-Kanal**, der lange strukturierte Dokumente (Verträge, AVB, BU-Bedingungswerke, technische Manuals, Geschäftsberichte) als **hierarchischen Baum** repräsentiert und ein LLM die relevanten Knoten direkt durch semantisches Reasoning auswählen lässt – **ohne Vektor-Embeddings**.

## Scope

**In Scope:**
- Tree-Builder, der Dokumente anhand von Headings, Sections, Paragraphs in eine Baumstruktur transformiert
- Persistenz der Baumstruktur in SQLite (gleiche DB wie bestehende Indexer)
- LLM-basiertes Node-Selection mit konfigurierbarem Provider
- Integration als 4. Kanal in `search.py` mit Score-Fusion
- Markdown, PDF (über bestehende PDF-Reader), DOCX, HTML, plain text
- Deutsche und englische Dokumente

**Out of Scope:**
- Bild-Extraktion aus Dokumenten (kommt später)
- Tabellen-Reasoning (Phase 2)
- Mehrsprachige Übersetzung
- Real-time Document-Editing

## Architektur

Erstelle ein neues Submodul: `src/jarvis/memory/hierarchical/`

```
hierarchical/
├── __init__.py
├── manager.py             # HierarchicalIndexManager
├── tree_builder.py        # DocumentTreeBuilder
├── parsers/
│   ├── __init__.py
│   ├── base.py            # DocumentParser ABC
│   ├── markdown.py        # MarkdownParser
│   ├── pdf.py             # PDFParser (nutzt bestehende PDF-Reader)
│   ├── docx.py            # DocxParser
│   ├── html.py            # HtmlParser
│   └── plaintext.py       # PlainTextParser (heuristisch)
├── tree_store.py          # TreeStore – SQLite-Persistenz
├── node_selector.py       # LLMNodeSelector
├── retrieval.py           # HierarchicalRetriever – als 4. Kanal nutzbar
├── models.py              # DocumentTree, TreeNode, NodeMetadata
└── prompts.py             # System-Prompts für LLM-Selection
```

## Datenmodell

### `TreeNode` (models.py)

```python
@dataclass(frozen=True)
class TreeNode:
    node_id: str                     # UUID
    document_id: str                 # parent document
    parent_id: str | None            # None = root
    level: int                       # 0 = root, 1 = h1, 2 = h2, ...
    title: str                       # heading text
    summary: str                     # 1-2 sentence LLM-generated summary
    content: str                     # full text of this section (without children)
    content_hash: str                # sha256
    token_count: int
    children_ids: tuple[str, ...]
    position: int                    # original order within parent
    page_number: int | None          # for PDF
    metadata: Mapping[str, Any]
```

### `DocumentTree`

```python
@dataclass(frozen=True)
class DocumentTree:
    document_id: str
    source_path: Path
    source_hash: str
    title: str
    root_node_id: str
    nodes: Mapping[str, TreeNode]    # node_id -> TreeNode
    created_at: datetime
    parser_used: str
    total_tokens: int
```

## Tree Builder – Algorithmus

### `DocumentTreeBuilder` (tree_builder.py)

**Schritte (in genau dieser Reihenfolge):**

1. **Parser-Auswahl** anhand der Dateiendung und Magic Bytes
2. **Strukturelle Extraktion**: Parser liefert eine flache Liste von `RawSection(level, title, content, position, page)`
3. **Hierarchie-Aufbau**: Iteriere flache Liste, baue Baum anhand von Level (h1 > h2 > h3 ...). Wenn ein h2 ohne vorhergehendes h1 auftaucht: virtuelles h1 mit Titel "Untitled Section" einfügen
4. **Content-Splitting bei Übergröße**: Wenn ein Knoten mehr als 4000 Tokens enthält, splitte anhand von Paragraphen in Sub-Knoten mit Level n+1 und Titel "Part 1", "Part 2", ...
5. **Summary-Generation**: Für jeden Knoten ein LLM-Call (lokal, batched), der eine 1-2-Satz-Zusammenfassung erstellt. Bottom-up: Leaf-Nodes zuerst, dann Parent-Nodes mit Children-Summaries als Input
6. **Token-Counting** via Tokenizer
7. **Persistierung** via `TreeStore`

**Wichtig:**
- Bottom-up-Summary-Generation, damit Parent-Summaries die Children-Summaries kennen
- Maximaler Branching-Factor: 50 Children pro Node. Wenn überschritten: Gruppen-Knoten "Part 1", "Part 2" einfügen
- Maximale Tiefe: 8 Level. Tiefer ⇒ flatten in Content
- Alle LLM-Calls async und batched (max 10 parallel)

### Parser-Heuristiken

**MarkdownParser**: ATX-Headings (`#`, `##`, ...) und Setext-Headings. Code-Blocks werden als atomare Inhalte behandelt (nie gesplittet).

**PDFParser**: Nutzt bestehenden PDF-Reader. Heading-Detection via Font-Size-Heuristik (top 20% der Font-Größen = Heading-Kandidaten). Falls PDF strukturiertes TOC hat: TOC bevorzugen.

**DocxParser**: Word-Heading-Styles (Heading 1, Heading 2, ...) sind die Wahrheit. Fallback: Bold + Größere Font.

**HtmlParser**: `<h1>`...`<h6>` Tags. Ignoriere Navigation, Footer, `<aside>` (heuristisch via Klassen-Namen und semantischen Tags).

**PlainTextParser**: Heuristik anhand von Leerzeilen, ALL-CAPS-Zeilen, Nummerierungs-Mustern (`1.`, `1.1`, `§ 1`, `Art. 1`). Speziell für deutsche Rechts- und Versicherungsdokumente: `§`, `Abs.`, `Satz`, `Art.` als Strukturmarker.

## Tree Store

`TreeStore` (tree_store.py) persistiert in derselben SQLite-DB wie bestehender Indexer, in neuen Tabellen:

```sql
CREATE TABLE IF NOT EXISTS hierarchical_documents (
    document_id TEXT PRIMARY KEY,
    source_path TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    title TEXT NOT NULL,
    root_node_id TEXT NOT NULL,
    parser_used TEXT NOT NULL,
    total_tokens INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS hierarchical_nodes (
    node_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    parent_id TEXT,
    level INTEGER NOT NULL,
    position INTEGER NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    page_number INTEGER,
    metadata_json TEXT,
    FOREIGN KEY (document_id) REFERENCES hierarchical_documents(document_id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES hierarchical_nodes(node_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_nodes_document ON hierarchical_nodes(document_id);
CREATE INDEX IF NOT EXISTS idx_nodes_parent ON hierarchical_nodes(parent_id);
```

Alle Schreiboperationen in einer Transaktion. Bei Fehler: Rollback, kein partieller Baum.

## LLM Node Selector

### `LLMNodeSelector` (node_selector.py)

```python
class LLMNodeSelector:
    async def select_nodes(
        self,
        query: str,
        tree: DocumentTree,
        max_nodes: int = 5,
        max_tokens_per_node: int = 2000,
    ) -> list[SelectedNode]: ...
```

**Algorithmus (Top-Down Tree Traversal):**

1. Start am Root-Knoten
2. Erstelle einen Prompt mit:
   - Der User-Query
   - Title + Summary aller direkten Children des aktuellen Knotens (NICHT der gesamte Baum)
   - Anweisung: Wähle bis zu 3 Children, die am wahrscheinlichsten die Antwort enthalten. Antworte als JSON-Array mit Node-IDs.
3. LLM antwortet → parse JSON → für jedes ausgewählte Child rekursiver Schritt 2
4. Wenn ein Knoten ein Leaf ist (keine Children) ODER vom LLM als "answer-bearing" markiert wurde: in `selected_nodes` aufnehmen
5. Stop, wenn `max_nodes` erreicht oder kein weiteres LLM-erlaubtes Children-Selection mehr möglich
6. Nach Selection: jeder ausgewählte Knoten wird auf `max_tokens_per_node` getrimmt (Mitte gekürzt, Anfang+Ende behalten)

**Prompt** (in prompts.py, deutsche und englische Variante):

```
Du bist ein Dokument-Navigator. Eine User-Frage ist gegeben, plus eine Liste von 
Abschnitten eines Dokuments mit jeweils Titel und Kurzbeschreibung. Deine Aufgabe:
Wähle bis zu 3 Abschnitte aus, die die Antwort am wahrscheinlichsten enthalten.

Antworte AUSSCHLIESSLICH mit JSON in diesem Format:
{"selected_node_ids": ["id1", "id2"], "reasoning": "kurze Begründung"}

Wenn KEIN Abschnitt relevant ist, antworte mit leerem Array.
```

**Robustheit:**
- JSON-Parsing mit Fallback auf Regex-Extraktion
- Bei drei aufeinanderfolgenden Parse-Fehlern: Cancel und return leere Liste
- Timeout pro LLM-Call: 30 Sekunden
- Alle LLM-Calls über die existierende LLM-Provider-Abstraktion (kein direkter Call)

## Integration als 4. Retrieval-Kanal

Erweitere `search.py` so:

1. Neue Methode `_hierarchical_channel(query) -> list[ScoredResult]` im Hybrid-Search-System
2. Score-Fusion: hierarchische Ergebnisse erhalten einen konfigurierbaren Default-Gewicht von `0.25` (BM25, Vector, Graph behalten ihre Gewichte, alle werden re-normalisiert)
3. Konfigurierbar pro Query, ob hierarchischer Kanal aktiv ist (default: nur wenn mindestens ein hierarchisches Dokument im Index ist)
4. Score eines hierarchischen Treffers = `1.0 / (1 + tree_depth)` * `llm_confidence`, wobei `llm_confidence` aus der Reasoning-Begründung extrahiert wird (heuristisch, default 0.8)

Bestehende `SearchResult`-Struktur darf NICHT geändert werden. Stattdessen: hierarchische Ergebnisse werden in das gleiche Format gemappt mit `source_type = "hierarchical"`.

## Integration mit MemoryManager

Erweitere `MemoryManager`:

```python
async def index_document_hierarchical(
    self,
    source_path: Path,
    document_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> DocumentTree: ...

async def remove_hierarchical_document(self, document_id: str) -> None: ...

async def list_hierarchical_documents(self) -> list[DocumentMetadata]: ...

async def reindex_hierarchical_document(self, document_id: str) -> DocumentTree: ...
```

Bestehende `index_document(...)` bleibt unverändert. User entscheidet explizit, ob hierarchisch oder klassisch.

## Konfiguration

```toml
[memory.hierarchical]
enabled = true
default_max_nodes_per_query = 5
default_max_tokens_per_node = 2000
summary_llm_provider = "ollama"          # nutzt vorhandene Provider-Konfiguration
summary_llm_model = "default"            # kein hardcoded Modellname
score_weight = 0.25
max_branching_factor = 50
max_tree_depth = 8
node_split_token_threshold = 4000
parallel_summary_generation = 10
```

## Edge Cases – ALLE müssen abgedeckt sein

1. **Dokument ohne Headings** → PlainTextParser nutzt Heuristiken; wenn auch das fehlschlägt: ein einziger Root-Knoten mit komplettem Inhalt
2. **Verschachtelte Heading-Sprünge** (h1 → h3 ohne h2) → virtuelle h2 einfügen
3. **Sehr großes Dokument** (>500.000 Tokens) → Indexierung in Chunks, Progress-Callback, kein OOM
4. **Beschädigte PDF/DOCX** → Parser gibt klaren Fehler, kein partieller Baum
5. **Duplicate document_id** → Re-Index mit neuem Source-Hash, alter Baum wird per CASCADE gelöscht
6. **LLM nicht erreichbar während Tree-Build** → Retry mit exponential backoff (3 Versuche), dann `HierarchicalIndexError`
7. **Concurrent index_document_hierarchical für gleiches Dokument** → DB-Constraint + AsyncLock, zweiter Caller wartet
8. **Query findet keine relevanten Knoten** → leere Liste, kein Crash, klassische Kanäle übernehmen
9. **Tree-Tiefe > max_tree_depth** → tiefere Sections in Parent flatten
10. **Branching Factor > Maximum** → Gruppen-Knoten einfügen
11. **Alle Children eines Nodes haben identischen Titel** → Disambiguation via Position-Suffix
12. **Source-File wurde gelöscht, aber Tree existiert noch** → Tree bleibt nutzbar (read-only), Reindex nicht möglich, log warning
13. **Deutsche Umlaute, BOM, Mixed Encoding** → automatische Erkennung via `chardet`/`charset-normalizer`, Fallback UTF-8
14. **Sehr kurze Dokumente** (<100 Tokens) → kein hierarchischer Index, Empfehlung an User: nutze klassisches Indexing

## Tests

Erstelle Tests unter `tests/memory/hierarchical/`:

- `test_tree_builder.py` – alle Parser, alle Edge Cases der Hierarchie-Erstellung
- `test_parsers/test_markdown.py` – ATX, Setext, Code-Blocks, Lists, gemischt
- `test_parsers/test_pdf.py` – mit Sample-PDFs (Fixtures unter `tests/fixtures/pdfs/`)
- `test_parsers/test_docx.py` – mit Sample-DOCX
- `test_parsers/test_html.py` – mit Sample-HTML inkl. Navigation-Filtering
- `test_parsers/test_plaintext.py` – inkl. deutscher Rechtsdokumente mit `§`, `Abs.`, `Art.`
- `test_tree_store.py` – Persistenz, CASCADE-Delete, Transaktionen
- `test_node_selector.py` – mit gemocktem LLM, JSON-Parse-Robustheit
- `test_retrieval.py` – End-to-End: Dokument indizieren, Query, Ergebnis prüfen
- `test_search_integration.py` – 4-Kanal-Hybrid-Search mit allen Kanälen aktiv, Score-Fusion-Korrektheit
- `test_concurrent_indexing.py` – Race-Conditions
- `test_edge_cases.py` – alle 14 Edge Cases oben

Test-Fixtures:
- `tests/fixtures/documents/avb_sample.md` – simulierte AVB
- `tests/fixtures/documents/contract.docx`
- `tests/fixtures/documents/legal_paragraphs.txt` – mit deutschen Paragraphen-Markern
- `tests/fixtures/documents/long_report.pdf` – >100 Seiten

Alle Tests deterministisch. LLM-Calls gemockt mit deterministischen Responses.

---

# Cross-Cutting Concerns – beide Features

## Logging

- Strukturiertes Logging via existierender Cognithor-Logger
- Log-Level: DEBUG für Details, INFO für Lifecycle-Events, WARNING für Recovery, ERROR für Failures
- KEINE PII in Logs (Content niemals loggen, nur Hashes und IDs)

## Error Handling

- Eigene Exception-Hierarchie:
  - `CAGError(MemoryError)` mit Subklassen `CAGCapacityError`, `CAGBackendError`, `CAGCorruptionError`
  - `HierarchicalIndexError(MemoryError)` mit Subklassen `ParserError`, `TreeBuildError`, `NodeSelectionError`
- Niemals stille Failures – jeder Recovery muss geloggt werden
- Public-API-Methoden müssen klare Exceptions werfen, keine `None`-Returns für Fehlerfälle (außer explizit dokumentiert)

## Type Hints

- 100% type-hinted
- `from __future__ import annotations` in allen Files
- `mypy --strict` muss durchlaufen

## Async

- Alle I/O ist async
- LLM-Calls sind async
- DB-Calls über existierende async-Wrapper
- Locks via `asyncio.Lock` für In-Process, `fcntl`/`msvcrt` für Cross-Process

## Documentation

- Docstrings im Google-Style für jede Public Function
- README in `src/jarvis/memory/cag/README.md` und `src/jarvis/memory/hierarchical/README.md`
- Architektur-Diagramme als ASCII-Art in den README-Files
- Update der Top-Level-Architektur-Dokumentation um beide neuen Subsysteme
- CHANGELOG-Eintrag mit klarer Feature-Beschreibung

## Performance-Ziele

**CAG:**
- Cache-Build für 50.000 Token Core Memory: <60 Sekunden auf Ryzen 9 9950X3D + RTX 5090
- Cache-Load: <500 ms
- Cache-Hit-Rate für Core Memory: >95% bei normalem Use
- Speicher-Overhead pro Cache: max. 2× der reinen Token-Größe

**Hierarchical:**
- Tree-Build für 100-Seiten-PDF: <5 Minuten inkl. aller Summary-LLM-Calls
- Node-Selection für eine Query: <3 Sekunden für Trees mit <500 Knoten
- Zusätzliche DB-Größe: max. 5× der Original-Dokumentgröße

## Pre-Push Workflow

Bevor du irgendetwas pushst:

1. `pytest tests/memory/cag/ -v` – muss komplett grün sein
2. `pytest tests/memory/hierarchical/ -v` – muss komplett grün sein
3. `pytest tests/memory/ -v` – alle bestehenden Memory-Tests müssen weiterhin grün sein
4. `pytest tests/ -v` – die volle Test-Suite muss grün sein, Coverage darf NICHT unter den aktuellen Wert fallen
5. `mypy --strict src/jarvis/memory/cag/ src/jarvis/memory/hierarchical/`
6. `ruff check src/jarvis/memory/`
7. Lokales Pre-Push-Test-Skript ausführen
8. Manueller Smoke-Test mit einem echten Cognithor-Run

## Branch- und Commit-Strategie

- Branch: `feature/retrieval-extensions-cag-hierarchical`
- Atomare Commits, ein Commit pro logischer Einheit
- Conventional Commits: `feat(memory/cag): ...`, `feat(memory/hierarchical): ...`, `test(memory/cag): ...`, `docs(memory): ...`
- Keine Mega-Commits mit gemischten Konzepten
- Vor dem Merge: rebase auf main, alle Test-Suites grün, CHANGELOG aktualisiert

---

# Reihenfolge der Implementierung

Folge dieser Reihenfolge strikt, weil jedes Feature in sich getestet sein muss, bevor Integration erfolgt:

1. **CAG: Foundation** – `models`, `cache_store`, `invalidation`, `selectors`, alle zugehörigen Tests
2. **CAG: Builders** – `base`, `llamacpp`, `vllm`, `ollama`, jeweils mit Tests
3. **CAG: Manager** – `manager.py`, Lifecycle, Tests
4. **CAG: Integration** – Hooks in `MemoryManager`, Inferenz-Pfad-Erweiterung, End-to-End-Tests
5. **Hierarchical: Foundation** – `models`, `tree_store`, alle Parser, Parser-Tests
6. **Hierarchical: Tree Builder** – `tree_builder`, mit Tests für alle Edge Cases
7. **Hierarchical: Node Selector** – `node_selector`, `prompts`, Tests
8. **Hierarchical: Retriever** – `retrieval`, Integration in `search.py` als 4. Kanal, Score-Fusion-Tests
9. **Hierarchical: Manager-Integration** – Erweiterungen in `MemoryManager`, End-to-End
10. **Cross-Feature-Integration** – ein realer Test-Run mit beiden Features aktiv, beide gleichzeitig
11. **Documentation** – READMEs, CHANGELOG, Architektur-Update
12. **Pre-Push-Sweep** – volle Test-Suite, mypy, ruff, manueller Smoke-Test

---

# Was du NIEMALS tun darfst

- Public-API von `MemoryManager` ändern (nur erweitern)
- Bestehende Tabellen in der SQLite-DB ändern oder löschen
- Existierende Tests löschen oder skippen
- Cloud-Services anbinden
- Hardcoded Modellnamen in Code (alles über Config)
- Telemetrie nach außen senden
- Synchrone I/O auf dem Hot-Path
- `print()` statt Logger
- `except Exception: pass`
- Globale Mutable State außerhalb von Manager-Instanzen
- Den Tactical Memory Tier für CAG cachen (ist explizit ausgeschlossen)
- Vektor-Embeddings im hierarchischen Kanal verwenden (das ist der ganze Punkt)

---

# Ausgabe

Wenn du fertig bist, präsentiere:

1. Eine Liste aller neu erstellten Files mit Zeilen-Anzahl
2. Test-Coverage-Report für die neuen Module
3. Ergebnis von `pytest tests/ -v` (Anzahl tests, alle grün)
4. Ergebnis von `mypy --strict` für die neuen Module
5. Ein kurzes Beispiel-Snippet, wie ein User beide Features nutzt
6. Eine Liste aller Annahmen, die du treffen musstest, weil im Spec etwas mehrdeutig war

Beginne, indem du zuerst die bestehenden Memory-Module liest und die aktuelle 6-Tier-Architektur (Core, Episodic, Semantic, Procedural, Working, Tactical) und das 3-Kanal-Hybrid-Search-System komplett verstehst. Stelle Fragen NUR, wenn etwas in diesem Spec wirklich mehrdeutig ist – sonst implementiere durch.
