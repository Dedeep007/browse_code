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

ASCII_BROWSE = [
    "██████╗ ██████╗  ██████╗ ██╗    ██╗███████╗███████╗    ",
    "██╔══██╗██╔══██╗██╔═══██╗██║    ██║██╔════╝██╔════╝   ",
    "██████╔╝██████╔╝██║   ██║██║ █╗ ██║███████╗█████╗     ",
    "██╔══██╗██╔══██╗██║   ██║██║███╗██║╚════██║██╔══╝     ",
    "██████╔╝██║  ██║╚██████╔╝╚███╔███╔╝███████║███████╗██╗",
    "╚═════╝ ╚═╝  ╚═╝ ╚═════╝  ╚══╝╚══╝ ╚══════╝╚══════╝╚═╝ "
]

ASCII_CODE = [
    "██████╗ ██████╗ ██████╗ ███████╗",
    "██╔════╝██╔═══██╗██╔══██╗██╔════╝",
    "██║     ██║   ██║██║  ██║█████╗  ",
    "██║     ██║   ██║██║  ██║██╔══╝  ",
    "╚██████╗╚██████╔╝██████╔╝███████╗",
    "╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝"
]


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
    console.print()
    for b, c in zip(ASCII_BROWSE, ASCII_CODE):
        console.print(f"[bold green]{b}[/bold green][bold red]{c}[/bold red]")


def setup_extension():
    """First-time setup: open Chrome, guide the user."""
    data_dir = get_data_dir()
    ext_dest = data_dir / "extension"

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

    ext_path_str = str(ext_dest)
    console.print()
    console.print(f"  [green]Extension ready at:[/green] [bold]{ext_path_str}[/bold]")
    console.print()

    # Copy path to clipboard
    copied = copy_to_clipboard(ext_path_str)

    # Open chrome://extensions (for Chromium browsers)
    console.print("  [green]Opening extensions page (for Chrome/Edge)...[/green]")
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

    steps.add_row("", "[cyan][bold]For Chrome / Edge:[/bold][/cyan]")
    steps.add_row("1.", "Enable [bold]Developer mode[/bold] in the top right")
    steps.add_row(
        "2.",
        f"Click [bold]Load unpacked[/bold] and select:\n[cyan]{ext_path_str}[/cyan]"
        + (" [dim](Copied!)[/dim]" if copied else ""),
    )
    steps.add_row("", "")
    steps.add_row("", "[cyan][bold]For Firefox:[/bold][/cyan]")
    steps.add_row("1.", "Open [bold]about:debugging[/bold] and click [bold]This Firefox[/bold]")
    steps.add_row("2.", f"Click [bold]Load Temporary Add-on[/bold] and select [bold]manifest.json[/bold] inside:\n[cyan]{ext_path_str}[/cyan]")

    console.print(
        Panel(
            steps,
            title="[bold]Installation Steps[/bold]",
            border_style="blue",
            box=box.ROUNDED,
            padding=(1, 2),
            expand=False,
        )
    )

    # Ask user to confirm they installed it
    Confirm.ask("\n  [yellow]Did you finish installing it?[/yellow]", default=True)

    # Create marker file
    marker = data_dir / ".installed"
    marker.touch()

    return True


def print_server_header():
    """Print the server startup header."""
    info = Table.grid(padding=(0, 2))
    info.add_column(style="dim", justify="right")
    info.add_column()

    from .server import SERVER_AUTH_KEY
    from . import __version__
    
    info.add_row("Endpoint", f"[bold]http://{HOST}:{PORT}[/bold]")
    info.add_row("Extension", "[yellow]Waiting for connection...[/yellow]")
    info.add_row("Auth Key", f"[bold cyan]{SERVER_AUTH_KEY}[/bold cyan]")
    info.add_row("Version", f"[dim]{__version__}[/dim]")
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

    # Create browser-specific extension folders to resolve MV3 manifest conflicts:
    # Chrome MV3 rejects 'scripts', Firefox MV3 disables 'service_worker'
    ext_chrome = data_dir / "extension_chrome"
    ext_firefox = data_dir / "extension_firefox"
    pkg_ext_dir = Path(__file__).parent / "extension"
    try:
        import shutil
        import json
        
        # Chrome extension
        shutil.copytree(pkg_ext_dir, ext_chrome, dirs_exist_ok=True)
        # Firefox extension
        shutil.copytree(pkg_ext_dir, ext_firefox, dirs_exist_ok=True)
        
        # Patch Firefox manifest
        ff_manifest_path = ext_firefox / "manifest.json"
        with open(ff_manifest_path, "r", encoding="utf-8") as f:
            ff_manifest = json.load(f)
        
        # Replace service_worker with scripts for Firefox
        if "background" in ff_manifest and "service_worker" in ff_manifest["background"]:
            ff_manifest["background"]["scripts"] = [ff_manifest["background"]["service_worker"]]
            del ff_manifest["background"]["service_worker"]
            
        with open(ff_manifest_path, "w", encoding="utf-8") as f:
            json.dump(ff_manifest, f, indent=2)
            
    except Exception:
        pass

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
    import sys
    import asyncio
    
    if sys.platform == "win32":
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception:
            pass

    uvicorn.run(app, host=HOST, port=PORT, access_log=False)


if __name__ == "__main__":
    main()
