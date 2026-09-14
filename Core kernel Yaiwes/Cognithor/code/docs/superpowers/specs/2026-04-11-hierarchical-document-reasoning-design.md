# Hierarchical Document Reasoning — Design Spec

**Goal:** Add a 4th retrieval channel to Cognithor's memory system that represents long structured documents (contracts, manuals, legal texts) as hierarchical trees and lets the LLM navigate to relevant nodes via top-down semantic reasoning — without vector embeddings.

**Issue:** Feature 2 from `docs/cognithor_retrieval_extensions_prompt.md`

**Package:** `src/cognithor/memory/hierarchical/`

---

## 1. Module Structure

```
src/cognithor/memory/hierarchical/
├── __init__.py
├── models.py              # TreeNode, DocumentTree, RawSection, SelectedNode, DocumentMetadata
├── tree_builder.py        # DocumentTreeBuilder
├── tree_store.py          # TreeStore — SQLite persistence (same DB as indexer)
├── node_selector.py       # LLMNodeSelector — top-down tree traversal
├── retrieval.py           # HierarchicalRetriever — 4th search channel
├── manager.py             # HierarchicalIndexManager
├── prompts.py             # DE/EN system prompts for node selection
└── parsers/
    ├── __init__.py        # get_parser(path) factory
    ├── base.py            # DocumentParser ABC + RawSection dataclass
    ├── markdown.py        # MarkdownParser — ATX + Setext headings
    ├── pdf.py             # PDFParser — font-size heuristic + TOC
    ├── docx.py            # DocxParser — Word heading styles
    ├── html.py            # HtmlParser — h1-h6, nav/footer filtering
    └── plaintext.py       # PlainTextParser — §, Abs., Art., ALL-CAPS
```

**Modified existing files:**
- `src/cognithor/memory/search.py` — add `_hierarchical_channel()`, extend score fusion
- `src/cognithor/memory/manager.py` — add 4 new public methods
- `src/cognithor/config.py` — add `HierarchicalConfig` section

---

## 2. Data Model (`models.py`)

```python
from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RawSection:
    """Flat section extracted by a parser before hierarchy construction."""
    level: int              # 0=document, 1=h1, 2=h2, ...
    title: str
    content: str
    position: int           # order in source document
    page: int | None = None # PDF page number


@dataclass(frozen=True)
class TreeNode:
    """Single node in a document tree."""
    node_id: str                          # UUID hex
    document_id: str
    parent_id: str | None                 # None = root
    level: int                            # 0=root, 1=h1, 2=h2, ...
    title: str
    summary: str                          # LLM-generated, 1-2 sentences
    content: str                          # full text of this section (without children)
    content_hash: str                     # sha256 of content
    token_count: int
    children_ids: tuple[str, ...]
    position: int                         # order within parent
    page_number: int | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DocumentTree:
    """Complete hierarchical representation of a document."""
    document_id: str
    source_path: Path
    source_hash: str                      # sha256 of source file
    title: str
    root_node_id: str
    nodes: Mapping[str, TreeNode]         # node_id -> TreeNode
    created_at: datetime
    parser_used: str
    total_tokens: int


@dataclass(frozen=True)
class SelectedNode:
    """A node selected by the LLM during tree traversal."""
    node: TreeNode
    depth: int                            # depth at which it was selected
    reasoning: str                        # LLM's explanation
    score: float                          # computed relevance score


@dataclass(frozen=True)
class DocumentMetadata:
    """Summary info for listing documents."""
    document_id: str
    title: str
    source_path: str
    parser_used: str
    total_tokens: int
    node_count: int
    created_at: str
```

---

## 3. Parsers (`parsers/`)

### 3.1 Base (`parsers/base.py`)

```python
from abc import ABC, abstractmethod

class DocumentParser(ABC):
    """Extracts flat sections from a document."""

    @abstractmethod
    def parse(self, content: str | bytes, source_path: Path) -> list[RawSection]:
        """Return ordered list of sections."""
        ...

    @abstractmethod
    def supported_extensions(self) -> frozenset[str]:
        """File extensions this parser handles (e.g. {'.md', '.markdown'})."""
        ...
```

### 3.2 Parser factory (`parsers/__init__.py`)

```python
def get_parser(source_path: Path) -> DocumentParser:
    """Select parser by file extension. Raises ParserError if unsupported."""
```

Extension mapping:
- `.md`, `.markdown` → MarkdownParser
- `.pdf` → PDFParser
- `.docx` → DocxParser
- `.html`, `.htm` → HtmlParser
- `.txt`, `.text`, no extension → PlainTextParser

### 3.3 MarkdownParser

- ATX headings: `#` through `######`
- Setext headings: `===` (h1) and `---` (h2)
- Code blocks (fenced ``` and indented) treated as atomic content — never split
- List items within a section remain part of that section's content

### 3.4 PDFParser

- Uses existing `pymupdf` dependency
- Font-size heuristic: top 20% of font sizes in the document = heading candidates
- If PDF has structured TOC (`get_toc()`): use TOC entries as headings, override heuristic
- Page numbers tracked per section
- Images and tables skipped (content only)

### 3.5 DocxParser

- Uses existing `python-docx` dependency
- Primary: Word heading styles (`Heading 1` through `Heading 6`)
- Fallback: Bold text with font size >= 14pt treated as heading
- Tables converted to plain text representation

### 3.6 HtmlParser

- `<h1>` through `<h6>` define structure
- Filters out: `<nav>`, `<footer>`, `<aside>`, `<header>` elements
- Heuristic class filtering: elements with class containing `nav`, `menu`, `footer`, `sidebar`
- Uses `beautifulsoup4` (already a dependency under `[memory]`)
- Script/style tags stripped

### 3.7 PlainTextParser

- Heuristic heading detection (ordered by priority):
  1. `§ N` / `Art. N` / `Abs. N` — German legal structure markers
  2. Numbered patterns: `1.`, `1.1`, `1.1.1`, `I.`, `II.`, `a)`, `(1)`
  3. ALL-CAPS lines (min 3 words, max 80 chars)
  4. Lines preceded and followed by blank lines (isolated short text)
- Fallback if no headings detected: split by double-newlines into paragraphs

---

## 4. Tree Builder (`tree_builder.py`)

### Algorithm (exact order)

1. **Parser selection** by file extension via `get_parser()`
2. **Structural extraction**: parser returns `list[RawSection]`
3. **Hierarchy construction**: iterate flat list, build tree by level.
   - If h2 appears without preceding h1: insert virtual h1 "Untitled Section"
   - If level jumps (h1→h3): insert virtual intermediate nodes
4. **Content splitting**: nodes >4,000 tokens → split by paragraphs into sub-nodes (level+1, titled "Part 1", "Part 2", ...)
5. **Constraint enforcement**:
   - Branching factor >50 → insert group nodes ("Group 1", "Group 2")
   - Depth >8 → flatten deeper content into parent's content
6. **Summary generation**: bottom-up LLM calls.
   - Leaf nodes first: summary from content
   - Parent nodes: summary from children's summaries
   - Async batched, max 10 parallel calls
   - Each call uses existing LLM provider abstraction
7. **Token counting** via simple whitespace split (words * 1.3 ≈ tokens)
8. **Persist** via TreeStore (single transaction)

### Interface

```python
class DocumentTreeBuilder:
    def __init__(
        self,
        llm_fn: Callable,           # existing LLM function
        max_parallel_summaries: int = 10,
        node_split_threshold: int = 4000,
        max_branching_factor: int = 50,
        max_depth: int = 8,
    ) -> None: ...

    async def build(
        self,
        source_path: Path,
        document_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> DocumentTree: ...
```

---

## 5. Tree Store (`tree_store.py`)

SQLite tables in the **same database** as the existing indexer (`~/.cognithor/index/memory.db`):

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

CREATE INDEX IF NOT EXISTS idx_hn_document ON hierarchical_nodes(document_id);
CREATE INDEX IF NOT EXISTS idx_hn_parent ON hierarchical_nodes(parent_id);
```

**Rules:**
- All writes in a single transaction. Rollback on any error — no partial trees.
- CASCADE delete: removing a document removes all its nodes.
- Re-index: delete old tree first (CASCADE), then insert new.
- Uses `encrypted_connect()` from existing security module if encryption is enabled.

### Interface

```python
class TreeStore:
    def __init__(self, db_path: Path) -> None: ...
    def save_tree(self, tree: DocumentTree) -> None: ...
    def load_tree(self, document_id: str) -> DocumentTree | None: ...
    def delete_tree(self, document_id: str) -> None: ...
    def list_documents(self) -> list[DocumentMetadata]: ...
    def has_any_documents(self) -> bool: ...
```

---

## 6. LLM Node Selector (`node_selector.py`)

### Algorithm (top-down tree traversal)

1. Start at root node
2. Build prompt: user query + title/summary of all direct children
3. LLM responds with JSON: `{"selected_node_ids": ["id1", "id2"], "reasoning": "..."}`
4. For each selected child: recurse step 2
5. Leaf nodes or LLM-marked "answer-bearing" nodes → add to results
6. Stop when `max_nodes` reached or no more selections possible
7. Trim each selected node's content to `max_tokens_per_node` (keep start+end, trim middle)

### Robustness

- JSON parsing with regex fallback (`re.search(r'\{.*\}', response, re.DOTALL)`)
- 3 consecutive parse failures → cancel, return empty list
- 30-second timeout per LLM call
- All LLM calls via existing provider abstraction (not direct HTTP)
- Empty `selected_node_ids` array = no relevant children, stop traversal

### Prompts (`prompts.py`)

German (default) and English variants. German:

```
Du bist ein Dokument-Navigator. Gegeben ist eine User-Frage und eine Liste
von Abschnitten mit Titel und Kurzbeschreibung. Waehle bis zu 3 Abschnitte
aus, die die Antwort am wahrscheinlichsten enthalten.

Antworte AUSSCHLIESSLICH mit JSON:
{"selected_node_ids": ["id1", "id2"], "reasoning": "kurze Begruendung"}

Wenn KEIN Abschnitt relevant ist, antworte: {"selected_node_ids": [], "reasoning": "nicht relevant"}
```

### Interface

```python
class LLMNodeSelector:
    def __init__(
        self,
        llm_fn: Callable,
        language: str = "de",
        timeout_seconds: float = 30.0,
    ) -> None: ...

    async def select_nodes(
        self,
        query: str,
        tree: DocumentTree,
        max_nodes: int = 5,
        max_tokens_per_node: int = 2000,
    ) -> list[SelectedNode]: ...
```

---

## 7. Retrieval Channel (`retrieval.py`)

```python
class HierarchicalRetriever:
    def __init__(
        self,
        tree_store: TreeStore,
        node_selector: LLMNodeSelector,
    ) -> None: ...

    async def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[ScoredResult]: ...
```

**Scoring:** `score = 1.0 / (1 + depth) * llm_confidence`
- `depth` = tree level at which the node was selected
- `llm_confidence` = heuristic from reasoning length (default 0.8)

**Result mapping:** Each `SelectedNode` is mapped to the existing `ScoredResult` format with `source_type = "hierarchical"`. No changes to `ScoredResult` dataclass.

---

## 8. Search Integration (`search.py` modification)

### New private method

```python
async def _hierarchical_channel(self, query: str, top_k: int) -> dict[str, float]:
    """Return {memory_id: score} from hierarchical retrieval."""
```

Only runs if `self._hierarchical_retriever` is set AND `tree_store.has_any_documents()` is True.

### Score fusion change

Current (3-channel):
```python
final_score = (w_vector * v + w_bm25 * b + w_graph * g) * decay
```

New (4-channel):
```python
w_h = self._config.hierarchical.score_weight if hierarchical_active else 0.0
total_w = w_vector + w_bm25 + w_graph + w_h
if total_w > 0:
    final_score = (w_vector/total_w * v + w_bm25/total_w * b + w_graph/total_w * g + w_h/total_w * h) * decay
```

Weights auto-normalize. When no hierarchical documents exist, `w_h = 0` and the formula reduces to the original 3-channel version.

---

## 9. MemoryManager Integration (`manager.py` modification)

4 new public methods. **No existing methods changed.**

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

In `__init__()`: if `config.memory.hierarchical.enabled`:
- Instantiate `TreeStore`, `LLMNodeSelector`, `HierarchicalRetriever`, `DocumentTreeBuilder`
- Pass `HierarchicalRetriever` to `HybridSearch`

---

## 10. Configuration (`config.py` addition)

```python
class HierarchicalConfig(BaseModel):
    """Hierarchical Document Reasoning configuration."""
    enabled: bool = Field(default=True, description="Enable hierarchical document indexing and retrieval")
    default_max_nodes_per_query: int = Field(default=5, ge=1, le=20)
    default_max_tokens_per_node: int = Field(default=2000, ge=100, le=8000)
    score_weight: float = Field(default=0.25, ge=0.0, le=1.0, description="Weight in 4-channel score fusion")
    max_branching_factor: int = Field(default=50, ge=5, le=200)
    max_tree_depth: int = Field(default=8, ge=2, le=15)
    node_split_token_threshold: int = Field(default=4000, ge=500, le=16000)
    parallel_summary_generation: int = Field(default=10, ge=1, le=50)
```

Added to `MemoryConfig` as: `hierarchical: HierarchicalConfig = Field(default_factory=HierarchicalConfig)`

---

## 11. Exception Hierarchy

```python
class HierarchicalIndexError(Exception):
    """Base exception for hierarchical document processing."""

class ParserError(HierarchicalIndexError):
    """Document could not be parsed."""

class TreeBuildError(HierarchicalIndexError):
    """Tree construction failed."""

class NodeSelectionError(HierarchicalIndexError):
    """LLM node selection failed."""
```

---

## 12. Edge Cases (14 — all must be covered)

| # | Case | Handling |
|---|------|----------|
| 1 | No headings | Single root node with full content |
| 2 | Heading jumps (h1→h3) | Insert virtual intermediate nodes |
| 3 | >500k tokens | Chunk-wise indexing with progress callback |
| 4 | Corrupt PDF/DOCX | ParserError, no partial tree |
| 5 | Duplicate document_id | Re-index: CASCADE delete old, insert new |
| 6 | LLM unreachable | 3 retries exponential backoff, then HierarchicalIndexError |
| 7 | Concurrent index same doc | AsyncLock + DB constraint |
| 8 | Query finds nothing | Empty list, other channels still work |
| 9 | Depth > max | Flatten deeper content into parent |
| 10 | Branching > max | Insert group nodes |
| 11 | Identical children titles | Disambiguation via position suffix |
| 12 | Source file deleted | Tree usable read-only, reindex blocked |
| 13 | Encoding issues | chardet detection, UTF-8 fallback |
| 14 | Very short docs (<100 tokens) | No hierarchical index, log info |

---

## 13. Tests

```
tests/memory/hierarchical/
├── test_models.py                    # Dataclass creation, immutability, defaults
├── test_tree_builder.py              # All parsers, hierarchy, splitting, summaries
├── test_tree_store.py                # SQLite persistence, CASCADE, transactions
├── test_node_selector.py             # Mocked LLM, JSON robustness, timeout, empty array
├── test_retrieval.py                 # End-to-end: index -> query -> result
├── test_search_integration.py        # 4-channel fusion, weight normalization, w_h=0 fallback
├── test_concurrent_indexing.py       # AsyncLock, DB constraint
├── test_edge_cases.py               # All 14 edge cases above
└── test_parsers/
    ├── test_markdown.py              # ATX, Setext, code blocks, lists, mixed
    ├── test_pdf.py                   # Font-size heuristic, TOC, page numbers
    ├── test_docx.py                  # Heading styles, bold fallback
    ├── test_html.py                  # h1-h6, nav/footer filtering, script stripping
    └── test_plaintext.py             # §, Abs., Art., ALL-CAPS, numbered, fallback

tests/fixtures/documents/
├── avb_sample.md                     # Simulated insurance conditions (German)
├── contract.docx                     # Word contract with heading styles
├── legal_paragraphs.txt              # German legal text with §-markers
├── long_report.html                  # Multi-section HTML report
└── sample_report.pdf                 # Multi-page PDF with TOC
```

All tests deterministic. LLM calls mocked with fixed responses. No real disk outside `tmp_path`.

---

## 14. Performance Targets

| Metric | Target | Hardware baseline |
|--------|--------|-------------------|
| Tree build (100-page PDF) | <5 minutes incl. all LLM summary calls | Ryzen 9 + RTX 5090 |
| Node selection per query | <3 seconds for trees <500 nodes | qwen3:8b |
| Additional DB size | max 5x original document size | SQLite |
| Memory overhead | <200MB for trees with <10k nodes | Python process |

---

## 15. Implementation Order

1. `models.py` — all dataclasses
2. `parsers/base.py` + `parsers/__init__.py` — ABC + factory
3. `parsers/markdown.py` + `test_markdown.py`
4. `parsers/plaintext.py` + `test_plaintext.py`
5. `parsers/pdf.py` + `test_pdf.py`
6. `parsers/docx.py` + `test_docx.py`
7. `parsers/html.py` + `test_html.py`
8. `tree_store.py` + `test_tree_store.py`
9. `tree_builder.py` + `test_tree_builder.py`
10. `prompts.py`
11. `node_selector.py` + `test_node_selector.py`
12. `retrieval.py` + `test_retrieval.py`
13. `manager.py` — HierarchicalIndexManager
14. `config.py` modification — HierarchicalConfig
15. `search.py` modification — 4th channel + score fusion
16. `manager.py` modification — 4 new MemoryManager methods
17. `test_search_integration.py` — 4-channel fusion
18. `test_edge_cases.py` — all 14 edge cases
19. `test_concurrent_indexing.py`
20. Test fixtures creation
21. Full test suite verification
