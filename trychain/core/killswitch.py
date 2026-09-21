"""
TryChain — Kill Switch
If the chain breaks, block all client traffic immediately.
"""
import asyncio


class KillSwitch:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._armed = True

    def trip(self):
        """Chain broke -> block traffic."""
        if self.enabled:
            self._armed = False

    def reset(self):
        """Chain restored -> allow traffic again."""
        self._armed = True

    @property
    def is_armed(self):
        return (not self.enabled) or self._armed

    async def guard(self, reader, writer, timeout: float = 2.0):
        """
        Monitor a client connection. If the kill switch trips,
        close the connection immediately.
        """
        if not self.enabled:
            return
        try:
            while True:
                await asyncio.sleep(timeout)
                if not self._armed:
                    try:
                        writer.close()
                        await writer.wait_closed()
                    except Exception:
                        pass
                    return
                # if the client is already gone, stop watching
                if writer.is_closing():
                    return
        except asyncio.CancelledError:
            return
        except Exception:
            return
