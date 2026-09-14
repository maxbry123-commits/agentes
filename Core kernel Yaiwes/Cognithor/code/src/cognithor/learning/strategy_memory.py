"""StrategyMemory — verfolgt task_type → strategy → success_rate fuer Meta-Reasoning.

Speichert Strategien pro Aufgabentyp und berechnet Erfolgsraten,
damit der Planner bevorzugte Strategien erhaelt.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from cognithor.security.encrypted_db import encrypted_connect
from cognithor.utils.logging import get_logger

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Tool-Type Mapping
# ---------------------------------------------------------------------------

_TOOL_TYPE_MAP: dict[str, set[str]] = {
    "web_research": {
        "web_search",
        "search_and_read",
        "fetch_url",
        "scrape_page",
        "duckduckgo_search",
    },
    "code_execution": {
        "run_python",
        "run_shell",
        "execute_code",
        "python_eval",
        "code_analysis",
    },
    "knowledge_management": {
        "memory_store",
        "memory_recall",
        "memory_search",
        "vault_store",
        "vault_recall",
        "knowledge_ingest",
    },
    "document_creation": {
        "document_export",
        "create_pdf",
        "create_docx",
        "markdown_render",
        "write_document",
    },
    "file_operations": {
        "read_file",
        "write_file",
        "list_directory",
        "file_search",
        "move_file",
        "copy_file",
        "delete_file",
    },
    "system_command": {
        "shell_exec",
        "run_command",
        "process_list",
        "system_info",
        "kill_process",
    },
    "browser_automation": {
        "browser_open",
        "browser_click",
        "browser_type",
        "browser_screenshot",
        "browser_navigate",
    },
    "communication": {
        "send_message",
        "send_telegram",
        "send_discord",
        "send_slack",
        "send_email",
    },
}


def classify_task_type(tools_used: list[str]) -> str:
    """Klassifiziert eine Tool-Liste in einen Aufgabentyp.

    Zaehlt die Ueberlappung mit ``_TOOL_TYPE_MAP`` und gibt den Typ
    mit den meisten Treffern zurueck.  Ohne Treffer wird ``"general"``
    zurueckgegeben.
    """
    if not tools_used:
        return "general"

    tool_set = set(tools_used)
    best_type = "general"
    best_count = 0

    for task_type, type_tools in _TOOL_TYPE_MAP.items():
        overlap = len(tool_set & type_tools)
        if overlap > best_count:
            best_count = overlap
            best_type = task_type

    return best_type


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class StrategyRecord:
    """Einzelner Strategie-Eintrag zum Speichern."""

    task_type: str
    strategy: str
    success: bool
    duration_ms: float
    tool_count: int


@dataclass
class StrategyStats:
    """Aggregierte Statistik fuer eine Strategie."""

    task_type: str
    strategy: str
    success_rate: float
    total_uses: int
    avg_duration_ms: float


# ---------------------------------------------------------------------------
# StrategyMemory
# ---------------------------------------------------------------------------


class StrategyMemory:
    """Persistente Strategie-Datenbank fuer Meta-Reasoning."""

    def __init__(self, db_path: str) -> None:
        self._conn = encrypted_connect(db_path, check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS strategies (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                task_type   TEXT    NOT NULL,
                strategy    TEXT    NOT NULL,
                success     INTEGER NOT NULL,
                duration_ms REAL    NOT NULL,
                tool_count  INTEGER NOT NULL,
                created_at  REAL    NOT NULL
            )
            """
        )
        self._conn.commit()
        log.debug("StrategyMemory initialisiert: %s", db_path)

    # -- write ---------------------------------------------------------------

    def record(self, rec: StrategyRecord) -> None:
        """Speichert einen Strategie-Datensatz."""
        self._conn.execute(
            """
            INSERT INTO strategies
                (task_type, strategy, success, duration_ms, tool_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                rec.task_type,
                rec.strategy,
                int(rec.success),
                rec.duration_ms,
                rec.tool_count,
                time.time(),
            ),
        )
        self._conn.commit()

    # -- read ----------------------------------------------------------------

    def best_strategy(
        self,
        task_type: str,
        min_uses: int = 1,
    ) -> StrategyStats | None:
        """Gibt die beste Strategie fuer einen Aufgabentyp zurueck.

        Sortiert nach Erfolgsrate (absteigend), dann durchschnittliche
        Dauer (aufsteigend).  Gibt ``None`` zurueck wenn keine Daten
        mit mindestens *min_uses* vorliegen.
        """
        cur = self._conn.execute(
            """
            SELECT
                task_type,
                strategy,
                AVG(success)     AS success_rate,
                COUNT(*)         AS total_uses,
                AVG(duration_ms) AS avg_duration_ms
            FROM strategies
            WHERE task_type = ?
            GROUP BY strategy
            HAVING COUNT(*) >= ?
            ORDER BY success_rate DESC, avg_duration_ms ASC
            LIMIT 1
            """,
            (task_type, min_uses),
        )
        row = cur.fetchone()
        if row is None:
            return None

        # row_factory kann dict oder tuple liefern
        if isinstance(row, dict):
            return StrategyStats(
                task_type=row["task_type"],
                strategy=row["strategy"],
                success_rate=float(row["success_rate"]),
                total_uses=int(row["total_uses"]),
                avg_duration_ms=float(row["avg_duration_ms"]),
            )
        return StrategyStats(
            task_type=row[0],
            strategy=row[1],
            success_rate=float(row[2]),
            total_uses=int(row[3]),
            avg_duration_ms=float(row[4]),
        )

    def get_strategy_hint(self, task_type: str) -> str:
        """Erzeugt einen menschenlesbaren Hinweis fuer den Planner.

        Gibt einen leeren String zurueck wenn keine ausreichenden Daten
        (min_uses=2) vorhanden sind.
        """
        stats = self.best_strategy(task_type, min_uses=2)
        if stats is None:
            return ""
        pct = round(stats.success_rate * 100)
        return (
            f"Bevorzugte Strategie fuer {stats.task_type}: "
            f'"{stats.strategy}" '
            f"(Erfolgsrate {pct}%, {stats.total_uses} Versuche, "
            f"~{round(stats.avg_duration_ms)}ms)"
        )

    # -- lifecycle -----------------------------------------------------------

    def close(self) -> None:
        """Schliesst die Datenbankverbindung."""
        self._conn.close()
