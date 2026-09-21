"""
TryChain — Traffic Padding
Injects dummy bytes into the tunnel at regular intervals to
defeat traffic-pattern analysis.
"""
import asyncio
import os
import struct


async def pad_stream(writer, interval: float = 5.0,
                     min_bytes: int = 16, max_bytes: int = 256):
    """
    Every `interval` seconds, write a random-length dummy packet
    into `writer`. The remote end (proxy) treats it as opaque payload.
    """
    try:
        while True:
            await asyncio.sleep(interval)
            size = int.from_bytes(os.urandom(2), "big")
            size = (size % (max_bytes - min_bytes)) + min_bytes
            dummy = os.urandom(size)
            # length-prefixed so the peer can (optionally) ignore it
            writer.write(struct.pack(">H", len(dummy)) + dummy)
            await writer.drain()
            if writer.is_closing():
                return
    except asyncio.CancelledError:
        return
    except Exception:
        return
