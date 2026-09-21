"""
TryChain — Rotation
Randomizes proxy order every N seconds.
"""
import asyncio
import random


class RotationManager:
    def __init__(self, proxies, interval: int = 60):
        self.proxies = list(proxies)
        self.interval = max(5, interval)
        self._current = list(proxies)
        self._task = None
        self._lock = asyncio.Lock()

    def current(self):
        """Return the current chain order."""
        return list(self._current)

    async def _loop(self):
        while True:
            await asyncio.sleep(self.interval)
            async with self._lock:
                random.shuffle(self._current)

    def start(self):
        if self._task is None:
            self._task = asyncio.create_task(self._loop())

    def stop(self):
        if self._task is not None:
            self._task.cancel()
            self._task = None
