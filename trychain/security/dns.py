"""
TryChain — DNS over Proxy
Forces DNS queries to travel through the chain instead of
being sent in the clear to the local resolver.
"""
import struct


def build_dns_query(hostname: str, tid: int = 0x1234) -> bytes:
    """Build a minimal DNS A-record query."""
    flags = 0x0100        # standard query, recursion desired
    header = struct.pack(">HHHHHH", tid, flags, 1, 0, 0, 0)
    q = b""
    for part in hostname.split("."):
        q += bytes([len(part)]) + part.encode()
    q += b"\x00"
    q += struct.pack(">HH", 1, 1)   # A record, IN class
    return header + q


def parse_dns_response(data: bytes):
    """Extract the first A-record IP from a DNS response, if any."""
    if len(data) < 12:
        return None
    ancount = struct.unpack(">H", data[6:8])[0]
    if ancount == 0:
        return None

    idx = 12
    # skip the question section
    while data[idx] != 0:
        idx += data[idx] + 1
    idx += 5   # null byte + qtype(2) + qclass(2)

    # first answer
    if data[idx] & 0xC0 == 0xC0:
        idx += 2                # compressed name pointer
    else:
        while data[idx] != 0:
            idx += data[idx] + 1
        idx += 1

    if idx + 10 > len(data):
        return None

    rtype, rclass, ttl, rdlen = struct.unpack(">HHIH", data[idx:idx + 10])
    idx += 10
    if rtype == 1 and rdlen == 4:
        return ".".join(str(b) for b in data[idx:idx + 4])
    return None
