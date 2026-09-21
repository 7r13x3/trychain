"""
TryChain v1.0 — GUI
Tkinter interface. Every toggle and button modifies the live server.
"""
import queue
import tkinter as tk
from tkinter import ttk, filedialog

from .controller import Controller


class TryChainGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TryChain v1.0")
        self.root.geometry("950x680")
        self.root.configure(bg="#1e1e2e")

        self.log_queue = queue.Queue()
        self.controller = Controller(self.log_queue)

        self.features = {
            "isolation":      tk.BooleanVar(value=True),
            "kill_switch":    tk.BooleanVar(value=True),
            "dns_over_proxy": tk.BooleanVar(value=True),
            "block_ipv6":     tk.BooleanVar(value=True),
            "rotation":       tk.BooleanVar(value=True),
            "padding":        tk.BooleanVar(value=True),
        }

        self._build_ui()
        self._poll_logs()

    # ─────────────────────────────────────────────
    def _build_ui(self):
        # Header
        tk.Label(
            self.root, text="🕸️  TryChain v1.0",
            font=("Segoe UI", 20, "bold"),
            fg="#cdd6f4", bg="#1e1e2e"
        ).pack(pady=10)

        # Status row
        status_frame = tk.Frame(self.root, bg="#1e1e2e")
        status_frame.pack(fill="x", padx=20)

        self.status_var = tk.StringVar(value="● STOPPED")
        self.status_label = tk.Label(
            status_frame, textvariable=self.status_var,
            font=("Consolas", 12, "bold"),
            fg="#f38ba8", bg="#1e1e2e"
        )
        self.status_label.pack(side="left")

        self.listen_var = tk.StringVar(value="Listen: 127.0.0.1:1080")
        tk.Label(
            status_frame, textvariable=self.listen_var,
            font=("Consolas", 11), fg="#a6adc8", bg="#1e1e2e"
        ).pack(side="right")

        # Controls
        ctrl = tk.Frame(self.root, bg="#1e1e2e")
        ctrl.pack(pady=12)

        self._btn(ctrl, "▶ START",  self._on_start, "#a6e3a1")
        self._btn(ctrl, "■ STOP",   self._on_stop,  "#f38ba8")
        self._btn(ctrl, "⟳ Reload", self._on_reload, "#89b4fa")

        # Middle: Proxies + Security
        middle = tk.Frame(self.root, bg="#1e1e2e")
        middle.pack(fill="both", expand=True, padx=20, pady=10)

        self._build_proxies_panel(middle)
        self._build_security_panel(middle)

        # Log
        log_frame = tk.LabelFrame(
            self.root, text=" Live Log ",
            bg="#1e1e2e", fg="#cdd6f4",
            font=("Segoe UI", 10, "bold")
        )
        log_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        self.log_text = tk.Text(
            log_frame, bg="#181825", fg="#cdd6f4",
            font=("Consolas", 10), height=10, state="disabled"
        )
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

    # ─────────────────────────────────────────────
    def _btn(self, parent, text, cmd, color):
        tk.Button(
            parent, text=text, command=cmd,
            bg=color, fg="#1e1e2e", width=12,
            font=("Segoe UI", 10, "bold"), relief="flat"
        ).pack(side="left", padx=5)

    # ─────────────────────────────────────────────
    def _build_proxies_panel(self, parent):
        frame = tk.LabelFrame(
            parent, text=" Proxies ",
            bg="#1e1e2e", fg="#cdd6f4",
            font=("Segoe UI", 10, "bold")
        )
        frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self.proxy_list = tk.Listbox(
            frame, bg="#181825", fg="#cdd6f4",
            font=("Consolas", 10), height=10,
            selectbackground="#89b4fa",
            selectforeground="#1e1e2e",
            relief="flat", borderwidth=0
        )
        self.proxy_list.pack(fill="both", expand=True, padx=5, pady=5)

        self.proxy_list.insert(tk.END, "(click START to load proxies)")

        btn_frame = tk.Frame(frame, bg="#1e1e2e")
        btn_frame.pack(fill="x", padx=5, pady=5)

        tk.Button(btn_frame, text="+ Add",
                  command=self._on_add_proxy,
                  bg="#a6e3a1", fg="#1e1e2e",
                  width=10, relief="flat").pack(side="left", padx=2)
        tk.Button(btn_frame, text="− Remove",
                  command=self._on_remove_proxy,
                  bg="#f38ba8", fg="#1e1e2e",
                  width=10, relief="flat").pack(side="left", padx=2)

    # ─────────────────────────────────────────────
    def _build_security_panel(self, parent):
        frame = tk.LabelFrame(
            parent, text=" Security ",
            bg="#1e1e2e", fg="#cdd6f4",
            font=("Segoe UI", 10, "bold")
        )
        frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        labels = {
            "isolation":      "Circuit Isolation",
            "kill_switch":    "Kill Switch",
            "dns_over_proxy": "DNS over Proxy",
            "block_ipv6":     "Block IPv6",
            "rotation":       "Rotation (60s)",
            "padding":        "Padding (5s)",
        }

        for key, label in labels.items():
            tk.Checkbutton(
                frame, text=label, variable=self.features[key],
                command=lambda k=key: self._on_toggle(k),
                bg="#1e1e2e", fg="#cdd6f4",
                selectcolor="#181825",
                activebackground="#1e1e2e",
                activeforeground="#89b4fa",
                font=("Segoe UI", 10)
            ).pack(anchor="w", padx=12, pady=5)

    # ─────────────────────────────────────────────
    # Events
    # ─────────────────────────────────────────────
    def _on_start(self):
        cfg_path = filedialog.askopenfilename(
            title="Select config file",
            filetypes=[("TOML files", "*.toml"), ("All files", "*.*")]
        )
        if not cfg_path:
            return

        self.controller.start(cfg_path)

        if self.controller.cfg:
            self.listen_var.set(
                f"Listen: {self.controller.cfg.listen}:"
                f"{self.controller.cfg.port}"
            )
            self.proxy_list.delete(0, tk.END)
            for i, p in enumerate(self.controller.cfg.proxies, 1):
                self.proxy_list.insert(
                    tk.END,
                    f"{i}. {p.name:<12} {p.type.upper():<6}  "
                    f"{p.host}:{p.port}"
                )

        self.status_var.set("● RUNNING")
        self.status_label.config(fg="#a6e3a1")

    def _on_stop(self):
        self.controller.stop()
        self.status_var.set("● STOPPED")
        self.status_label.config(fg="#f38ba8")

    def _on_reload(self):
        if not self.controller.running:
            self._log("⚠ Server not running")
            return
        cfg_path = filedialog.askopenfilename(
            title="Select config to reload",
            filetypes=[("TOML files", "*.toml")]
        )
        if not cfg_path:
            return
        try:
            from ..config import load
            new_cfg = load(cfg_path)
            self.controller.server.cfg = new_cfg
            self._log("⟳ Config reloaded")

            self.proxy_list.delete(0, tk.END)
            for i, p in enumerate(new_cfg.proxies, 1):
                self.proxy_list.insert(
                    tk.END,
                    f"{i}. {p.name:<12} {p.type.upper():<6}  "
                    f"{p.host}:{p.port}"
                )
        except Exception as e:
            self._log(f"✗ Reload failed: {e}")

    def _on_toggle(self, key):
        value = self.features[key].get()
        self.controller.toggle_feature(key, value)

    def _on_add_proxy(self):
        self._log("+ Add proxy: edit configs/example.toml and reload")

    def _on_remove_proxy(self):
        sel = self.proxy_list.curselection()
        if sel:
            self.proxy_list.delete(sel[0])
            self._log(f"− Removed proxy #{sel[0] + 1}")

    # ─────────────────────────────────────────────
    def _poll_logs(self):
        while not self.log_queue.empty():
            try:
                msg = self.log_queue.get_nowait()
                self._log(msg)
            except queue.Empty:
                break
        self.root.after(200, self._poll_logs)

    def _log(self, msg: str):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")


def run():
    root = tk.Tk()
    TryChainGUI(root)
    root.mainloop()


if __name__ == "__main__":
    run()
