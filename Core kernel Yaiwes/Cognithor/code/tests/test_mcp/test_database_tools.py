"""Tests fuer Database-Tools -- db_query, db_schema, db_execute, db_connect.

Testet:
  - TestRegistration: 4 Tools registriert
  - TestSQLiteReadOnly: query_only Pragma wird gesetzt
  - TestParameterizedQueries: Parameterisierung funktioniert
  - TestSchemaExtraction: Tabellen und Spalten werden korrekt gelesen
  - TestPathValidation: Pfade ausserhalb erlaubter Verzeichnisse blockiert
  - TestInjectionProtection: Offensichtliche Injection-Patterns erkannt
  - TestDbConnect: Verbindungsinfo wird korrekt zurueckgegeben
  - TestDbExecute: Schreiboperationen funktionieren
"""

from __future__ import annotations

import sqlite3
from sqlite3 import OperationalError
from typing import TYPE_CHECKING

import pytest

from cognithor.config import CognithorConfig, SecurityConfig, ensure_directory_structure
from cognithor.mcp.database_tools import (
    DatabaseError,
    DatabaseTools,
    _check_injection,
    _format_table,
    register_database_tools,
)

if TYPE_CHECKING:
    from pathlib import Path


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture()
def config(tmp_path: Path) -> CognithorConfig:
    cfg = CognithorConfig(
        cognithor_home=tmp_path / ".cognithor",
        security=SecurityConfig(allowed_paths=[str(tmp_path)]),
    )
    ensure_directory_structure(cfg)
    return cfg


@pytest.fixture()
def db_tools(config: CognithorConfig) -> DatabaseTools:
    return DatabaseTools(config)


@pytest.fixture()
def sample_db(tmp_path: Path) -> Path:
    """Create a sample SQLite database with test data."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL, age INTEGER, email TEXT)"
    )
    conn.execute("INSERT INTO users (name, age, email) VALUES ('Alice', 30, 'alice@example.com')")
    conn.execute("INSERT INTO users (name, age, email) VALUES ('Bob', 25, 'bob@example.com')")
    conn.execute(
        "INSERT INTO users (name, age, email) VALUES ('Charlie', 35, 'charlie@example.com')"
    )
    conn.execute(
        "CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER, product TEXT, amount REAL)"
    )
    conn.execute("INSERT INTO orders (user_id, product, amount) VALUES (1, 'Widget', 9.99)")
    conn.execute("INSERT INTO orders (user_id, product, amount) VALUES (2, 'Gadget', 19.99)")
    conn.commit()
    conn.close()
    return db_path


# =============================================================================
# Mock MCP Client
# =============================================================================


class MockMCPClient:
    def __init__(self) -> None:
        self.registered: dict[str, dict] = {}

    def register_builtin_handler(
        self,
        name: str,
        handler: object,
        *,
        description: str = "",
        input_schema: dict | None = None,
    ) -> None:
        self.registered[name] = {
            "handler": handler,
            "description": description,
            "input_schema": input_schema,
        }


# =============================================================================
# TestRegistration
# =============================================================================


class TestRegistration:
    def test_all_tools_registered(self, config: CognithorConfig) -> None:
        client = MockMCPClient()
        tools = register_database_tools(client, config)

        assert tools is not None
        expected = {"db_query", "db_schema", "db_execute", "db_connect"}
        assert set(client.registered.keys()) == expected

    def test_handlers_are_callable(self, config: CognithorConfig) -> None:
        client = MockMCPClient()
        register_database_tools(client, config)

        for name, entry in client.registered.items():
            assert callable(entry["handler"]), f"Handler fuer '{name}' nicht aufrufbar"

    def test_descriptions_non_empty(self, config: CognithorConfig) -> None:
        client = MockMCPClient()
        register_database_tools(client, config)

        for name, entry in client.registered.items():
            assert entry["description"], f"Description fuer '{name}' ist leer"

    def test_schemas_present(self, config: CognithorConfig) -> None:
        client = MockMCPClient()
        register_database_tools(client, config)

        for name, entry in client.registered.items():
            assert entry["input_schema"] is not None, f"Schema fuer '{name}' fehlt"
            assert entry["input_schema"]["type"] == "object"


# =============================================================================
# TestSQLiteReadOnly
# =============================================================================


class TestSQLiteReadOnly:
    @pytest.mark.asyncio()
    async def test_select_works(self, db_tools: DatabaseTools, sample_db: Path) -> None:
        result = await db_tools.db_query(str(sample_db), "SELECT * FROM users")
        assert "Alice" in result
        assert "Bob" in result
        assert "Charlie" in result

    @pytest.mark.asyncio()
    async def test_readonly_blocks_insert(self, db_tools: DatabaseTools, sample_db: Path) -> None:
        with pytest.raises((DatabaseError, OperationalError)):
            await db_tools.db_query(
                str(sample_db),
                "INSERT INTO users (name, age) VALUES ('Eve', 28)",
            )

    @pytest.mark.asyncio()
    async def test_readonly_blocks_delete(self, db_tools: DatabaseTools, sample_db: Path) -> None:
        with pytest.raises((DatabaseError, OperationalError)):
            await db_tools.db_query(
                str(sample_db),
                "DELETE FROM users WHERE name='Alice'",
            )

    @pytest.mark.asyncio()
    async def test_empty_sql_returns_error(self, db_tools: DatabaseTools, sample_db: Path) -> None:
        result = await db_tools.db_query(str(sample_db), "")
        assert "Fehler" in result or "error" in result.lower()

    @pytest.mark.asyncio()
    async def test_limit_parameter(self, db_tools: DatabaseTools, sample_db: Path) -> None:
        result = await db_tools.db_query(str(sample_db), "SELECT * FROM users", limit=1)
        assert "1 row" in result


# =============================================================================
# TestParameterizedQueries
# =============================================================================


class TestParameterizedQueries:
    @pytest.mark.asyncio()
    async def test_parameterized_select(self, db_tools: DatabaseTools, sample_db: Path) -> None:
        result = await db_tools.db_query(
            str(sample_db),
            "SELECT name, age FROM users WHERE age > ?",
            params=[28],
        )
        assert "Alice" in result
        assert "Charlie" in result
        # Bob is 25, should not appear
        assert "Bob" not in result

    @pytest.mark.asyncio()
    async def test_parameterized_string(self, db_tools: DatabaseTools, sample_db: Path) -> None:
        result = await db_tools.db_query(
            str(sample_db),
            "SELECT * FROM users WHERE name = ?",
            params=["Alice"],
        )
        assert "Alice" in result
        assert "Bob" not in result


# =============================================================================
# TestSchemaExtraction
# =============================================================================


class TestSchemaExtraction:
    @pytest.mark.asyncio()
    async def test_list_tables(self, db_tools: DatabaseTools, sample_db: Path) -> None:
        result = await db_tools.db_schema(str(sample_db))
        assert "users" in result
        assert "orders" in result

    @pytest.mark.asyncio()
    async def test_table_columns(self, db_tools: DatabaseTools, sample_db: Path) -> None:
        result = await db_tools.db_schema(str(sample_db), table="users")
        assert "name" in result
        assert "age" in result
        assert "email" in result
        assert "id" in result

    @pytest.mark.asyncio()
    async def test_nonexistent_table(self, db_tools: DatabaseTools, sample_db: Path) -> None:
        with pytest.raises(DatabaseError, match="Tabelle nicht gefunden"):
            await db_tools.db_schema(str(sample_db), table="nonexistent")


# =============================================================================
# TestPathValidation
# =============================================================================


class TestPathValidation:
    @pytest.mark.asyncio()
    async def test_outside_workspace_blocked(self, db_tools: DatabaseTools) -> None:
        with pytest.raises(DatabaseError, match="Zugriff verweigert"):
            await db_tools.db_query("/etc/passwd", "SELECT 1")

    @pytest.mark.asyncio()
    async def test_nonexistent_db_blocked(self, db_tools: DatabaseTools, tmp_path: Path) -> None:
        with pytest.raises(DatabaseError, match="nicht gefunden"):
            await db_tools.db_query(str(tmp_path / "nonexistent.db"), "SELECT 1")

    @pytest.mark.asyncio()
    async def test_path_traversal_blocked(self, db_tools: DatabaseTools, tmp_path: Path) -> None:
        with pytest.raises(DatabaseError, match="Zugriff verweigert"):
            await db_tools.db_query(
                str(tmp_path / ".." / ".." / "etc" / "passwd"),
                "SELECT 1",
            )


# =============================================================================
# TestInjectionProtection
# =============================================================================


class TestInjectionProtection:
    def test_drop_detected(self) -> None:
        with pytest.raises(DatabaseError, match="injection"):
            _check_injection("SELECT 1; DROP TABLE users", None)

    def test_union_select_detected(self) -> None:
        with pytest.raises(DatabaseError, match="injection"):
            _check_injection("SELECT * FROM users UNION SELECT * FROM secrets", None)

    def test_parameterized_ok(self) -> None:
        # Should NOT raise when params are provided
        _check_injection("SELECT * FROM users WHERE id = ?", [1])

    def test_normal_select_ok(self) -> None:
        # Should NOT raise for normal queries
        _check_injection("SELECT * FROM users WHERE name = 'test'", None)

    @pytest.mark.asyncio()
    async def test_drop_blocked_in_execute(self, db_tools: DatabaseTools, sample_db: Path) -> None:
        with pytest.raises(DatabaseError, match="DROP"):
            await db_tools.db_execute(str(sample_db), "DROP TABLE users")


# =============================================================================
# TestDbConnect
# =============================================================================


class TestDbConnect:
    @pytest.mark.asyncio()
    async def test_sqlite_connect_info(self, db_tools: DatabaseTools, sample_db: Path) -> None:
        result = await db_tools.db_connect(str(sample_db))
        assert "SQLite" in result
        assert "Tabellen:" in result
        assert "erfolgreich" in result.lower() or "Erfolgreich" in result

    @pytest.mark.asyncio()
    async def test_nonexistent_db(self, db_tools: DatabaseTools, tmp_path: Path) -> None:
        with pytest.raises(DatabaseError, match="nicht gefunden"):
            await db_tools.db_connect(str(tmp_path / "nonexistent.db"))


# =============================================================================
# TestDbExecute
# =============================================================================


class TestDbExecute:
    @pytest.mark.asyncio()
    async def test_insert(self, db_tools: DatabaseTools, sample_db: Path) -> None:
        result = await db_tools.db_execute(
            str(sample_db),
            "INSERT INTO users (name, age, email) VALUES (?, ?, ?)",
            params=["Dave", 40, "dave@example.com"],
        )
        assert "Erfolgreich" in result
        assert "1 Zeile" in result

    @pytest.mark.asyncio()
    async def test_update(self, db_tools: DatabaseTools, sample_db: Path) -> None:
        result = await db_tools.db_execute(
            str(sample_db),
            "UPDATE users SET age = ? WHERE name = ?",
            params=[31, "Alice"],
        )
        assert "Erfolgreich" in result

    @pytest.mark.asyncio()
    async def test_empty_sql(self, db_tools: DatabaseTools, sample_db: Path) -> None:
        result = await db_tools.db_execute(str(sample_db), "")
        assert "Fehler" in result or "error" in result.lower()


# =============================================================================
# TestFormatTable
# =============================================================================


class TestFormatTable:
    def test_basic_table(self) -> None:
        columns = ["name", "age"]
        rows = [("Alice", 30), ("Bob", 25)]
        result = _format_table(columns, rows, 2)
        assert "Alice" in result
        assert "Bob" in result
        assert "name" in result
        assert "2 rows" in result

    def test_single_row(self) -> None:
        columns = ["id"]
        rows = [(1,)]
        result = _format_table(columns, rows, 1)
        assert "1 row)" in result

    def test_no_columns(self) -> None:
        result = _format_table([], [], 5)
        assert "5 rows affected" in result

    def test_truncation(self) -> None:
        columns = ["data"]
        long_value = "x" * 300
        rows = [(long_value,)]
        result = _format_table(columns, rows, 1)
        assert "..." in result
        # The full 300-char value should NOT appear
        assert long_value not in result
