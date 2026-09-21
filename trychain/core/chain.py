"""
TryChain — Chain engine
Opens a tunneled connection through a sequence of proxies.

Flow:
    Client -> P1 -> P2 -> P3 -> Target

Each proxy is told to connect to the NEXT hop. The last one is told
to connect to the final target.
"""
import asyncio
from ..protocols import build


class ChainError(Exception):
    pass


async def open_through_chain(proxies_cfg, target_host: str,
                             target_port: int, timeout: int = 10):
    """
    Open a TCP tunnel to target_host:target_port by hopping through
    every proxy in `proxies_cfg`, in order.

    Returns (reader, writer) — the final tunneled socket.
    """
    if not proxies_cfg:
        # Direct connection (no proxies configured)
        return await asyncio.wait_for(
            asyncio.open_connection(target_host, target_port),
            timeout=timeout,
        )

    # ── Step 1: connect to the FIRST proxy ──
    first = proxies_cfg[0]
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(first.host, first.port),
            timeout=timeout,
        )
    except Exception as e:
        raise ChainError(
            f"Cannot reach first proxy {first.host}:{first.port} — {e}"
        )

    # ── Step 2: hop through proxies 1..N-1 ──
    #   Each hop tells the current proxy to connect to the NEXT proxy.
    for i in range(len(proxies_cfg) - 1):
        current_cfg = proxies_cfg[i]
        next_cfg = proxies_cfg[i + 1]

        try:
            handler = build(current_cfg)
            await asyncio.wait_for(
                handler.connect_to(reader, writer,
                                   next_cfg.host, next_cfg.port),
                timeout=timeout,
            )
        except Exception as e:
            writer.close()
            raise ChainError(
                f"Hop {i + 1} ({current_cfg.name} -> "
                f"{next_cfg.name}) failed: {e}"
            )

    # ── Step 3: last proxy connects to the FINAL TARGET ──
    last_cfg = proxies_cfg[-1]
    try:
        handler = build(last_cfg)
        await asyncio.wait_for(
            handler.connect_to(reader, writer, target_host, target_port),
            timeout=timeout,
        )
    except Exception as e:
        writer.close()
        raise ChainError(
            f"Final hop ({last_cfg.name} -> "
            f"{target_host}:{target_port}) failed: {e}"
        )

    return reader, writer
