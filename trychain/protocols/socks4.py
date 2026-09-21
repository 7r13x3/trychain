"""
TryChain — SOCKS4 protocol
SOCKS4 only supports IPv4 and no authentication password.
"""
import ipaddress
import struct
from .base import BaseProxy


class Socks4Proxy(BaseProxy):

    async def connect_to(self, reader, writer,
                         target_host: str, target_port: int):
        try:
            ip = ipaddress.IPv4Address(target_host)
            packed_ip = ip.packed
        except ipaddress.AddressValueError:
            raise ConnectionError("SOCKS4 requires an IPv4 address")

        userid = (self.username or "").encode()

        # VN=4, CD=1 (CONNECT), DSTPORT, DSTIP, USERID, NULL
        req = (
            b"\x04\x01"
            + struct.pack(">H", target_port)
            + packed_ip
            + userid
            + b"\x00"
        )
        writer.write(req)
        await writer.drain()

        resp = await reader.readexactly(8)
        if resp[0] != 0x00 or resp[1] != 0x5A:
            raise ConnectionError(f"SOCKS4 refused (code {resp[1]})")
