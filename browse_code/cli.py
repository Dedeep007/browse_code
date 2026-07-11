import os
import sys
import shutil
import platform
import subprocess
import webbrowser
from pathlib import Path


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
            # Linux — try xclip, fall back to xsel
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


def setup_extension():
    """First-time setup: extract extension, open Chrome, guide the user."""
    data_dir = get_data_dir()
    ext_dest = data_dir / "extension"
    pkg_ext_dir = Path(__file__).parent / "extension"

    print()
    print("=" * 60)
    print("  Browse Code - First Time Setup")
    print("=" * 60)
    print()
    print("Browse Code needs a Chrome extension to connect your")
    print("browser to the local server.")
    print()

    ans = input("Do you want to set up the extension now? (y/n): ")
    if ans.strip().lower() != "y":
        print("Skipped. You can re-run 'bc' anytime to set it up.")
        return False

    # Extract extension files
    print()
    print("Extracting extension files...")
    if ext_dest.exists():
        shutil.rmtree(ext_dest)
    shutil.copytree(pkg_ext_dir, ext_dest)

    ext_path_str = str(ext_dest)
    print(f"  Extension extracted to: {ext_path_str}")
    print()

    # Copy path to clipboard
    copied = copy_to_clipboard(ext_path_str)

    # Open chrome://extensions
    print("Opening Chrome extensions page...")
    webbrowser.open("chrome://extensions/")

    print()
    print("-" * 60)
    print("  QUICK SETUP (one-time, takes 30 seconds):")
    print("-" * 60)
    print('  1. Enable "Developer mode" toggle (top-right corner)')
    print('  2. Click "Load unpacked"')
    if copied:
        print("  3. Paste the path (already copied to your clipboard)")
    else:
        print(f"  3. Select this folder: {ext_path_str}")
    print("-" * 60)
    print()

    input("Press Enter after you've loaded the extension...")

    # Mark as installed
    marker = data_dir / ".installed"
    marker.touch()

    print()
    print("Extension setup complete!")
    return True


def main():
    data_dir = get_data_dir()
    marker = data_dir / ".installed"

    if not marker.exists():
        result = setup_extension()
        if not result:
            return

    print()
    print("=" * 60)
    print("  Browse Code")
    print("=" * 60)
    print()
    print("Starting server...")
    print()

    try:
        from .server import app
    except ImportError:
        from server import app

    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5505, access_log=False)


if __name__ == "__main__":
    main()
