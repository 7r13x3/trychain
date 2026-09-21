"""
TryChain — Local SOCKS5 server
Accepts client connections on 127.0.0.1:1080 (configurable) and
tunnels them through the proxy chain, applying all security layers.
"""
import asyncio
import ipaddress
import struct

from .chain import open_through_chain, ChainError
from .isolation import isolate_chain
from .rotation import RotationManager
from .killswitch import KillSwitch
from ..security.ipv6 import block_ipv6
from ..security.padding import pad_stream
from .. import logger


async def _relay(reader, writer):
    """Forward bytes in one direction until EOF."""
    try:
        while True:
            data = await reader.read(65536)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except Exception:
        pass
    finally:
        try:
            writer.close()
        except Exception:
            pass


class TryChainServer:
    def __init__(self, config):
        self.cfg = config
        self._server = None
        self._rotation = RotationManager(
            config.proxies,
            interval=config.rotation.interval,
        ) if config.rotation.enabled else None
        self._killswitch = KillSwitch(enabled=config.security.kill_switch)

    # ─────────────────────────────────────────────
    async def _handle_client(self, reader, writer):
        peer = writer.get_extra_info("peername")
        client_ip = peer[0] if peer else "?"

        try:
            # ── SOCKS5 handshake ──
            ver, nmethods = await reader.readexactly(2)
            if ver != 0x05:
                writer.close()
                return
            await reader.readexactly(nmethods)
            writer.write(b"\x05\x00")     # no auth
            await writer.drain()

            # ── CONNECT request ──
            ver, cmd, _, atyp = await reader.readexactly(4)
            if cmd != 0x01:
                writer.write(b"\x05\x07\x00\x01" + b"\x00" * 6)
                await writer.drain()
                writer.close()
                return

            if atyp == 0x01:
                raw = await reader.readexactly(4)
                target_host = str(ipaddress.IPv4Address(raw))
            elif atyp == 0x03:
                ln = (await reader.readexactly(1))[0]
                target_host = (await reader.readexactly(ln)).decode()
            elif atyp == 0x04:
                raw = await reader.readexactly(16)
                target_host = str(ipaddress.IPv6Address(raw))
            else:
                writer.close()
                return

            target_port = struct.unpack(
                ">H", await reader.readexactly(2)
            )[0]

            # ── Security: IPv6 blocker ──
            try:
                block_ipv6(target_host,
                           enabled=self.cfg.security.block_ipv6)
            except ConnectionError as e:
                logger.error(str(e))
                writer.write(b"\x05\x02\x00\x01" + b"\x00" * 6)
                await writer.drain()
                writer.close()
                return

            # ── Build the chain (isolation or static) ──
            proxies = self._rotation.current() if self._rotation \
                else list(self.cfg.proxies)

            if self.cfg.security.circuit_isolation:
                session_key = f"{client_ip}:{target_host}:{target_port}"
                proxies = isolate_chain(
                    proxies, session_key,
                    min_hops=self.cfg.min_hops,
                )

            route = " → ".join(p.name for p in proxies)
            logger.info(f"{client_ip} → {target_host}:{target_port} "
                        f"via {route}")

            # ── Open the chain ──
            try:
                up_reader, up_writer = await open_through_chain(
                    proxies, target_host, target_port,
                    timeout=self.cfg.timeout,
                )
            except ChainError as e:
                logger.error(f"Chain failed: {e}")
                self._killswitch.trip()
                writer.write(b"\x05\x05\x00\x01" + b"\x00" * 6)
                await writer.drain()
                writer.close()
                return

            # chain OK → re-arm kill switch
            self._killswitch.reset()

            # ── Reply to client: success ──
            writer.write(b"\x05\x00\x00\x01" + b"\x00" * 6)
            await writer.drain()

            # ── Apply padding on the upstream socket ──
            tasks = []
            if self.cfg.security.padding:
                tasks.append(asyncio.create_task(
                    pad_stream(up_writer,
                               interval=self.cfg.security.padding_interval)
                ))

            # ── Kill switch watcher ──
            if self.cfg.security.kill_switch:
                tasks.append(asyncio.create_task(
                    self._killswitch.guard(reader, writer)
                ))

            # ── Bidirectional relay ──
            await asyncio.gather(
                _relay(reader, up_writer),
                _relay(up_reader, writer),
            )

            for t in tasks:
                t.cancel()

        except Exception:
            pass
        finally:
            try:
                writer.close()
            except Exception:
                pass

    # ─────────────────────────────────────────────
    async def start(self):
        logger.banner()
        logger.info(f"Listening on "
                    f"{self.cfg.listen}:{self.cfg.port}  "
                    f"(mode={self.cfg.mode}, "
                    f"{len(self.cfg.proxies)} proxies)")
        logger.chain_table(self.cfg.proxies)
        logger.features_table(self.cfg.security.as_dict())

        if self._rotation:
            self._rotation.start()
            logger.success(f"Rotation ON — every "
                           f"{self.cfg.rotation.interval}s")

        self._server = await asyncio.start_server(
            self._handle_client,
            self.cfg.listen,
            self.cfg.port,
        )

        async with self._server:
            await self._server.serve_forever()

    async def stop(self):
        if self._rotation:
            self._rotation.stop()
        if self._server:
            self._server.close()
            await self._server.wait_closed()
