import os
import sys
import shutil
import subprocess
from pathlib import Path

def get_data_dir():
    home = Path.home()
    data_dir = home / ".browse_code"
    data_dir.mkdir(exist_ok=True)
    return data_dir

def install_extension():
    data_dir = get_data_dir()
    installed_marker = data_dir / ".installed"
    ext_dest = data_dir / "extension"

    # Copy extension files from package to ~/.browse_code/extension
    pkg_ext_dir = Path(__file__).parent / "extension"
    
    if not installed_marker.exists():
        ans_allow = input("Do you allow browse_code to install its Chrome extension? (y/n): ")
        if ans_allow.lower() != 'y':
            print("Extension installation skipped.")
            return

        print("Installing browse_code extension...")
        if ext_dest.exists():
            shutil.rmtree(ext_dest)
        shutil.copytree(pkg_ext_dir, ext_dest)
        
        print("\n========================================================")
        print("Extension files copied to: ", ext_dest)
        print("To load the extension in Chrome:")
        print("1. Open Chrome and navigate to chrome://extensions/")
        print("2. Enable 'Developer mode' at the top right")
        print("3. Click 'Load unpacked' and select the folder:")
        print(f"   {ext_dest}")
        print("========================================================\n")
        
        ans = input("Do you want me to try launching Chrome with this extension now? (y/n): ")
        if ans.lower() == 'y':
            # Attempt to launch chrome
            # On Windows:
            chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            if not os.path.exists(chrome_path):
                chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
            if os.path.exists(chrome_path):
                subprocess.Popen([chrome_path, f"--load-extension={ext_dest}"])
            else:
                print("Could not find Chrome executable automatically.")
        
        installed_marker.touch()
    else:
        # Already installed, check if files are still there, if not recopy
        if not ext_dest.exists():
            shutil.copytree(pkg_ext_dir, ext_dest)

def main():
    install_extension()
    
    print("\nStarting AI session server...\n")
    # Now we need to start the FastAPI server.
    # The original server.py is in the same package
    try:
        from .server import app
    except ImportError:
        # Fallback if run directly during dev
        from server import app
        
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5505, access_log=False)

if __name__ == "__main__":
    main()
