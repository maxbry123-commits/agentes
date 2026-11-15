"""Enhanced tests for TalkMode -- additional coverage."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cognithor.channels.talk_mode import TalkMode


@pytest.fixture
def voice_channel() -> MagicMock:
    vc = MagicMock()
    vc._handler = AsyncMock()
    vc.listen_once = AsyncMock(return_value=None)
    vc.send = AsyncMock()
    vc._play_audio = AsyncMock()
    return vc


@pytest.fixture
def wake_detector() -> MagicMock:
    wd = MagicMock()
    wd.stop = MagicMock()
    return wd


@pytest.fixture
def tm(voice_channel: MagicMock, wake_detector: MagicMock) -> TalkMode:
    return TalkMode(voice_channel, wake_detector, auto_listen=False, confirmation_beep=False)


class TestTalkModeProperties:
    def test_initial_state(self, tm: TalkMode) -> None:
        assert tm.is_active is False
        assert tm.auto_listen is False

    def test_auto_listen_setter(self, tm: TalkMode) -> None:
        tm.auto_listen = True
        assert tm.auto_listen is True


class TestTalkModeStart:
    @pytest.mark.asyncio
    async def test_start(self, tm: TalkMode) -> None:
        await tm.start()
        assert tm.is_active is True
        assert tm._task is not None
        # Clean up
        await tm.stop()

    @pytest.mark.asyncio
    async def test_start_already_active(self, tm: TalkMode) -> None:
        tm._active = True
        await tm.start()
        # Should log warning but not create second task
        assert tm._task is None  # not created since already active


class TestTalkModeStop:
    @pytest.mark.asyncio
    async def test_stop_not_started(self, tm: TalkMode) -> None:
        await tm.stop()
        assert tm.is_active is False

    @pytest.mark.asyncio
    async def test_stop_cancels_task(self, tm: TalkMode) -> None:
        await tm.start()
        assert tm.is_active is True
        await tm.stop()
        assert tm.is_active is False
        assert tm._task is None


class TestTalkModeWaitForWakeWord:
    @pytest.mark.asyncio
    async def test_wait_returns_false(self, tm: TalkMode) -> None:
        result = await tm._wait_for_wake_word()
        assert result is False


class TestTalkModePlayConfirmation:
    @pytest.mark.asyncio
    async def test_play_confirmation(self, tm: TalkMode) -> None:
        await tm._play_confirmation()
        tm._voice._play_audio.assert_called_once()
        # The audio should be WAV format
        call_data = tm._voice._play_audio.call_args[0][0]
        assert call_data[:4] == b"RIFF"


class TestTalkModeLoop:
    @pytest.mark.asyncio
    async def test_loop_no_wake_word(self, tm: TalkMode) -> None:
        tm._active = True
        call_count = 0

        async def fake_wait():
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                tm._active = False
            return False

        with patch.object(tm, "_wait_for_wake_word", side_effect=fake_wait):
            await tm._loop()
        assert tm.is_active is False

    @pytest.mark.asyncio
    async def test_loop_with_speech(self, tm: TalkMode) -> None:
        from cognithor.models import OutgoingMessage

        tm._active = True
        tm._voice.listen_once = AsyncMock(return_value="Hello Jarvis")
        response = OutgoingMessage(channel="voice", text="Hi there", session_id="s")
        tm._voice._handler = AsyncMock(return_value=response)

        call_count = 0

        async def fake_wait():
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                tm._active = False
                return False
            return True

        with patch.object(tm, "_wait_for_wake_word", side_effect=fake_wait):
            await tm._loop()

        tm._voice._handler.assert_called_once()
        tm._voice.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_loop_no_speech(self, tm: TalkMode) -> None:
        tm._active = True
        tm._voice.listen_once = AsyncMock(return_value=None)

        call_count = 0

        async def fake_wait():
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                tm._active = False
                return False
            return True

        with patch.object(tm, "_wait_for_wake_word", side_effect=fake_wait):
            await tm._loop()

        tm._voice._handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_loop_with_confirmation_beep(
        self,
        voice_channel: MagicMock,
        wake_detector: MagicMock,
    ) -> None:
        tm = TalkMode(voice_channel, wake_detector, confirmation_beep=True)
        tm._active = True
        tm._voice.listen_once = AsyncMock(return_value=None)

        call_count = 0

        async def fake_wait():
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                tm._active = False
                return False
            return True

        with patch.object(tm, "_wait_for_wake_word", side_effect=fake_wait):
            with patch.object(tm, "_play_confirmation", new_callable=AsyncMock) as play:
                await tm._loop()
            play.assert_called_once()

    @pytest.mark.asyncio
    async def test_loop_exception(self, tm: TalkMode) -> None:
        tm._active = True

        async def fake_wait():
            raise RuntimeError("unexpected")

        with patch.object(tm, "_wait_for_wake_word", side_effect=fake_wait):
            await tm._loop()
        assert tm.is_active is False
