"""
TryChain — SOCKS5 protocol
RFC 1928 + RFC 1929 (username/password auth)
"""
import ipaddress
import struct
from .base import BaseProxy


class Socks5Proxy(BaseProxy):

    async def connect_to(self, reader, writer,
                         target_host: str, target_port: int):
        # ── Step 1: greeting ──
        if self.username:
            # offer "no auth" and "user/pass"
            writer.write(b"\x05\x02\x00\x02")
        else:
            # offer only "no auth"
            writer.write(b"\x05\x01\x00")
        await writer.drain()

        ver, method = await reader.readexactly(2)
        if ver != 0x05:
            raise ConnectionError("Not a SOCKS5 server")

        # ── Step 2: auth ──
        if method == 0x02:
            u = self.username.encode()
            p = self.password.encode()
            writer.write(bytes([0x01, len(u)]) + u + bytes([len(p)]) + p)
            await writer.drain()
            _, status = await reader.readexactly(2)
            if status != 0x00:
                raise ConnectionError("SOCKS5 authentication failed")
        elif method != 0x00:
            raise ConnectionError(f"SOCKS5 refused auth method: {method}")

        # ── Step 3: CONNECT request ──
        try:
            ip = ipaddress.ip_address(target_host)
            if isinstance(ip, ipaddress.IPv4Address):
                addr = b"\x01" + ip.packed
            else:
                addr = b"\x04" + ip.packed
        except ValueError:
            # domain name
            h = target_host.encode()
            addr = bytes([0x03, len(h)]) + h

        writer.write(
            b"\x05\x01\x00" + addr + struct.pack(">H", target_port)
        )
        await writer.drain()

        # ── Step 4: response ──
        ver, rep, _, atyp = await reader.readexactly(4)
        if rep != 0x00:
            raise ConnectionError(f"SOCKS5 CONNECT failed (code {rep})")

        # consume the bound address
        if atyp == 0x01:
            await reader.readexactly(6)          # IPv4 + port
        elif atyp == 0x03:
            ln = (await reader.readexactly(1))[0]
            await reader.readexactly(ln + 2)     # domain + port
        elif atyp == 0x04:
            await reader.readexactly(18)         # IPv6 + port
        else:
            raise ConnectionError("SOCKS5 bad address type")
