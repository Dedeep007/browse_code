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

    steps.add_row("1.", "Enable [bold]Developer mode[/bold] in the top right")
    steps.add_row(
        "2.",
        f"Click [bold]Load unpacked[/bold] and select this folder:\n[cyan]{ext_path_str}[/cyan]"
        + (" [dim](Copied to clipboard!)[/dim]" if copied else ""),
    )
    steps.add_row("3.", "The Browse Code icon should now appear in your browser")

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

    # Always sync the latest extension files from the package to the data dir
    # so updates (like new icons, JS changes) propagate automatically
    ext_dest = data_dir / "extension"
    pkg_ext_dir = Path(__file__).parent / "extension"
    try:
        import shutil
        shutil.copytree(pkg_ext_dir, ext_dest, dirs_exist_ok=True)
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
    uvicorn.run(app, host=HOST, port=PORT, access_log=False)


if __name__ == "__main__":
    main()
