"""
TryChain — IPv6 Blocker
Prevents IPv6 traffic from bypassing the proxy chain and leaking the real IP.
"""
import ipaddress


def is_ipv6(host: str) -> bool:
    try:
        return isinstance(ipaddress.ip_address(host), ipaddress.IPv6Address)
    except ValueError:
        return False


def block_ipv6(host: str, enabled: bool = True):
    """
    Raise ConnectionError if `host` is IPv6 and the blocker is enabled.
    """
    if enabled and is_ipv6(host):
        raise ConnectionError(
            f"IPv6 connection blocked by policy: {host} — "
            f"IPv6 can leak your real IP"
        )
