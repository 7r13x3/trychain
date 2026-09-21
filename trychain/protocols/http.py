"""
TryChain — HTTP CONNECT protocol
Used by corporate proxies and HTTPS relays.
"""
import base64
from .base import BaseProxy


class HttpProxy(BaseProxy):

    def __init__(self, host, port, username="", password="", use_tls=False):
        super().__init__(host, port, username, password)
        self.use_tls = use_tls

    async def connect_to(self, reader, writer,
                         target_host: str, target_port: int):
        target = f"{target_host}:{target_port}"

        lines = [
            f"CONNECT {target} HTTP/1.1",
            f"Host: {target}",
            "Proxy-Connection: keep-alive",
        ]
        if self.username:
            creds = f"{self.username}:{self.password}".encode()
            b64 = base64.b64encode(creds).decode()
            lines.append(f"Proxy-Authorization: Basic {b64}")

        # blank line terminates the request
        lines.append("")
        lines.append("")

        writer.write("\r\n".join(lines).encode())
        await writer.drain()

        # ── status line ──
        status_line = await reader.readline()
        if b"200" not in status_line:
            raise ConnectionError(f"HTTP proxy refused: {status_line!r}")

        # ── consume headers until blank line ──
        while True:
            line = await reader.readline()
            if line in (b"\r\n", b"\n", b""):
                break
