import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from app.main import TwinPeer


class Socket:
    def __init__(self):
        self.writing = False
        self.frames = []

    async def send_text(self, payload):
        # Detect overlapping heartbeat / state writes, without relying on
        # timing thresholds or a particular server's transport implementation.
        assert not self.writing
        self.writing = True
        await asyncio.sleep(0)
        self.frames.append(payload)
        self.writing = False


def test_concurrent_socket_writes_are_serialized_and_old_states_are_dropped():
    async def scenario():
        socket = Socket()
        peer = TwinPeer(socket)
        now = datetime.now(UTC)
        await asyncio.gather(
            peer.send("newer", now + timedelta(seconds=1)),
            peer.send("heartbeat"),
            peer.send("older", now),
            peer.send("duplicate", now + timedelta(seconds=1)),
            peer.send("newest", now + timedelta(seconds=2)),
        )
        assert socket.frames == ["newer", "heartbeat", "newest"]

    asyncio.run(scenario())


def test_failed_socket_does_not_keep_retrying_queued_samples():
    async def scenario():
        class FailedSocket:
            calls = 0

            async def send_text(self, payload):
                self.calls += 1
                raise OSError("Disconnected")

        socket = FailedSocket()
        peer = TwinPeer(socket)
        with pytest.raises(OSError):
            await peer.send("first")
        await peer.send("queued sample")
        assert socket.calls == 1
        assert peer.failed

    asyncio.run(scenario())
