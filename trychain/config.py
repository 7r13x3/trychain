"""
TryChain — Config loader
Reads configs/*.toml and produces a validated Config object.
"""
import sys
from dataclasses import dataclass, field
from typing import List

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


# ─────────────────────────────────────────────────────────────
#  Dataclasses
# ─────────────────────────────────────────────────────────────

@dataclass
class Proxy:
    name: str
    type: str          # socks5 | socks4 | http | https
    host: str
    port: int
    username: str = ""
    password: str = ""


@dataclass
class Security:
    circuit_isolation: bool = True
    kill_switch: bool = True
    dns_over_proxy: bool = True
    block_ipv6: bool = True
    padding: bool = True
    padding_interval: int = 5

    def as_dict(self) -> dict:
        return {
            "Circuit Isolation": self.circuit_isolation,
            "Kill Switch":       self.kill_switch,
            "DNS over Proxy":    self.dns_over_proxy,
            "IPv6 Blocker":      self.block_ipv6,
            "Padding":           self.padding,
        }


@dataclass
class Rotation:
    enabled: bool = True
    interval: int = 60


@dataclass
class Config:
    listen: str = "127.0.0.1"
    port: int = 1080
    mode: str = "strict"          # strict | dynamic | isolation
    timeout: int = 10
    min_hops: int = 3
    proxy_dns: bool = True
    security: Security = field(default_factory=Security)
    rotation: Rotation = field(default_factory=Rotation)
    proxies: List[Proxy] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────
#  Loader
# ─────────────────────────────────────────────────────────────

VALID_MODES = {"strict", "dynamic", "isolation"}
VALID_TYPES = {"socks5", "socks4", "http", "https"}


def load(path: str) -> Config:
    """Load a TOML config file into a Config object."""
    with open(path, "rb") as f:
        data = tomllib.load(f)

    # ── Server ──
    server = data.get("server", {})

    # ── Chain ──
    chain = data.get("chain", {})
    mode = chain.get("mode", "strict").lower()
    if mode not in VALID_MODES:
        raise ValueError(
            f"Invalid chain.mode '{mode}'. Must be one of: {VALID_MODES}"
        )

    # ── Security ──
    sec = data.get("security", {})
    security = Security(
        circuit_isolation=bool(sec.get("circuit_isolation", True)),
        kill_switch=bool(sec.get("kill_switch", True)),
        dns_over_proxy=bool(sec.get("dns_over_proxy", True)),
        block_ipv6=bool(sec.get("block_ipv6", True)),
        padding=bool(sec.get("padding", True)),
        padding_interval=int(sec.get("padding_interval", 5)),
    )

    # ── Rotation ──
    rot = data.get("rotation", {})
    rotation = Rotation(
        enabled=bool(rot.get("enabled", True)),
        interval=int(rot.get("interval", 60)),
    )

    # ── Proxies ──
    proxies = []
    for idx, p in enumerate(data.get("proxies", [])):
        ptype = p.get("type", "").lower()
        if ptype not in VALID_TYPES:
            raise ValueError(
                f"Proxy #{idx + 1} has invalid type '{ptype}'. "
                f"Must be one of: {VALID_TYPES}"
            )
        proxies.append(
            Proxy(
                name=p.get("name", f"proxy{idx + 1}"),
                type=ptype,
                host=p["host"],
                port=int(p["port"]),
                username=p.get("username", ""),
                password=p.get("password", ""),
            )
        )

    if not proxies:
        raise ValueError("Config must define at least one [[proxies]] block")

    return Config(
        listen=server.get("listen", "127.0.0.1"),
        port=int(server.get("port", 1080)),
        mode=mode,
        timeout=int(chain.get("timeout", 10)),
        min_hops=int(chain.get("min_hops", 3)),
        proxy_dns=bool(chain.get("proxy_dns", True)),
        security=security,
        rotation=rotation,
        proxies=proxies,
    )


def save(path: str, cfg: Config):
    """Optional: write a Config back to TOML (used by GUI)."""
    try:
        import tomli_w
    except ImportError:
        raise RuntimeError("tomli-w is required to save config")

    data = {
        "server": {"listen": cfg.listen, "port": cfg.port},
        "chain": {
            "mode": cfg.mode,
            "timeout": cfg.timeout,
            "min_hops": cfg.min_hops,
            "proxy_dns": cfg.proxy_dns,
        },
        "security": {
            "circuit_isolation": cfg.security.circuit_isolation,
            "kill_switch": cfg.security.kill_switch,
            "dns_over_proxy": cfg.security.dns_over_proxy,
            "block_ipv6": cfg.security.block_ipv6,
            "padding": cfg.security.padding,
            "padding_interval": cfg.security.padding_interval,
        },
        "rotation": {
            "enabled": cfg.rotation.enabled,
            "interval": cfg.rotation.interval,
        },
        "proxies": [
            {
                "name": p.name,
                "type": p.type,
                "host": p.host,
                "port": p.port,
                "username": p.username,
                "password": p.password,
            }
            for p in cfg.proxies
        ],
    }
    with open(path, "wb") as f:
        tomli_w.dump(data, f)
