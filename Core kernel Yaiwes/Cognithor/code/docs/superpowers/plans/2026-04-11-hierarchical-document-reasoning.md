# Hierarchical Document Reasoning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a 4th retrieval channel to Cognithor's memory that indexes documents as hierarchical trees and uses LLM-driven top-down navigation to find relevant sections — without vector embeddings.

**Architecture:** New `src/cognithor/memory/hierarchical/` package with 5 document parsers, SQLite tree storage, LLM node selector, and integration into the existing 3-channel HybridSearch as a 4th channel with auto-normalizing score fusion.

**Tech Stack:** Python 3.12+, SQLite (existing), pymupdf (PDF), python-docx (DOCX), beautifulsoup4 (HTML), asyncio, existing LLM provider abstraction

---

## File Map

### New files (create)
```
src/cognithor/memory/hierarchical/__init__.py
src/cognithor/memory/hierarchical/models.py
src/cognithor/memory/hierarchical/parsers/__init__.py
src/cognithor/memory/hierarchical/parsers/base.py
src/cognithor/memory/hierarchical/parsers/markdown.py
src/cognithor/memory/hierarchical/parsers/plaintext.py
src/cognithor/memory/hierarchical/parsers/pdf.py
src/cognithor/memory/hierarchical/parsers/docx.py
src/cognithor/memory/hierarchical/parsers/html.py
src/cognithor/memory/hierarchical/tree_store.py
src/cognithor/memory/hierarchical/tree_builder.py
src/cognithor/memory/hierarchical/prompts.py
src/cognithor/memory/hierarchical/node_selector.py
src/cognithor/memory/hierarchical/retrieval.py
src/cognithor/memory/hierarchical/manager.py
tests/memory/hierarchical/__init__.py
tests/memory/hierarchical/test_models.py
tests/memory/hierarchical/test_parsers/__init__.py
tests/memory/hierarchical/test_parsers/test_markdown.py
tests/memory/hierarchical/test_parsers/test_plaintext.py
tests/memory/hierarchical/test_parsers/test_pdf.py
tests/memory/hierarchical/test_parsers/test_docx.py
tests/memory/hierarchical/test_parsers/test_html.py
tests/memory/hierarchical/test_tree_store.py
tests/memory/hierarchical/test_tree_builder.py
tests/memory/hierarchical/test_node_selector.py
tests/memory/hierarchical/test_retrieval.py
tests/memory/hierarchical/test_search_integration.py
tests/memory/hierarchical/test_edge_cases.py
tests/fixtures/documents/avb_sample.md
tests/fixtures/documents/legal_paragraphs.txt
```

### Modified files
```
src/cognithor/config.py                  — add HierarchicalConfig
src/cognithor/memory/search.py           — add 4th channel + score fusion
src/cognithor/memory/manager.py          — add 4 new public methods
```

---

### Task 1: Data Models + Package Scaffold

**Files:**
- Create: `src/cognithor/memory/hierarchical/__init__.py`
- Create: `src/cognithor/memory/hierarchical/models.py`
- Create: `src/cognithor/memory/hierarchical/parsers/__init__.py`
- Create: `src/cognithor/memory/hierarchical/parsers/base.py`
- Test: `tests/memory/hierarchical/__init__.py`
- Test: `tests/memory/hierarchical/test_models.py`

**Scope:** Create the package structure, all dataclasses (TreeNode, DocumentTree, RawSection, SelectedNode, DocumentMetadata), the DocumentParser ABC, and the parser factory stub. Test that all models are frozen, have correct defaults, and the parser factory raises for unsupported extensions.

- [ ] **Step 1:** Create package init files (`__init__.py` for `hierarchical/` and `parsers/`)
- [ ] **Step 2:** Implement `models.py` with all 5 dataclasses from the spec (TreeNode, DocumentTree, RawSection, SelectedNode, DocumentMetadata)
- [ ] **Step 3:** Implement `parsers/base.py` with DocumentParser ABC and `parsers/__init__.py` with `get_parser()` factory (raises `ParserError` for unknown extensions, returns correct parser class for `.md`, `.pdf`, `.docx`, `.html`, `.txt`)
- [ ] **Step 4:** Implement exception hierarchy: `HierarchicalIndexError`, `ParserError`, `TreeBuildError`, `NodeSelectionError` in `models.py`
- [ ] **Step 5:** Write `test_models.py`: test frozen dataclasses, default values, exception hierarchy
- [ ] **Step 6:** Run tests, verify pass
- [ ] **Step 7:** Commit: `feat(memory/hierarchical): add data models and package scaffold`

---

### Task 2: Markdown Parser

**Files:**
- Create: `src/cognithor/memory/hierarchical/parsers/markdown.py`
- Create: `tests/memory/hierarchical/test_parsers/__init__.py`
- Create: `tests/memory/hierarchical/test_parsers/test_markdown.py`
- Create: `tests/fixtures/documents/avb_sample.md`

**Scope:** Parse Markdown documents into flat `RawSection` lists. Handle ATX headings (`#` through `######`), Setext headings (`===`/`---`), code blocks (fenced and indented, never split), and mixed content.

- [ ] **Step 1:** Create `avb_sample.md` fixture — simulated German insurance conditions with h1/h2/h3, code blocks, lists, paragraphs (~200 lines)
- [ ] **Step 2:** Write `test_markdown.py` with tests: ATX headings produce correct levels, Setext headings detected, code blocks stay atomic, content between headings captured, empty document returns single root section, no-heading document returns single section
- [ ] **Step 3:** Implement `MarkdownParser` — regex-based ATX/Setext detection, code block tracking (fenced ``` state machine), section accumulation
- [ ] **Step 4:** Run tests, verify pass
- [ ] **Step 5:** Commit: `feat(memory/hierarchical): add Markdown parser`

---

### Task 3: Plaintext Parser

**Files:**
- Create: `src/cognithor/memory/hierarchical/parsers/plaintext.py`
- Create: `tests/memory/hierarchical/test_parsers/test_plaintext.py`
- Create: `tests/fixtures/documents/legal_paragraphs.txt`

**Scope:** Parse unstructured text using heuristics: German legal markers (`§`, `Art.`, `Abs.`), numbered patterns (`1.`, `1.1`, `I.`), ALL-CAPS lines, isolated short lines. Fallback: split by double-newlines.

- [ ] **Step 1:** Create `legal_paragraphs.txt` fixture — German legal text with `§ 1`, `§ 2`, `Abs. 1`, numbered sub-sections (~100 lines)
- [ ] **Step 2:** Write `test_plaintext.py`: German `§`-markers detected as h1, `Abs.` as h2, ALL-CAPS lines as headings, numbered patterns, fallback to paragraph splitting, empty document handling
- [ ] **Step 3:** Implement `PlainTextParser` — priority-ordered regex patterns, blank-line paragraph fallback
- [ ] **Step 4:** Run tests, verify pass
- [ ] **Step 5:** Commit: `feat(memory/hierarchical): add Plaintext parser with German legal heuristics`

---

### Task 4: PDF Parser

**Files:**
- Create: `src/cognithor/memory/hierarchical/parsers/pdf.py`
- Create: `tests/memory/hierarchical/test_parsers/test_pdf.py`

**Scope:** Parse PDFs using pymupdf. Font-size heuristic (top 20% = headings), TOC preferred if available, page numbers tracked. No test fixture PDF committed — tests mock pymupdf.

- [ ] **Step 1:** Write `test_pdf.py` with mocked pymupdf: TOC extraction produces correct levels, font-size heuristic detects headings, page numbers tracked, corrupt PDF raises ParserError, empty PDF returns empty list
- [ ] **Step 2:** Implement `PDFParser` — try TOC first via `doc.get_toc()`, fallback to font-size analysis, track page numbers per section
- [ ] **Step 3:** Run tests, verify pass
- [ ] **Step 4:** Commit: `feat(memory/hierarchical): add PDF parser`

---

### Task 5: DOCX Parser

**Files:**
- Create: `src/cognithor/memory/hierarchical/parsers/docx.py`
- Create: `tests/memory/hierarchical/test_parsers/test_docx.py`

**Scope:** Parse Word documents using python-docx. Primary: Heading styles (`Heading 1` through `6`). Fallback: bold text with large font. Tests mock python-docx.

- [ ] **Step 1:** Write `test_docx.py` with mocked python-docx: heading styles produce correct levels, bold+large font fallback works, tables converted to text, empty document handling, corrupt file raises ParserError
- [ ] **Step 2:** Implement `DocxParser` — iterate paragraphs, check style names, fallback bold+font detection
- [ ] **Step 3:** Run tests, verify pass
- [ ] **Step 4:** Commit: `feat(memory/hierarchical): add DOCX parser`

---

### Task 6: HTML Parser

**Files:**
- Create: `src/cognithor/memory/hierarchical/parsers/html.py`
- Create: `tests/memory/hierarchical/test_parsers/test_html.py`

**Scope:** Parse HTML using beautifulsoup4. h1-h6 define structure. Filter nav/footer/aside/header elements and classes containing `nav`, `menu`, `footer`, `sidebar`. Strip script/style tags.

- [ ] **Step 1:** Write `test_html.py`: h1-h6 produce correct levels, nav/footer filtered out, script/style stripped, class-based filtering works, nested sections, empty HTML, malformed HTML handling
- [ ] **Step 2:** Implement `HtmlParser` — BeautifulSoup parsing, tag-based filtering, class heuristic filtering, recursive section extraction
- [ ] **Step 3:** Run tests, verify pass
- [ ] **Step 4:** Commit: `feat(memory/hierarchical): add HTML parser`

---

### Task 7: Tree Store (SQLite Persistence)

**Files:**
- Create: `src/cognithor/memory/hierarchical/tree_store.py`
- Create: `tests/memory/hierarchical/test_tree_store.py`

**Scope:** SQLite persistence in `hierarchical_documents` + `hierarchical_nodes` tables. Same DB as existing indexer. All writes in transaction. CASCADE delete. Uses `encrypted_connect()` if available.

- [ ] **Step 1:** Write `test_tree_store.py`: save_tree persists all fields, load_tree reconstructs DocumentTree, delete_tree cascades to nodes, list_documents returns metadata, has_any_documents returns bool, duplicate document_id re-inserts cleanly, tables created on first access
- [ ] **Step 2:** Implement `TreeStore` with `__init__`, `_ensure_tables`, `save_tree`, `load_tree`, `delete_tree`, `list_documents`, `has_any_documents` — all using transactions, parameterized queries
- [ ] **Step 3:** Run tests, verify pass
- [ ] **Step 4:** Commit: `feat(memory/hierarchical): add SQLite tree store`

---

### Task 8: Tree Builder

**Files:**
- Create: `src/cognithor/memory/hierarchical/tree_builder.py`
- Create: `tests/memory/hierarchical/test_tree_builder.py`

**Scope:** The core algorithm: parser selection → flat sections → hierarchy → content splitting → summary generation → constraint enforcement → DocumentTree. LLM calls mocked in tests.

- [ ] **Step 1:** Write `test_tree_builder.py`: flat sections become correct tree, heading jumps insert virtual nodes, content >4000 tokens splits into parts, branching >50 inserts groups, depth >8 flattens, bottom-up summary generation called in correct order, progress callback invoked, empty document produces single root, short document (<100 tokens) raises info
- [ ] **Step 2:** Implement `DocumentTreeBuilder.__init__` and `async build()` — the full 8-step algorithm from the spec. Summary generation as async batched LLM calls (max `parallel_summary_generation` concurrent). Token counting via `len(text.split()) * 1.3`.
- [ ] **Step 3:** Run tests, verify pass
- [ ] **Step 4:** Commit: `feat(memory/hierarchical): add tree builder with hierarchy construction`

---

### Task 9: Prompts + Node Selector

**Files:**
- Create: `src/cognithor/memory/hierarchical/prompts.py`
- Create: `src/cognithor/memory/hierarchical/node_selector.py`
- Create: `tests/memory/hierarchical/test_node_selector.py`

**Scope:** LLM-driven top-down tree traversal. German and English prompts. JSON parsing with regex fallback. 3 consecutive failures = cancel. 30s timeout.

- [ ] **Step 1:** Implement `prompts.py` — German and English prompt templates as string constants. Each takes `query`, `children_info` (list of title+summary pairs), returns formatted prompt string.
- [ ] **Step 2:** Write `test_node_selector.py`: correct children selected from mock LLM response, recursive traversal stops at leaves, max_nodes limit respected, JSON parse with regex fallback, 3 consecutive parse failures returns empty, empty selected_node_ids stops traversal, content trimmed to max_tokens_per_node (keep start+end)
- [ ] **Step 3:** Implement `LLMNodeSelector` — `__init__` with llm_fn/language/timeout, `async select_nodes()` with recursive top-down traversal, JSON parsing, content trimming
- [ ] **Step 4:** Run tests, verify pass
- [ ] **Step 5:** Commit: `feat(memory/hierarchical): add LLM node selector with top-down traversal`

---

### Task 10: Retrieval Channel

**Files:**
- Create: `src/cognithor/memory/hierarchical/retrieval.py`
- Create: `tests/memory/hierarchical/test_retrieval.py`

**Scope:** `HierarchicalRetriever` wraps TreeStore + NodeSelector. Returns results compatible with HybridSearch scoring. Score = `1.0 / (1 + depth) * llm_confidence`.

- [ ] **Step 1:** Write `test_retrieval.py`: search returns scored results, score calculation correct (depth 0 = 0.8, depth 1 = 0.4, depth 2 = 0.27), empty tree returns empty results, results mapped to correct format with source_type="hierarchical"
- [ ] **Step 2:** Implement `HierarchicalRetriever` — `__init__` with tree_store + node_selector, `async search()` that loads all trees, runs node selection on each, scores results, returns top N
- [ ] **Step 3:** Run tests, verify pass
- [ ] **Step 4:** Commit: `feat(memory/hierarchical): add hierarchical retrieval channel`

---

### Task 11: Manager + Config + Integration

**Files:**
- Create: `src/cognithor/memory/hierarchical/manager.py`
- Modify: `src/cognithor/config.py`
- Modify: `src/cognithor/memory/search.py`
- Modify: `src/cognithor/memory/manager.py`
- Create: `tests/memory/hierarchical/test_search_integration.py`

**Scope:** Wire everything together. HierarchicalConfig in config.py. 4th channel in HybridSearch. 4 new methods on MemoryManager. AsyncLock for concurrent indexing.

- [ ] **Step 1:** Add `HierarchicalConfig` to `config.py` (enabled, max_nodes, max_tokens, score_weight, branching, depth, split_threshold, parallel_summaries). Add `hierarchical: HierarchicalConfig = Field(default_factory=HierarchicalConfig)` to `MemoryConfig`.

- [ ] **Step 2:** Implement `manager.py` (HierarchicalIndexManager) — wraps TreeStore + TreeBuilder + HierarchicalRetriever. Methods: `async index_document()`, `async remove_document()`, `async list_documents()`, `async reindex_document()`. AsyncLock for concurrent protection.

- [ ] **Step 3:** Modify `search.py` — add optional `hierarchical_retriever` parameter to `HybridSearch.__init__()`. Add `async _hierarchical_channel()` method. Modify score fusion to include 4th weight with auto-normalization. When no hierarchical docs exist or retriever is None, `w_h = 0` and formula reduces to original 3-channel.

- [ ] **Step 4:** Modify `manager.py` (MemoryManager) — in `__init__`, if `config.memory.hierarchical.enabled`: instantiate HierarchicalIndexManager, pass retriever to HybridSearch. Add 4 public methods that delegate to HierarchicalIndexManager.

- [ ] **Step 5:** Write `test_search_integration.py`: 4-channel fusion with all channels active produces correct scores, w_h=0 when no hierarchical docs reduces to 3-channel, weight normalization is correct (sum to 1.0), hierarchical results have source_type="hierarchical"

- [ ] **Step 6:** Run ALL tests (not just new ones): `pytest tests/memory/ -v`
- [ ] **Step 7:** Commit: `feat(memory/hierarchical): integrate 4th channel into HybridSearch`

---

### Task 12: Edge Cases + Final Tests

**Files:**
- Create: `tests/memory/hierarchical/test_edge_cases.py`

**Scope:** All 14 edge cases from the spec. Each as a separate test function.

- [ ] **Step 1:** Write `test_edge_cases.py` with 14 test functions:
  - `test_no_headings` — single root node
  - `test_heading_jumps` — virtual intermediate nodes
  - `test_large_document` — progress callback, no OOM (mock large content)
  - `test_corrupt_file` — ParserError raised
  - `test_duplicate_document_id` — re-index replaces old
  - `test_llm_unreachable` — HierarchicalIndexError after 3 retries
  - `test_concurrent_index` — AsyncLock prevents race
  - `test_query_finds_nothing` — empty list returned
  - `test_depth_exceeds_max` — deeper content flattened
  - `test_branching_exceeds_max` — group nodes inserted
  - `test_identical_children_titles` — position suffix added
  - `test_source_deleted` — tree still readable
  - `test_encoding_issues` — BOM/mixed encoding handled
  - `test_very_short_document` — no index created, info logged

- [ ] **Step 2:** Run tests, verify all pass
- [ ] **Step 3:** Run full project test suite: `pytest tests/ -x -q --tb=line`
- [ ] **Step 4:** Run lint: `ruff format src/cognithor/memory/hierarchical/ tests/memory/hierarchical/` and `ruff check src/ tests/ --select=F821,F811`
- [ ] **Step 5:** Commit: `test(memory/hierarchical): add edge case tests — all 14 covered`

---

### Task 13: Final Verification + Cleanup

**Files:** All files from Tasks 1-12

- [ ] **Step 1:** Verify import: `python -c "from cognithor.memory.hierarchical import HierarchicalIndexManager; print('OK')"`
- [ ] **Step 2:** Verify config: `python -c "from cognithor.config import JarvisConfig; c = JarvisConfig(); print(c.memory.hierarchical.enabled)"`
- [ ] **Step 3:** Run targeted tests: `pytest tests/memory/hierarchical/ -v` — ALL PASS
- [ ] **Step 4:** Run full suite: `pytest tests/ -x -q` — no regressions
- [ ] **Step 5:** Final commit: `feat(memory/hierarchical): complete hierarchical document reasoning — 4th retrieval channel`
