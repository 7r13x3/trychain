"""
TryChain — Logger
Colored console output using Rich.
"""
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def info(msg: str):
    console.print(f"[cyan][*][/cyan] {msg}")


def success(msg: str):
    console.print(f"[green][+][/green] {msg}")


def warn(msg: str):
    console.print(f"[yellow][!][/yellow] {msg}")


def error(msg: str):
    console.print(f"[red][-][/red] {msg}")


def debug(msg: str):
    console.print(f"[dim][.][/dim] {msg}")


def banner():
    text = """[bold cyan]
  _____          _____ _           _
 |_   _| __ _  _/ ____| |__   __ _(_)_ __
   | |  | '__| | |    | '_ \\ / _` | | '_ \\
   | |  | |    | |____| | | | (_| | | | | |
   |_|  |_|     \\_____|_| |_|\\__,_|_|_| |_|
[/bold cyan]
[dim]Cross-platform proxy chaining tool  •  v1.0.0[/dim]
"""
    console.print(text)


def chain_table(chain):
    """Print the active chain as a colored table."""
    table = Table(title="Active Chain")
    table.add_column("#", style="bold")
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("Address")
    for i, p in enumerate(chain, 1):
        table.add_row(str(i), p.name, p.type.upper(), f"{p.host}:{p.port}")
    console.print(table)


def features_table(security: dict):
    """Print the enabled security features."""
    table = Table(title="Security Layers")
    table.add_column("Layer")
    table.add_column("Status", justify="center")
    for name, enabled in security.items():
        status = "[green]● ON[/green]" if enabled else "[dim]○ OFF[/dim]"
        table.add_row(name, status)
    console.print(table)


def panel(title: str, body: str, style: str = "cyan"):
    console.print(Panel(body, title=title, border_style=style))
