from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import sqlite3

from schemas.base import utc_now


class LiteratureMemoryStore:
    """Cross-run persistent memory for papers, chunks, evidence, and method cards."""

    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # -- write methods --------------------------------------------------------

    def write_paper(self, paper: dict[str, Any], scope: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO lit_papers
                    (paper_id, scope, title, abstract, authors, year, keywords, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    paper.get("paper_id", ""),
                    scope,
                    paper.get("title", ""),
                    paper.get("abstract", ""),
                    json.dumps(paper.get("authors", []), ensure_ascii=False),
                    paper.get("year") or 0,
                    json.dumps(paper.get("keywords", []), ensure_ascii=False),
                    utc_now(),
                ),
            )

    def write_chunk(self, chunk: dict[str, Any], scope: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO lit_chunks
                    (chunk_id, paper_id, scope, text, section, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    chunk.get("chunk_id", ""),
                    chunk.get("paper_id", ""),
                    scope,
                    chunk.get("text", ""),
                    chunk.get("section", ""),
                    utc_now(),
                ),
            )

    def write_evidence(self, evidence: dict[str, Any], scope: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO lit_evidence
                    (evidence_id, paper_id, scope, claim_supported, quote, section, support_level, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    evidence.get("evidence_id", ""),
                    evidence.get("paper_id", ""),
                    scope,
                    evidence.get("claim_supported", ""),
                    evidence.get("quote", ""),
                    evidence.get("section", ""),
                    evidence.get("support_level", ""),
                    utc_now(),
                ),
            )

    def write_method_card(self, card: dict[str, Any], scope: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO lit_method_cards
                    (method_card_id, paper_id, scope, task, problem_setting,
                     input_modalities, model_architecture, fusion_strategy,
                     training_objective, datasets, metrics, main_results,
                     limitations, reusable_ideas, implementation_difficulty,
                     risk, evidence_ids, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    card.get("method_card_id", ""),
                    card.get("paper_id", ""),
                    scope,
                    card.get("task", ""),
                    card.get("problem_setting", ""),
                    json.dumps(card.get("input_modalities", []), ensure_ascii=False),
                    json.dumps(card.get("model_architecture", {}), ensure_ascii=False),
                    json.dumps(card.get("fusion_strategy", {}), ensure_ascii=False),
                    card.get("training_objective", ""),
                    json.dumps(card.get("datasets", []), ensure_ascii=False),
                    json.dumps(card.get("metrics", []), ensure_ascii=False),
                    card.get("main_results", ""),
                    json.dumps(card.get("limitations", []), ensure_ascii=False),
                    json.dumps(
                        card.get("reusable_ideas_for_current_topic")
                        or card.get("reusable_ideas", []),
                        ensure_ascii=False,
                    ),
                    card.get("implementation_difficulty", ""),
                    json.dumps(card.get("risk", []), ensure_ascii=False),
                    json.dumps(card.get("evidence_ids", []), ensure_ascii=False),
                    utc_now(),
                ),
            )

    def write_reference(self, reference: dict[str, Any], scope: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO lit_references
                    (ref_id, scope, title, source_paper_id, authors, year,
                     venue, relevance_score, cited_in_sections, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    reference.get("ref_id", ""),
                    scope,
                    reference.get("title", ""),
                    reference.get("source_paper_id", ""),
                    json.dumps(reference.get("authors", []), ensure_ascii=False),
                    str(reference.get("year", "")),
                    reference.get("venue", ""),
                    float(reference.get("relevance_score", 0.0) or 0.0),
                    json.dumps(reference.get("cited_in_sections", []), ensure_ascii=False),
                    utc_now(),
                ),
            )

    def write_run_artifacts(self, state_values: dict[str, Any], scope: str) -> int:
        """Persist all artifacts from a completed run. Returns total records written."""
        count = 0

        for paper in state_values.get("selected_papers", []) or []:
            if isinstance(paper, dict) and paper.get("paper_id"):
                self.write_paper(paper, scope)
                count += 1

        parsed = state_values.get("parsed_papers") or []
        if isinstance(parsed, dict):
            parsed = list(parsed.values())
        for parsed_paper in (parsed if isinstance(parsed, list) else []):
            if isinstance(parsed_paper, dict):
                chunks = parsed_paper.get("chunks", [])
                for chunk in (chunks if isinstance(chunks, list) else []):
                    if isinstance(chunk, dict) and chunk.get("chunk_id"):
                        self.write_chunk(chunk, scope)
                        count += 1

        checked = state_values.get("checked_evidence", []) or []
        if isinstance(checked, dict):
            checked = list(checked.values())
        for evidence in (checked if isinstance(checked, list) else []):
            if isinstance(evidence, dict) and evidence.get("evidence_id"):
                self.write_evidence(evidence, scope)
                count += 1

        for card in state_values.get("method_cards", []) or []:
            if isinstance(card, dict) and card.get("method_card_id"):
                self.write_method_card(card, scope)
                count += 1

        for reference in state_values.get("extracted_references", []) or []:
            if isinstance(reference, dict) and reference.get("ref_id") and reference.get("title"):
                self.write_reference(reference, scope)
                count += 1

        tree = state_values.get("experiment_tree")
        if isinstance(tree, dict) and tree.get("branch_id"):
            self.write_branch(tree, scope)
            count += 1

        return count

    # -- retrieve methods -----------------------------------------------------

    def retrieve_references(
        self, scope: str, *, min_score: float = 0.0, limit: int = 10
    ) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT ref_id, title, source_paper_id, authors, year, venue,
                       relevance_score, cited_in_sections, created_at
                FROM lit_references
                WHERE scope = ? AND relevance_score >= ?
                ORDER BY relevance_score DESC, created_at DESC
                LIMIT ?
                """,
                (scope, min_score, limit),
            ).fetchall()
        return [
            {
                "ref_id": r[0],
                "title": r[1],
                "source_paper_id": r[2],
                "authors": json.loads(r[3]) if r[3] else [],
                "year": r[4],
                "venue": r[5],
                "relevance_score": float(r[6] or 0.0),
                "cited_in_sections": json.loads(r[7]) if r[7] else [],
                "created_at": r[8],
            }
            for r in rows
        ]

    def retrieve_papers(
        self, scope: str, query: str = "", limit: int = 10
    ) -> list[dict[str, Any]]:
        like = f"%{query}%"
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT paper_id, title, abstract, authors, year, keywords, created_at
                FROM lit_papers
                WHERE scope = ? AND (title LIKE ? OR abstract LIKE ? OR keywords LIKE ?)
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (scope, like, like, like, limit),
            ).fetchall()
        return [
            {
                "paper_id": r[0], "title": r[1], "abstract": r[2],
                "authors": json.loads(r[3]) if r[3] else [],
                "year": r[4],
                "keywords": json.loads(r[5]) if r[5] else [],
                "created_at": r[6],
            }
            for r in rows
        ]

    def retrieve_method_cards(
        self,
        scope: str,
        *,
        task: str | None = None,
        dataset: str | None = None,
        metric: str | None = None,
        fusion_strategy: str | None = None,
        topic_keywords: list[str] | None = None,
        paper_ids: list[str] | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Retrieve method cards with structured filters.

        Task names are normalized (underscores → spaces) so that
        ``pedestrian_trajectory_prediction`` matches ``pedestrian trajectory prediction``.
        If strict filters return zero results, the query falls back to keyword-only.
        """
        kw_tokens = _keyword_tokens(topic_keywords)

        # Try full query first
        rows = self._query_method_cards(
            scope, task, dataset, metric, fusion_strategy, kw_tokens, paper_ids, limit,
        )
        # Fallback: drop task/dataset/metric if they produced zero results but keywords exist
        if not rows and kw_tokens and (task or dataset or metric or fusion_strategy):
            rows = self._query_method_cards(
                scope, None, None, None, None, kw_tokens, paper_ids, limit,
            )

        return [
            {
                "method_card_id": r[0], "paper_id": r[1], "task": r[2],
                "problem_setting": r[3],
                "input_modalities": json.loads(r[4]) if r[4] else [],
                "model_architecture": json.loads(r[5]) if r[5] else {},
                "fusion_strategy": json.loads(r[6]) if r[6] else {},
                "training_objective": r[7],
                "datasets": json.loads(r[8]) if r[8] else [],
                "metrics": json.loads(r[9]) if r[9] else [],
                "main_results": r[10],
                "limitations": json.loads(r[11]) if r[11] else [],
                "reusable_ideas": json.loads(r[12]) if r[12] else [],
                "reusable_ideas_for_current_topic": json.loads(r[12]) if r[12] else [],
                "implementation_difficulty": r[13],
                "risk": json.loads(r[14]) if r[14] else [],
                "evidence_ids": json.loads(r[15]) if r[15] else [],
                "created_at": r[16],
            }
            for r in rows
        ]

    def _query_method_cards(
        self,
        scope: str,
        task: str | None,
        dataset: str | None,
        metric: str | None,
        fusion_strategy: str | None,
        kw_tokens: list[str],
        paper_ids: list[str] | None,
        limit: int,
    ) -> list[tuple]:
        conditions: list[str] = ["scope = ?"]
        params: list[Any] = [scope]

        if task:
            normalized = _normalize_task_patterns(task)
            task_conds = []
            for pattern in normalized:
                task_conds.append("task LIKE ?")
                params.append(f"%{pattern}%")
            conditions.append(f"({' OR '.join(task_conds)})")

        if dataset:
            conditions.append("datasets LIKE ?")
            params.append(f"%{dataset}%")

        if metric:
            conditions.append("metrics LIKE ?")
            params.append(f"%{metric}%")

        if fusion_strategy:
            conditions.append("fusion_strategy LIKE ?")
            params.append(f"%{fusion_strategy}%")

        if kw_tokens:
            kw_conds = []
            for token in kw_tokens[:12]:
                kw_conds.append("(task LIKE ? OR problem_setting LIKE ? OR main_results LIKE ?)")
                params.extend([f"%{token}%", f"%{token}%", f"%{token}%"])
            if kw_conds:
                conditions.append(f"({' OR '.join(kw_conds)})")

        if paper_ids:
            placeholders = ",".join("?" for _ in paper_ids)
            conditions.append(f"paper_id IN ({placeholders})")
            params.extend(paper_ids)

        where = " AND ".join(conditions)
        with self._connect() as conn:
            return conn.execute(
                f"""
                SELECT method_card_id, paper_id, task, problem_setting,
                       input_modalities, model_architecture, fusion_strategy,
                       training_objective, datasets, metrics, main_results,
                       limitations, reusable_ideas, implementation_difficulty,
                       risk, evidence_ids, created_at
                FROM lit_method_cards
                WHERE {where}
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (*params, limit),
            ).fetchall()

    def retrieve_evidence(
        self, scope: str, paper_ids: list[str], limit: int = 20
    ) -> list[dict[str, Any]]:
        placeholders = ",".join("?" for _ in paper_ids)
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT evidence_id, paper_id, claim_supported, quote, section, support_level, created_at
                FROM lit_evidence
                WHERE scope = ? AND paper_id IN ({placeholders})
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (scope, *paper_ids, limit),
            ).fetchall()
        return [
            {
                "evidence_id": r[0], "paper_id": r[1], "claim_supported": r[2],
                "quote": r[3], "section": r[4], "support_level": r[5],
                "created_at": r[6],
            }
            for r in rows
        ]

    def get_paper_ids_by_scope(self, scope: str) -> set[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT paper_id FROM lit_papers WHERE scope = ?", (scope,)
            ).fetchall()
        return {r[0] for r in rows}

    # -- experiment tree persistence ------------------------------------------

    def write_branch(self, branch: dict[str, Any], scope: str) -> None:
        """Upsert a branch and all its nodes. Removes nodes no longer present."""
        branch_id = branch.get("branch_id", "")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO lit_experiment_branches
                    (branch_id, scope, root_id, status, max_depth, max_active_nodes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    branch_id,
                    scope,
                    branch.get("root_id", ""),
                    branch.get("status", "active"),
                    branch.get("max_depth", 2),
                    branch.get("max_active_nodes", 3),
                    utc_now(),
                ),
            )
            # Remove old nodes so pruned nodes don't reappear on load
            conn.execute(
                "DELETE FROM lit_experiment_nodes WHERE branch_id = ?",
                (branch_id,),
            )
            for node in branch.get("nodes", []) or []:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO lit_experiment_nodes
                        (node_id, branch_id, scope, experiment_id, parent_id,
                         hypothesis, patch_scope, result_json, decision_json,
                         children_ids, status, depth, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        node.get("node_id", ""),
                        branch.get("branch_id", ""),
                        scope,
                        node.get("experiment_id", ""),
                        node.get("parent_id", ""),
                        node.get("hypothesis", ""),
                        node.get("patch_scope", ""),
                        json.dumps(node.get("result", {}), ensure_ascii=False),
                        json.dumps(node.get("decision", {}), ensure_ascii=False),
                        json.dumps(node.get("children_ids", []), ensure_ascii=False),
                        node.get("status", "pending"),
                        node.get("depth", 0),
                        node.get("created_at", utc_now()),
                    ),
                )

    def load_branch(self, scope: str) -> dict[str, Any] | None:
        """Load the most recent active branch (with all nodes) for a scope."""
        with self._connect() as conn:
            branch_row = conn.execute(
                """
                SELECT branch_id, root_id, status, max_depth, max_active_nodes, created_at
                FROM lit_experiment_branches
                WHERE scope = ? AND status = 'active'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (scope,),
            ).fetchone()

            if branch_row is None:
                return None

            node_rows = conn.execute(
                """
                SELECT node_id, experiment_id, parent_id, hypothesis, patch_scope,
                       result_json, decision_json, children_ids, status, depth, created_at
                FROM lit_experiment_nodes
                WHERE branch_id = ?
                ORDER BY created_at ASC
                """,
                (branch_row[0],),
            ).fetchall()

        return {
            "branch_id": branch_row[0],
            "root_id": branch_row[1],
            "status": branch_row[2],
            "max_depth": branch_row[3],
            "max_active_nodes": branch_row[4],
            "nodes": [
                {
                    "node_id": r[0],
                    "experiment_id": r[1],
                    "parent_id": r[2],
                    "hypothesis": r[3],
                    "patch_scope": r[4],
                    "result": json.loads(r[5]) if r[5] else {},
                    "decision": json.loads(r[6]) if r[6] else {},
                    "children_ids": json.loads(r[7]) if r[7] else [],
                    "status": r[8],
                    "depth": r[9],
                    "created_at": r[10],
                }
                for r in node_rows
            ],
        }

    def update_node(
        self, node_id: str, result: dict | None = None,
        decision: dict | None = None, status: str | None = None,
    ) -> None:
        """Update result, decision, and/or status on a single node."""
        with self._connect() as conn:
            if result is not None:
                conn.execute(
                    "UPDATE lit_experiment_nodes SET result_json = ? WHERE node_id = ?",
                    (json.dumps(result, ensure_ascii=False), node_id),
                )
            if decision is not None:
                conn.execute(
                    "UPDATE lit_experiment_nodes SET decision_json = ? WHERE node_id = ?",
                    (json.dumps(decision, ensure_ascii=False), node_id),
                )
            if status is not None:
                conn.execute(
                    "UPDATE lit_experiment_nodes SET status = ? WHERE node_id = ?",
                    (status, node_id),
                )

    # -- internal -------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.path))

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS lit_papers (
                    paper_id TEXT PRIMARY KEY,
                    scope TEXT NOT NULL,
                    title TEXT,
                    abstract TEXT,
                    authors TEXT,
                    year INTEGER,
                    keywords TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_lit_papers_scope ON lit_papers(scope);

                CREATE TABLE IF NOT EXISTS lit_chunks (
                    chunk_id TEXT PRIMARY KEY,
                    paper_id TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    text TEXT,
                    section TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_lit_chunks_paper ON lit_chunks(paper_id);

                CREATE TABLE IF NOT EXISTS lit_evidence (
                    evidence_id TEXT PRIMARY KEY,
                    paper_id TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    claim_supported TEXT,
                    quote TEXT,
                    section TEXT,
                    support_level TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_lit_evidence_paper ON lit_evidence(paper_id);

                CREATE TABLE IF NOT EXISTS lit_method_cards (
                    method_card_id TEXT PRIMARY KEY,
                    paper_id TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    task TEXT,
                    problem_setting TEXT,
                    input_modalities TEXT,
                    model_architecture TEXT,
                    fusion_strategy TEXT,
                    training_objective TEXT,
                    datasets TEXT,
                    metrics TEXT,
                    main_results TEXT,
                    limitations TEXT,
                    reusable_ideas TEXT,
                    implementation_difficulty TEXT,
                    risk TEXT,
                    evidence_ids TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_lit_mc_scope ON lit_method_cards(scope);
                CREATE INDEX IF NOT EXISTS idx_lit_mc_task ON lit_method_cards(task);
                CREATE INDEX IF NOT EXISTS idx_lit_mc_diff ON lit_method_cards(implementation_difficulty);

                CREATE TABLE IF NOT EXISTS lit_references (
                    ref_id TEXT PRIMARY KEY,
                    scope TEXT NOT NULL,
                    title TEXT NOT NULL,
                    source_paper_id TEXT,
                    authors TEXT,
                    year TEXT,
                    venue TEXT,
                    relevance_score REAL DEFAULT 0.0,
                    cited_in_sections TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_lit_ref_scope_score
                    ON lit_references(scope, relevance_score);
                CREATE INDEX IF NOT EXISTS idx_lit_ref_title
                    ON lit_references(title);

                CREATE TABLE IF NOT EXISTS lit_experiment_branches (
                    branch_id TEXT PRIMARY KEY,
                    scope TEXT NOT NULL,
                    root_id TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    max_depth INTEGER DEFAULT 2,
                    max_active_nodes INTEGER DEFAULT 3,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS lit_experiment_nodes (
                    node_id TEXT PRIMARY KEY,
                    branch_id TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    experiment_id TEXT,
                    parent_id TEXT,
                    hypothesis TEXT,
                    patch_scope TEXT,
                    result_json TEXT,
                    decision_json TEXT,
                    children_ids TEXT,
                    status TEXT DEFAULT 'pending',
                    depth INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_lit_ennode_branch ON lit_experiment_nodes(branch_id);
                CREATE INDEX IF NOT EXISTS idx_lit_ennode_scope_status ON lit_experiment_nodes(scope, status);
                """
            )


def _keyword_tokens(topic_keywords: list[str] | None) -> list[str]:
    if not topic_keywords:
        return []
    tokens: set[str] = set()
    for kw in topic_keywords[:8]:
        for token in kw.lower().split():
            token = token.strip(".,;:()[]{}\"'")
            if len(token) >= 3:
                tokens.add(token)
    return list(tokens)[:12]


def _normalize_task_patterns(task: str) -> list[str]:
    """Generate LIKE patterns for both underscore and space forms of a task name."""
    patterns = [task]
    if "_" in task:
        patterns.append(task.replace("_", " "))
    if " " in task:
        patterns.append(task.replace(" ", "_"))
    return list(set(patterns))
