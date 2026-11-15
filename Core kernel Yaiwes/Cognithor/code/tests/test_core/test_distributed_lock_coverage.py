"""Coverage-Tests fuer distributed_lock.py."""

from __future__ import annotations

import pytest

from cognithor.core.distributed_lock import (
    DistributedLock,
    FileLockBackend,
    LocalLockBackend,
    LockBackend,
    RedisLockBackend,
    create_lock,
)

# ============================================================================
# LockBackend Enum
# ============================================================================


class TestLockBackendEnum:
    def test_values(self) -> None:
        assert LockBackend.LOCAL == "local"
        assert LockBackend.FILE == "file"
        assert LockBackend.REDIS == "redis"


# ============================================================================
# LocalLockBackend
# ============================================================================


class TestLocalLockBackend:
    @pytest.mark.asyncio
    async def test_acquire_and_release(self) -> None:
        lock = LocalLockBackend()
        acquired = await lock.acquire("test_lock")
        assert acquired is True
        await lock.release("test_lock")

    @pytest.mark.asyncio
    async def test_acquire_same_lock_twice_fails_with_timeout(self) -> None:
        lock = LocalLockBackend()
        await lock.acquire("busy")
        # Second acquire should timeout
        acquired = await lock.acquire("busy", timeout=0.1)
        assert acquired is False
        await lock.release("busy")

    @pytest.mark.asyncio
    async def test_release_unknown_lock(self) -> None:
        lock = LocalLockBackend()
        # Should not raise
        await lock.release("nonexistent")

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        lock = LocalLockBackend()
        async with lock("my_lock"):
            pass  # Critical section

    @pytest.mark.asyncio
    async def test_context_manager_timeout(self) -> None:
        lock = LocalLockBackend()
        await lock.acquire("taken")
        with pytest.raises(TimeoutError):
            async with lock("taken", timeout=0.1):
                pass
        await lock.release("taken")

    @pytest.mark.asyncio
    async def test_multiple_named_locks(self) -> None:
        lock = LocalLockBackend()
        a1 = await lock.acquire("lock_a")
        a2 = await lock.acquire("lock_b")
        assert a1 is True
        assert a2 is True
        await lock.release("lock_a")
        await lock.release("lock_b")


# ============================================================================
# FileLockBackend
# ============================================================================


class TestFileLockBackend:
    @pytest.mark.asyncio
    async def test_acquire_and_release(self, tmp_path) -> None:
        lock = FileLockBackend(lock_dir=tmp_path / "locks")
        acquired = await lock.acquire("file_test")
        assert acquired is True
        await lock.release("file_test")

    @pytest.mark.asyncio
    async def test_lock_path_sanitization(self, tmp_path) -> None:
        lock = FileLockBackend(lock_dir=tmp_path / "locks")
        path = lock._lock_path("session/user/123")
        assert "/" not in path.name or "\\" not in path.name

    @pytest.mark.asyncio
    async def test_context_manager(self, tmp_path) -> None:
        lock = FileLockBackend(lock_dir=tmp_path / "locks")
        async with lock("ctx_test"):
            pass

    @pytest.mark.asyncio
    async def test_release_unknown(self, tmp_path) -> None:
        lock = FileLockBackend(lock_dir=tmp_path / "locks")
        await lock.release("never_acquired")


# ============================================================================
# RedisLockBackend (without actual Redis)
# ============================================================================


class TestRedisLockBackend:
    @pytest.mark.asyncio
    async def test_fallback_to_file_lock(self, tmp_path) -> None:
        """Without Redis, it should fall back to file locking."""
        lock = RedisLockBackend(
            redis_url="redis://localhost:9999/0",
            lock_dir=tmp_path / "locks",
        )
        # Force redis unavailable
        lock._redis_available = False
        acquired = await lock.acquire("test")
        assert acquired is True
        await lock.release("test")

    @pytest.mark.asyncio
    async def test_release_without_token(self, tmp_path) -> None:
        lock = RedisLockBackend(lock_dir=tmp_path / "locks")
        lock._redis_available = False
        # Release without ever acquiring should not raise
        await lock.release("never_held")


# ============================================================================
# DistributedLock base class
# ============================================================================


class TestDistributedLockBase:
    @pytest.mark.asyncio
    async def test_aenter_without_name_raises(self) -> None:
        lock = DistributedLock()
        with pytest.raises(RuntimeError, match="Use lock"):
            await lock.__aenter__()

    @pytest.mark.asyncio
    async def test_acquire_not_implemented(self) -> None:
        lock = DistributedLock()
        with pytest.raises(NotImplementedError):
            await lock.acquire("x")

    @pytest.mark.asyncio
    async def test_release_not_implemented(self) -> None:
        lock = DistributedLock()
        with pytest.raises(NotImplementedError):
            await lock.release("x")


# ============================================================================
# Factory
# ============================================================================


class TestCreateLock:
    def test_default_returns_local(self) -> None:
        lock = create_lock()
        assert isinstance(lock, LocalLockBackend)

    def test_with_config_local(self) -> None:
        class FakeConfig:
            lock_backend = "local"
            cognithor_home = "/tmp"

        lock = create_lock(FakeConfig())
        assert isinstance(lock, LocalLockBackend)

    def test_with_config_file(self, tmp_path) -> None:
        class FakeConfig:
            lock_backend = "file"
            cognithor_home = str(tmp_path)

        lock = create_lock(FakeConfig())
        assert isinstance(lock, FileLockBackend)

    def test_with_config_redis(self) -> None:
        class FakeConfig:
            lock_backend = "redis"
            redis_url = "redis://localhost:6379/0"
            cognithor_home = "/tmp"

        lock = create_lock(FakeConfig())
        assert isinstance(lock, RedisLockBackend)
