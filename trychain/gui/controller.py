"""
TryChain — GUI Controller
Bridges the Tkinter UI with the asyncio TryChainServer running in a
background thread.
"""
import asyncio
import threading
import queue

from ..config import load
from ..core.server import TryChainServer


class Controller:
    def __init__(self, log_queue: queue.Queue):
        self.log_queue = log_queue
        self.server = None
        self.loop = None
        self.thread = None
        self.running = False
        self.cfg = None

    # ─────────────────────────────────────────────
    def start(self, config_path: str):
        if self.running:
            self._log("⚠ Server already running")
            return

        try:
            self.cfg = load(config_path)
        except Exception as e:
            self._log(f"✗ Config error: {e}")
            return

        self.thread = threading.Thread(
            target=self._run_loop, daemon=True
        )
        self.thread.start()
        self.running = True
        self._log(f"✓ Server starting on "
                  f"{self.cfg.listen}:{self.cfg.port}")

    def _run_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.server = TryChainServer(self.cfg)
        try:
            self.loop.run_until_complete(self.server.start())
        except Exception as e:
            self._log(f"✗ Server error: {e}")
        finally:
            self.running = False

    # ─────────────────────────────────────────────
    def stop(self):
        if not self.running:
            self._log("⚠ Server not running")
            return
        self._log("⏹ Stopping server...")
        if self.server and self.loop:
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self.server.stop(), self.loop
                )
                future.result(timeout=5)
            except Exception as e:
                self._log(f"✗ Stop error: {e}")
        self.running = False
        self._log("✓ Server stopped")

    # ─────────────────────────────────────────────
    def toggle_feature(self, feature: str, value: bool):
        """Update a security feature on the live server."""
        if not self.server:
            self._log(f"⚙ {feature} = {value} (server not running)")
            return
        sec = self.server.cfg.security

        mapping = {
            "isolation":      "circuit_isolation",
            "kill_switch":    "kill_switch",
            "dns_over_proxy": "dns_over_proxy",
            "block_ipv6":     "block_ipv6",
            "padding":        "padding",
        }

        if feature == "rotation":
            self.server.cfg.rotation.enabled = value
            self._log(f"⚙ Rotation = {value}")
            return

        attr = mapping.get(feature)
        if attr and hasattr(sec, attr):
            setattr(sec, attr, value)
            self._log(f"⚙ {attr} = {value}")

    # ─────────────────────────────────────────────
    def _log(self, msg: str):
        self.log_queue.put(msg)
