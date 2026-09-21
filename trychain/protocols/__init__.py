"""
TryChain — Proxy protocols
Factory for building protocol handlers from config.
"""
from .socks5 import Socks5Proxy
from .socks4 import Socks4Proxy
from .http import HttpProxy

PROTOCOLS = {
    "socks5": Socks5Proxy,
    "socks4": Socks4Proxy,
    "http":   HttpProxy,
    "https":  HttpProxy,
}


def build(proxy_cfg):
    """Build a protocol handler from a Proxy config object."""
    cls = PROTOCOLS.get(proxy_cfg.type)
    if not cls:
        raise ValueError(f"Unknown proxy type: {proxy_cfg.type}")

    if proxy_cfg.type in ("http", "https"):
        return cls(
            proxy_cfg.host,
            proxy_cfg.port,
            proxy_cfg.username,
            proxy_cfg.password,
            use_tls=(proxy_cfg.type == "https"),
        )

    return cls(
        proxy_cfg.host,
        proxy_cfg.port,
        proxy_cfg.username,
        proxy_cfg.password,
    )


__all__ = ["build", "Socks5Proxy", "Socks4Proxy", "HttpProxy"]
