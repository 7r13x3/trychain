# TryChain 🕸️

> Chain it. Route it.

A cross-platform proxy chaining tool that routes any TCP traffic through a chain of SOCKS5 / SOCKS4 / HTTP proxies, with six security layers built on top of the chain.
[Your App] → [TryChain :1080] → [P1] → [P2] → [P3] → [Target]
Each connection gets
a different route

---

## Table of Contents

- [Overview](#overview)
- [Security Layers](#security-layers)
- [Features](#features)
- [What TryChain Is Not](#what-trychain-is-not)
- [Installation](#installation)
- [CLI Usage](#cli-usage)
- [GUI Usage](#gui-usage)
- [Configuration](#configuration)
- [Architecture](#architecture)
- [Legal Disclaimer](#legal-disclaimer)
- [License](#license)

---

## Overview

TryChain runs a **local SOCKS5 server** on `127.0.0.1:1080`. Any application — a browser, `curl`, a Python script — can point its traffic to that port. TryChain then forwards that traffic through a configurable chain of proxies before reaching the final target.

Every hop in the chain only knows the address of the next hop. The last proxy only knows the final destination. No single proxy ever sees both the origin and the destination.

On top of the chain, TryChain applies **six independent security layers** that can be toggled live from the CLI or GUI without restarting the server.

---

## Security Layers

### 1. Circuit Isolation

**What it does:** Every new connection gets its own unique route through the proxy pool.

Instead of sending all traffic through `P1 → P2 → P3`, each connection is shuffled deterministically based on a session key (client IP + target host + target port):
Connection A → P2 → P1 → P3 → Target
Connection B → P4 → P5 → P1 → Target
Connection C → P1 → P3 → P5 → Target

**Why it matters:** If one connection is compromised or correlated, it cannot be linked to any other connection from the same client. Traffic analysis across sessions becomes significantly harder.

**Toggle:** `[security] circuit_isolation = true`

---

### 2. Kill Switch

**What it does:** Continuously monitors the health of the active chain. If any proxy in the chain fails, the kill switch trips and **blocks all client traffic immediately** — no packets leave the machine until the chain is restored.
[Chain OK] → traffic flows normally
[Chain broken] → BLOCK ALL TRAFFIC
[Chain restored] → traffic resumes

**Why it matters:** Prevents accidental leaks when a proxy goes down. Without a kill switch, a client might silently fall back to a direct connection, exposing the real IP.

**Toggle:** `[security] kill_switch = true`

---

### 3. DNS over Proxy

**What it does:** Forces all DNS resolution to travel through the proxy chain instead of asking your local resolver.

Without this, when you visit `example.com`, your operating system asks your ISP's DNS server for the IP — even if your web traffic is being proxied. That query alone reveals every domain you visit.
Without DNS over Proxy:
[Your OS] ──► [ISP DNS] ← leak: every domain visible

With DNS over Proxy:
[Your OS] ──► [TryChain] ──► [P1] ──► [P2] ──► [DNS server]
↑
DNS query travels through the chain

**Why it matters:** Eliminates DNS leaks, one of the most common ways a proxied connection still exposes browsing activity.

**Toggle:** `[security] dns_over_proxy = true`

---

### 4. IPv6 Blocker

**What it does:** Blocks every IPv6 connection attempt outright. Only IPv4 traffic is allowed through the chain.

**Why it matters:** Most VPNs and proxy tools are configured for IPv4 only. If your machine has IPv6 enabled, the operating system may silently route IPv6 traffic **directly to the internet**, bypassing the proxy entirely — exposing the real IP.

This is one of the most overlooked leaks in proxy setups.

**Toggle:** `[security] block_ipv6 = true`

---

### 5. Rotation

**What it does:** Randomizes the order of proxies in the active chain at a fixed interval.
t = 0s → chain is P1 → P2 → P3 → P4 → P5
t = 60s → chain is P3 → P5 → P1 → P4 → P2
t = 120s → chain is P4 → P2 → P5 → P1 → P3

**Why it matters:** Even if one proxy in the chain is identified or correlated over time, the rotation breaks that pattern. Long-term traffic analysis against a static chain becomes ineffective.

**Toggle:** `[rotation] enabled = true` / `interval = 60`

---

### 6. Traffic Padding

**What it does:** Injects dummy packets into the tunnel at regular intervals.
Real traffic: ─█──█──█─────█──█──█─
With padding: ─█─p─█─p─█─p───█─p─█─p─█─p─
↑ padding packets

**Why it matters:** Defeats traffic-pattern analysis. An observer watching packet timing and sizes cannot distinguish real bursts of activity from injected noise, which obscures when you are actively using the connection and what type of data is flowing.

**Toggle:** `[security] padding = true` / `padding_interval = 5`

---

## Features

| Feature | Description |
|---|---|
| **Multi-protocol** | SOCKS5, SOCKS4, HTTP CONNECT, HTTPS |
| **Chain modes** | `strict` (all proxies required), `dynamic` (skip dead), `isolation` (unique route per connection) |
| **Circuit Isolation** | Every connection takes a different path through the pool |
| **Kill Switch** | Blocks all traffic the moment the chain breaks |
| **DNS over Proxy** | DNS queries travel through the chain — no leaks |
| **IPv6 Blocker** | Prevents IPv6 from bypassing the proxy |
| **Rotation** | Randomizes proxy order on a timer |
| **Traffic Padding** | Injects noise to defeat pattern analysis |
| **Hot Reload** | Edit config or toggle features without restarting |
| **GUI + CLI** | Both interfaces fully functional |
| **Portable .exe** | Optional PyInstaller build for Windows |

---

## What TryChain Is Not

- ❌ **Not a VPN** — it does not create an encrypted tunnel by itself
- ❌ **Not Tor** — it does not provide anonymity on its own
- ❌ **Not an anonymity tool** — anonymity depends entirely on the proxies you configure

TryChain is a **traffic router**. If you point it at well-chosen proxies (Tor, trusted VPN, paid clean proxies), it strengthens your setup. If you point it at free, untrusted proxies, you are worse off than not using it at all.

---

## Installation

```bash
git clone https://github.com/7r13x3/trychain.git
cd trychain
pip install -r requirements.txt
Requires Python 3.10+.
CLI Usage
Start the local SOCKS5 server:
python -m trychain.cli start --config configs/example.toml
Launch the GUI:
python -m trychain.cli gui
Validate configuration without starting:
python -m trychain.cli check --config configs/example.toml
Route a test request through the chain:
curl --socks5 127.0.0.1:1080 https://ifconfig.me
The IP returned should match your last proxy in the chain, not your real IP.
GUI Usage
The GUI provides fully functional controls — every toggle and button directly modifies the running server's state.

Control	Action
START	Loads a config file and launches the local server
STOP	Gracefully shuts down the server and releases port 1080
Reload Config	Re-reads the TOML file and applies changes live
Circuit Isolation	Toggles per-connection routing
Kill Switch	Arms or disarms the traffic block
DNS over Proxy	Enables or disables DNS tunneling through the chain
Block IPv6	Enables or disables the IPv6 leak guard
Rotation	Starts or stops automatic chain rotation
Padding	Enables or disables dummy traffic injection
+ Add / − Remove	Edits the proxy list in real time
Live Log	Streams every connection event as it happens
Configuration
Copy configs/example.toml and add your proxies:
[server]
listen = "127.0.0.1"
port = 1080

[chain]
mode = "isolation"
timeout = 10
min_hops = 3

[security]
circuit_isolation = true
kill_switch       = true
dns_over_proxy    = true
block_ipv6        = true
padding           = true
padding_interval  = 5

[rotation]
enabled  = true
interval = 60

[[proxies]]
name = "tor"
type = "socks5"
host = "127.0.0.1"
port = 9050

[[proxies]]
name = "residential1"
type = "socks5"
host = "1.2.3.4"
port = 1080
username = "user"
password = "pass"
Chain order equals the order of [[proxies]] blocks. Add as many as you want.
Legal Disclaimer
TryChain is provided for legal privacy, security research, and authorized penetration testing only.

You are solely responsible for ensuring your use of this software complies with all applicable local, national, and international laws. Do not use this tool to violate any law or the rights of others. The authors assume no liability for misuse.
License
GPL-3.0
Commit changes. Then say **"next"** and I'll send `trychain/__init__.py`, `trychain/logger.py`, and `trychain/config.py`.
