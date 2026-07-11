import os
import sys
import shutil
import platform
import subprocess
import webbrowser
from pathlib import Path

# ── Rich TUI imports ──────────────────────────────────────
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box

console = Console()

PORT = 5505
HOST = "127.0.0.1"

ASCII_BANNER = r"""
██████╗ ██████╗  ██████╗ ██╗    ██╗███████╗███████╗    ██████╗ ██████╗ ██████╗ ███████╗
██╔══██╗██╔══██╗██╔═══██╗██║    ██║██╔════╝██╔════╝   ██╔════╝██╔═══██╗██╔══██╗██╔════╝
██████╔╝██████╔╝██║   ██║██║ █╗ ██║███████╗█████╗     ██║     ██║   ██║██║  ██║█████╗  
██╔══██╗██╔══██╗██║   ██║██║███╗██║╚════██║██╔══╝     ██║     ██║   ██║██║  ██║██╔══╝  
██████╔╝██║  ██║╚██████╔╝╚███╔███╔╝███████║███████╗██╗╚██████╗╚██████╔╝██████╔╝███████╗
╚═════╝ ╚═╝  ╚═╝ ╚═════╝  ╚══╝╚══╝ ╚══════╝╚══════╝╚═╝ ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝
"""


def get_data_dir():
    """Return ~/.browse_code, creating it if needed."""
    data_dir = Path.home() / ".browse_code"
    data_dir.mkdir(exist_ok=True)
    return data_dir


def copy_to_clipboard(text):
    """Copy text to the system clipboard (cross-platform)."""
    try:
        system = platform.system()
        if system == "Windows":
            subprocess.run("clip", input=text.encode("utf-8"), check=True)
        elif system == "Darwin":
            subprocess.run("pbcopy", input=text.encode("utf-8"), check=True)
        else:
            try:
                subprocess.run(
                    ["xclip", "-selection", "clipboard"],
                    input=text.encode("utf-8"),
                    check=True,
                )
            except FileNotFoundError:
                subprocess.run(
                    ["xsel", "--clipboard", "--input"],
                    input=text.encode("utf-8"),
                    check=True,
                )
        return True
    except Exception:
        return False


def print_banner():
    """Print the Browse Code ASCII art banner."""
    console.print(f"[bold green]{ASCII_BANNER}[/bold green]")


def setup_extension():
    """First-time setup: extract extension, open Chrome, guide the user."""
    data_dir = get_data_dir()
    ext_dest = data_dir / "extension"
    pkg_ext_dir = Path(__file__).parent / "extension"

    print_banner()
    console.print(
        Panel(
            "[bold]First Time Setup[/bold]\n\n"
            "Browse Code needs a Chrome extension to connect\n"
            "your browser to the local server.",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
            expand=False,
        )
    )

    if not Confirm.ask("\n  Do you want to set up the extension now?", default=True):
        console.print("  [dim]Skipped. Re-run 'bc' anytime to set it up.[/dim]")
        return False

    # Extract extension files
    console.print()
    with console.status("[green]Extracting extension files...[/green]", spinner="dots"):
        if ext_dest.exists():
            shutil.rmtree(ext_dest)
        shutil.copytree(pkg_ext_dir, ext_dest)

    ext_path_str = str(ext_dest)
    console.print(f"  [green]Extracted to:[/green] [bold]{ext_path_str}[/bold]")
    console.print()

    # Copy path to clipboard
    copied = copy_to_clipboard(ext_path_str)

    # Open chrome://extensions
    console.print("  [green]Opening Chrome extensions page...[/green]")
    webbrowser.open("chrome://extensions/")

    # Setup instructions
    steps = Table(
        show_header=False,
        box=box.SIMPLE,
        padding=(0, 2),
        show_edge=False,
    )
    steps.add_column("step", style="bold green", width=4)
    steps.add_column("instruction")

    steps.add_row("1.", 'Enable [bold]"Developer mode"[/bold] toggle (top-right corner)')
    steps.add_row("2.", 'Click [bold]"Load unpacked"[/bold]')
    if copied:
        steps.add_row("3.", "Paste the path [green](already copied to your clipboard)[/green]")
    else:
        steps.add_row("3.", f"Select this folder: [bold]{ext_path_str}[/bold]")

    console.print()
    console.print(
        Panel(
            steps,
            title="[bold green]Quick Setup[/bold green]",
            title_align="left",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 1),
            expand=False,
        )
    )
    console.print()

    Prompt.ask("  Press [bold]Enter[/bold] after you've loaded the extension")

    # Mark as installed
    marker = data_dir / ".installed"
    marker.touch()

    console.print("  [bold green]Extension setup complete![/bold green]")
    return True


def print_server_header():
    """Print the server status panel before starting."""
    info = Table(show_header=False, box=None, padding=(0, 1), show_edge=False)
    info.add_column("key", style="dim", width=12)
    info.add_column("value")

    info.add_row("Endpoint", f"[bold]http://{HOST}:{PORT}[/bold]")
    info.add_row("Extension", "[yellow]Waiting for connection...[/yellow]")
    info.add_row("Status", "[bold green]Running[/bold green]")

    console.print(
        Panel(
            info,
            title="[bold green]Agent Bridge Backend[/bold green]",
            title_align="center",
            subtitle="[dim]Press Ctrl+C to stop[/dim]",
            subtitle_align="right",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
            expand=False,
        )
    )
    console.print()


def main():
    data_dir = get_data_dir()
    marker = data_dir / ".installed"

    if not marker.exists():
        result = setup_extension()
        if not result:
            return
    else:
        print_banner()

    print_server_header()

    try:
        from .server import app
    except ImportError:
        from server import app

    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT, access_log=False)


if __name__ == "__main__":
    main()
