"""
Tests für jarvis.core.message_queue – Durable Message Queue.

Testet:
  - Enqueue/Dequeue Reihenfolge (Priorität + FIFO)
  - Retry-Logik (fail → requeue → max retries → DLQ)
  - Cleanup entfernt abgelaufene Nachrichten
  - Stats-Reporting
  - Queue-Tiefe (max_size Limitierung)
  - Concurrent Access (mehrere enqueue/dequeue gleichzeitig)
  - Serialisierung verschiedener Nachrichtenformate
"""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING

import pytest

from cognithor.core.message_queue import (
    DurableMessageQueue,
    MessagePriority,
    QueuedMessage,
)

if TYPE_CHECKING:
    from pathlib import Path

    pass


@pytest.fixture
def queue_db(tmp_path: Path) -> Path:
    """Temporärer DB-Pfad für die Queue."""
    return tmp_path / "test_queue.db"


@pytest.fixture
def queue(queue_db: Path) -> DurableMessageQueue:
    """Frische DurableMessageQueue-Instanz."""
    q = DurableMessageQueue(queue_db, max_size=100, max_retries=3, ttl_hours=1)
    yield q
    q.close()


# ============================================================================
# Enqueue / Dequeue Basics
# ============================================================================


class TestEnqueueDequeue:
    """Grundlegende Enqueue/Dequeue-Operationen."""

    async def test_enqueue_returns_id(self, queue: DurableMessageQueue) -> None:
        msg_id = await queue.enqueue({"text": "Hello", "channel": "cli"})
        assert isinstance(msg_id, str)
        assert len(msg_id) == 32  # UUID hex

    async def test_dequeue_empty_returns_none(self, queue: DurableMessageQueue) -> None:
        result = await queue.dequeue()
        assert result is None

    async def test_enqueue_dequeue_roundtrip(self, queue: DurableMessageQueue) -> None:
        msg = {"text": "Hallo Welt", "channel": "telegram", "user_id": "alex"}
        msg_id = await queue.enqueue(msg)

        queued = await queue.dequeue()
        assert queued is not None
        assert queued.id == msg_id
        assert queued.status == "processing"
        assert queued.retry_count == 0

        data = queued.message_data
        assert data["text"] == "Hallo Welt"
        assert data["channel"] == "telegram"

    async def test_dequeue_sets_processing_status(self, queue: DurableMessageQueue) -> None:
        await queue.enqueue({"text": "test"})
        queued = await queue.dequeue()
        assert queued is not None
        assert queued.status == "processing"

        # Zweites Dequeue sollte None sein (kein pending mehr)
        second = await queue.dequeue()
        assert second is None

    async def test_fifo_within_same_priority(self, queue: DurableMessageQueue) -> None:
        """Bei gleicher Priorität: First In, First Out."""
        id1 = await queue.enqueue({"text": "first"}, priority=MessagePriority.NORMAL)
        id2 = await queue.enqueue({"text": "second"}, priority=MessagePriority.NORMAL)
        id3 = await queue.enqueue({"text": "third"}, priority=MessagePriority.NORMAL)

        msg1 = await queue.dequeue()
        msg2 = await queue.dequeue()
        msg3 = await queue.dequeue()

        assert msg1 is not None and msg1.id == id1
        assert msg2 is not None and msg2.id == id2
        assert msg3 is not None and msg3.id == id3


# ============================================================================
# Priorität
# ============================================================================


class TestPriority:
    """Prioritätsbasiertes Dequeuing."""

    async def test_higher_priority_first(self, queue: DurableMessageQueue) -> None:
        """Höhere Priorität wird zuerst verarbeitet."""
        id_low = await queue.enqueue({"text": "low"}, priority=MessagePriority.LOW)
        id_high = await queue.enqueue({"text": "high"}, priority=MessagePriority.HIGH)
        id_normal = await queue.enqueue({"text": "normal"}, priority=MessagePriority.NORMAL)

        msg1 = await queue.dequeue()
        msg2 = await queue.dequeue()
        msg3 = await queue.dequeue()

        assert msg1 is not None and msg1.id == id_high
        assert msg2 is not None and msg2.id == id_normal
        assert msg3 is not None and msg3.id == id_low

    async def test_critical_priority_always_first(self, queue: DurableMessageQueue) -> None:
        """CRITICAL hat immer Vorrang."""
        await queue.enqueue({"text": "normal"}, priority=MessagePriority.NORMAL)
        id_crit = await queue.enqueue({"text": "critical"}, priority=MessagePriority.CRITICAL)
        await queue.enqueue({"text": "high"}, priority=MessagePriority.HIGH)

        msg = await queue.dequeue()
        assert msg is not None and msg.id == id_crit

    async def test_mixed_priority_and_fifo(self, queue: DurableMessageQueue) -> None:
        """Bei gleicher Priorität gilt FIFO, verschiedene Prioritäten nach Rang."""
        id_n1 = await queue.enqueue({"text": "normal-1"}, priority=MessagePriority.NORMAL)
        id_h1 = await queue.enqueue({"text": "high-1"}, priority=MessagePriority.HIGH)
        id_n2 = await queue.enqueue({"text": "normal-2"}, priority=MessagePriority.NORMAL)
        id_h2 = await queue.enqueue({"text": "high-2"}, priority=MessagePriority.HIGH)

        results = []
        for _ in range(4):
            m = await queue.dequeue()
            assert m is not None
            results.append(m.id)

        # HIGH zuerst (FIFO innerhalb), dann NORMAL (FIFO innerhalb)
        assert results == [id_h1, id_h2, id_n1, id_n2]


# ============================================================================
# Complete / Fail / Retry / DLQ
# ============================================================================


class TestRetryAndDLQ:
    """Retry-Logik und Dead-Letter-Queue."""

    async def test_complete_marks_message(self, queue: DurableMessageQueue) -> None:
        msg_id = await queue.enqueue({"text": "test"})
        queued = await queue.dequeue()
        assert queued is not None

        await queue.complete(msg_id)

        stats = await queue.get_stats()
        assert stats["completed"] == 1
        assert stats["pending"] == 0

    async def test_fail_requeues_with_retries_remaining(self, queue: DurableMessageQueue) -> None:
        """Fehler mit verbleibenden Retries: zurück in die Queue."""
        msg_id = await queue.enqueue({"text": "flaky"})
        await queue.dequeue()

        # Erstes Fail → retry_count=1, zurück zu pending (max_retries=3)
        await queue.fail(msg_id, "Connection timeout")

        stats = await queue.get_stats()
        assert stats["pending"] == 1
        assert stats["dead"] == 0

        # Nachricht erneut dequeuen
        retried = await queue.dequeue()
        assert retried is not None
        assert retried.id == msg_id
        assert retried.retry_count == 1
        assert retried.error_message == "Connection timeout"

    async def test_fail_exhausts_retries_to_dlq(self, queue: DurableMessageQueue) -> None:
        """Nach max_retries: Nachricht in DLQ (status='dead')."""
        msg_id = await queue.enqueue({"text": "doomed"})

        for i in range(3):
            queued = await queue.dequeue()
            assert queued is not None
            await queue.fail(msg_id, f"Error #{i + 1}")

        stats = await queue.get_stats()
        assert stats["dead"] == 1
        assert stats["pending"] == 0

    async def test_get_dead_letters(self, queue: DurableMessageQueue) -> None:
        """Dead-Letter-Abfrage liefert die toten Nachrichten."""
        msg_id = await queue.enqueue({"text": "dead-msg"})

        # 3 Fails = DLQ
        for _ in range(3):
            await queue.dequeue()
            await queue.fail(msg_id, "fatal error")

        dead = await queue.get_dead_letters()
        assert len(dead) == 1
        assert dead[0].id == msg_id
        assert dead[0].status == "dead"
        assert dead[0].error_message == "fatal error"
        assert dead[0].retry_count == 3

    async def test_fail_nonexistent_id_is_safe(self, queue: DurableMessageQueue) -> None:
        """Fail auf eine nicht existierende ID verursacht keinen Fehler."""
        await queue.fail("nonexistent_id_12345", "some error")
        # Kein Error erwartet

    async def test_retry_count_increments(self, queue: DurableMessageQueue) -> None:
        """Retry-Zähler wird korrekt hochgezählt."""
        queue_with_5 = DurableMessageQueue(queue._db_path.parent / "retry5.db", max_retries=5)
        try:
            msg_id = await queue_with_5.enqueue({"text": "retry-test"})

            for expected_retry in range(5):
                queued = await queue_with_5.dequeue()
                assert queued is not None
                assert queued.retry_count == expected_retry
                await queue_with_5.fail(msg_id, f"Error {expected_retry}")

            # Nach 5 Fails: DLQ
            stats = await queue_with_5.get_stats()
            assert stats["dead"] == 1
        finally:
            queue_with_5.close()


# ============================================================================
# Cleanup
# ============================================================================


class TestCleanup:
    """Cleanup-Funktionalität."""

    async def test_cleanup_removes_completed(self, queue: DurableMessageQueue) -> None:
        """Cleanup entfernt abgeschlossene Nachrichten."""
        msg_id = await queue.enqueue({"text": "done"})
        await queue.dequeue()
        await queue.complete(msg_id)

        removed = await queue.cleanup()
        assert removed == 1

        stats = await queue.get_stats()
        assert stats["total"] == 0

    async def test_cleanup_preserves_pending(self, queue: DurableMessageQueue) -> None:
        """Cleanup lässt ausstehende Nachrichten unberührt."""
        await queue.enqueue({"text": "still waiting"})

        removed = await queue.cleanup()
        assert removed == 0

        depth = await queue.get_depth()
        assert depth == 1

    async def test_cleanup_removes_expired_dead(self, tmp_path: Path) -> None:
        """Cleanup entfernt abgelaufene Dead-Letter-Nachrichten."""
        # Queue mit sehr kurzer TTL
        q = DurableMessageQueue(tmp_path / "ttl.db", max_retries=1, ttl_hours=0)
        try:
            msg_id = await q.enqueue({"text": "expired"})
            await q.dequeue()
            await q.fail(msg_id, "error")

            # Da ttl_hours=0 ist alles sofort "abgelaufen"
            # Wir müssen das created_at manuell in die Vergangenheit setzen
            import time

            past = time.time() - 3600  # 1 Stunde zurück
            q.conn.execute(
                "UPDATE message_queue SET created_at = ? WHERE id = ?",
                (past, msg_id),
            )
            q.conn.commit()

            removed = await q.cleanup()
            assert removed >= 1
        finally:
            q.close()


# ============================================================================
# Stats & Depth
# ============================================================================


class TestStatsAndDepth:
    """Stats-Reporting und Queue-Tiefe."""

    async def test_depth_empty(self, queue: DurableMessageQueue) -> None:
        depth = await queue.get_depth()
        assert depth == 0

    async def test_depth_counts_pending_only(self, queue: DurableMessageQueue) -> None:
        await queue.enqueue({"text": "a"})
        await queue.enqueue({"text": "b"})
        await queue.enqueue({"text": "c"})

        assert await queue.get_depth() == 3

        # Eins dequeuen (→ processing)
        await queue.dequeue()
        assert await queue.get_depth() == 2

    async def test_stats_all_statuses(self, queue: DurableMessageQueue) -> None:
        """Stats zeigen alle Status korrekt."""
        # 1 completed: enqueue, dequeue, complete
        id_comp = await queue.enqueue({"text": "completed"})
        await queue.dequeue()
        await queue.complete(id_comp)

        # 1 dead (3 fails): enqueue then exhaust retries
        id_dead = await queue.enqueue({"text": "dead"})
        for _ in range(3):
            await queue.dequeue()
            await queue.fail(id_dead, "error")

        # 1 processing: enqueue then dequeue (stays processing)
        await queue.enqueue({"text": "processing"})
        await queue.dequeue()

        # 1 pending: enqueue (stays pending)
        await queue.enqueue({"text": "pending"})

        stats = await queue.get_stats()
        assert stats["pending"] == 1
        assert stats["processing"] == 1
        assert stats["completed"] == 1
        assert stats["dead"] == 1
        assert stats["total"] == 4

    async def test_stats_empty_queue(self, queue: DurableMessageQueue) -> None:
        stats = await queue.get_stats()
        assert stats["pending"] == 0
        assert stats["processing"] == 0
        assert stats["total"] == 0


# ============================================================================
# Queue-Größenlimit
# ============================================================================


class TestQueueSizeLimit:
    """Queue-Größe wird begrenzt."""

    async def test_max_size_raises_when_full(self, tmp_path: Path) -> None:
        """Queue wirft RuntimeError wenn max_size erreicht."""
        small_queue = DurableMessageQueue(tmp_path / "small.db", max_size=3)
        try:
            await small_queue.enqueue({"text": "1"})
            await small_queue.enqueue({"text": "2"})
            await small_queue.enqueue({"text": "3"})

            with pytest.raises(RuntimeError, match="Queue voll"):
                await small_queue.enqueue({"text": "4"})
        finally:
            small_queue.close()

    async def test_dequeue_frees_slot(self, tmp_path: Path) -> None:
        """Nach Dequeue + Complete wird Platz für neue Nachrichten frei."""
        small_queue = DurableMessageQueue(tmp_path / "small2.db", max_size=2)
        try:
            id1 = await small_queue.enqueue({"text": "1"})
            await small_queue.enqueue({"text": "2"})

            # Queue ist voll
            with pytest.raises(RuntimeError):
                await small_queue.enqueue({"text": "3"})

            # Eins abarbeiten
            await small_queue.dequeue()
            await small_queue.complete(id1)

            # Jetzt ist Platz (processing zählt noch mit!)
            # Wir müssen das completed entfernen damit der Zähler sinkt
            await small_queue.cleanup()
            await small_queue.enqueue({"text": "3"})

            depth = await small_queue.get_depth()
            assert depth == 2  # "2" (pending) + "3" (pending)
        finally:
            small_queue.close()


# ============================================================================
# Concurrent Access
# ============================================================================


class TestConcurrentAccess:
    """Gleichzeitiger Zugriff auf die Queue."""

    async def test_concurrent_enqueue(self, queue: DurableMessageQueue) -> None:
        """Mehrere gleichzeitige Enqueue-Aufrufe sind sicher."""
        tasks = [queue.enqueue({"text": f"msg-{i}"}) for i in range(20)]
        ids = await asyncio.gather(*tasks)

        assert len(ids) == 20
        assert len(set(ids)) == 20  # Alle IDs sind einzigartig

        depth = await queue.get_depth()
        assert depth == 20

    async def test_concurrent_dequeue_no_duplicates(self, queue: DurableMessageQueue) -> None:
        """Gleichzeitige Dequeues liefern nie die gleiche Nachricht."""
        # 10 Nachrichten einfügen
        for i in range(10):
            await queue.enqueue({"text": f"msg-{i}"})

        # 10 gleichzeitige Dequeues
        tasks = [queue.dequeue() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # Einige können None sein (Race Condition), aber keine Duplikate
        received_ids = [r.id for r in results if r is not None]
        assert len(received_ids) == len(set(received_ids))

    async def test_concurrent_enqueue_dequeue(self, queue: DurableMessageQueue) -> None:
        """Gleichzeitiges Enqueue und Dequeue ist sicher."""

        async def producer(n: int) -> list[str]:
            ids = []
            for i in range(n):
                mid = await queue.enqueue({"text": f"produced-{i}"})
                ids.append(mid)
            return ids

        async def consumer(n: int) -> list[str]:
            ids = []
            for _ in range(n):
                msg = await queue.dequeue()
                if msg:
                    ids.append(msg.id)
                    await queue.complete(msg.id)
            return ids

        # Produzent und Konsument parallel laufen lassen
        produced, consumed = await asyncio.gather(producer(10), consumer(5))

        # Alle produzierten IDs sollten einzigartig sein
        assert len(set(produced)) == 10


# ============================================================================
# Serialisierung
# ============================================================================


class TestSerialization:
    """Verschiedene Nachrichtenformate serialisieren."""

    async def test_dict_message(self, queue: DurableMessageQueue) -> None:
        await queue.enqueue({"key": "value", "number": 42})
        msg = await queue.dequeue()
        assert msg is not None
        data = msg.message_data
        assert data["key"] == "value"
        assert data["number"] == 42

    async def test_string_message(self, queue: DurableMessageQueue) -> None:
        raw_json = json.dumps({"text": "raw json string"})
        await queue.enqueue(raw_json)
        msg = await queue.dequeue()
        assert msg is not None
        data = msg.message_data
        assert data["text"] == "raw json string"

    async def test_pydantic_model_message(self, queue: DurableMessageQueue) -> None:
        """Pydantic-Modelle (IncomingMessage) werden korrekt serialisiert."""
        from cognithor.models import IncomingMessage

        incoming = IncomingMessage(
            channel="telegram",
            user_id="user123",
            text="Wie wird das Wetter?",
        )
        msg_id = await queue.enqueue(incoming)

        queued = await queue.dequeue()
        assert queued is not None
        assert queued.id == msg_id

        data = queued.message_data
        assert data["channel"] == "telegram"
        assert data["user_id"] == "user123"
        assert data["text"] == "Wie wird das Wetter?"


# ============================================================================
# Edge Cases
# ============================================================================


class TestEdgeCases:
    """Randfälle und Robustheit."""

    async def test_close_and_reopen(self, queue_db: Path) -> None:
        """Queue überlebt close/reopen (Durability)."""
        q1 = DurableMessageQueue(queue_db)
        msg_id = await q1.enqueue({"text": "persistent"})
        q1.close()

        # Neue Instanz auf gleicher DB
        q2 = DurableMessageQueue(queue_db)
        try:
            msg = await q2.dequeue()
            assert msg is not None
            assert msg.id == msg_id
            assert msg.message_data["text"] == "persistent"
        finally:
            q2.close()

    async def test_double_close_is_safe(self, queue: DurableMessageQueue) -> None:
        queue.close()
        queue.close()  # Kein Error

    async def test_complete_already_completed(self, queue: DurableMessageQueue) -> None:
        """Doppeltes Complete verursacht keinen Fehler."""
        msg_id = await queue.enqueue({"text": "test"})
        await queue.dequeue()
        await queue.complete(msg_id)
        await queue.complete(msg_id)  # Idempotent

    async def test_message_priority_enum_values(self) -> None:
        """MessagePriority-Werte stimmen."""
        assert MessagePriority.LOW == 1
        assert MessagePriority.NORMAL == 5
        assert MessagePriority.HIGH == 8
        assert MessagePriority.CRITICAL == 10

    async def test_queued_message_data_property(self) -> None:
        """QueuedMessage.message_data deserialisiert korrekt."""
        from datetime import UTC, datetime

        qm = QueuedMessage(
            id="test",
            message_json='{"foo": "bar"}',
            priority=5,
            status="pending",
            retry_count=0,
            max_retries=3,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        assert qm.message_data == {"foo": "bar"}
