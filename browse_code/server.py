import os
import re
import subprocess
import difflib
import threading
import uuid
import atexit
import asyncio
import shutil
import time
import platform
import traceback
from collections import deque
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

async def check_extension_connection():
    from pathlib import Path
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich import box
        console = Console()
        
        while True:
            if not is_extension_connected():
                ext_path = str(Path.home() / ".browse_code" / "extension")
                console.print()
                console.print(
                    Panel(
                        "[bold yellow]Extension Not Connected![/bold yellow]\n\n"
                        "The server is running, but the browser extension hasn't connected.\n"
                        "To fix this:\n"
                        "  1. Ensure the [bold]Browse Code[/bold] extension is installed and enabled.\n"
                        "  2. Make sure Chrome is open and your AI chat tab is active.\n"
                        "  3. Try reloading the AI browser tab.\n"
                        "  4. If that fails, try reloading the extension in chrome://extensions/.\n\n"
                        "[dim]If you haven't installed it yet:[/dim]\n"
                        "  • Open [cyan]chrome://extensions/[/cyan]\n"
                        "  • Enable [bold]Developer Mode[/bold] (top right)\n"
                        "  • Click [bold]Load unpacked[/bold] and select this folder:\n"
                        f"    [green]{ext_path}[/green]",
                        title="[bold yellow]Warning[/bold yellow]",
                        title_align="left",
                        border_style="yellow",
                        box=box.ROUNDED,
                        padding=(1, 2),
                        expand=False
                    )
                )
            await asyncio.sleep(30)
    except asyncio.CancelledError:
        pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(check_extension_connection())
    yield
    task.cancel()


app = FastAPI(title="Agent Bridge", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.claudemcpcontent\.com|https://claude\.ai|https://gemini\.google\.com|https://chatgpt\.com|https://chat\.openai\.com|https://huggingface\.co|chrome-extension://.*|http://localhost:.*|http://127\.0\.0\.1:.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
#  Shared ANSI palette — used by the diff engine, tool banners,
#  request logger, and startup banner.
# ============================================================
C_RESET    = "\033[0m"
C_BOLD     = "\033[1m"
C_DIM      = "\033[2;90m"
C_GRAY     = "\033[90m"
C_MUTED    = "\033[38;5;245m"
C_HEADER   = "\033[1;32m"
C_GREEN    = "\033[32m"

C_OK       = "\033[1;32m"   # success / 2xx
C_ERR      = "\033[1;31m"   # error / 5xx
C_WARN     = "\033[1;33m"   # warn / 4xx
C_INFO     = "\033[1;34m"   # info

C_ADD_FG   = "\033[38;5;150m"
C_ADD_BG   = "\033[48;2;0;40;0m"
C_ADD_MARK = "\033[1;38;5;114m\033[48;2;0;40;0m"
C_ADD_NUM  = "\033[32m"
C_DEL_FG   = "\033[38;5;210m"
C_DEL_BG   = "\033[48;2;45;0;0m"
C_DEL_MARK = "\033[1;38;5;203m\033[48;2;45;0;0m"
C_DEL_NUM  = "\033[31m"

# icon + friendly label per tool tag, used by the tool-call banner
TOOL_META = {
    "view_dir":      ("📁", "View Directory"),
    "read":          ("📄", "Read File"),
    "read_lines":    ("📄", "Read Lines"),
    "write":         ("✍️ ", "Write File"),
    "patch":         ("🩹", "Patch File"),
    "search_code":   ("🔍", "Search Code"),
    "terminal_run":  ("💻", "Run Command"),
    "terminal_bg":   ("⚙️ ", "Background Process"),
    "terminal_logs": ("📜", "Process Logs"),
    "terminal_kill": ("✋", "Kill Process"),
    "cron_monitor":  ("⏰", "Monitor Process"),
}


def print_tool_start(tool_name: str, detail: str = ""):
    """Print a compact, colored banner when a tool call begins."""
    icon, label = TOOL_META.get(tool_name, ("🔧", tool_name or "Unknown Tool"))
    line = f"\n{C_HEADER}{icon} {label}{C_RESET}"
    if detail:
        detail = detail.strip().replace("\n", " ⏎ ")
        if len(detail) > 90:
            detail = detail[:89] + "…"
        line += f"  {C_DIM}{detail}{C_RESET}"
    print(line)


def print_tool_end(ok: bool, elapsed_ms: float, note: str = ""):
    """Print a compact status line when a tool call finishes."""
    if ok:
        badge = f"{C_OK}✓ done{C_RESET}"
    else:
        badge = f"{C_ERR}✗ failed{C_RESET}"
    timing = f"{C_DIM}{elapsed_ms:.0f}ms{C_RESET}"
    line = f"  {badge}  {timing}"
    if note:
        note = note.strip().replace("\n", " ⏎ ")
        if len(note) > 90:
            note = note[:89] + "…"
        line += f"  {C_MUTED}{note}{C_RESET}"
    print(line)

def load_or_create_server_key():
    key_path = os.path.expanduser("~/.browse_code_key")
    if os.path.exists(key_path):
        with open(key_path, "r") as f:
            return f.read().strip()
    key = uuid.uuid4().hex
    try:
        with open(key_path, "w") as f:
            f.write(key)
    except:
        pass
    return key

SERVER_AUTH_KEY = load_or_create_server_key()

def print_startup_banner(workspace: str, host: str, port: int):
    width = 78
    title = " Agent Bridge Backend "
    pad = width - len(title)
    left, right = pad // 2, pad - pad // 2
    print()
    print(f"{C_HEADER}╭{'─' * left}{title}{'─' * right}╮{C_RESET}")
    ws_text = f" Workspace  {workspace}"
    ws_pad = max(0, width - len(ws_text))
    print(f"{C_HEADER}│{C_RESET} {C_MUTED}Workspace{C_RESET}  {workspace}{' ' * ws_pad}{C_HEADER}│{C_RESET}")
    ep_text = f" Endpoint   http://{host}:{port}"
    ep_pad = max(0, width - len(ep_text))
    print(f"{C_HEADER}│{C_RESET} {C_MUTED}Endpoint {C_RESET}  http://{host}:{port}{' ' * ep_pad}{C_HEADER}│{C_RESET}")
    ext_label = "Extension"
    ext_status = "Waiting for connection..."
    ext_text = f" {ext_label}  {ext_status}"
    ext_pad = max(0, width - len(ext_text))
    print(f"{C_HEADER}│{C_RESET} {C_MUTED}{ext_label}{C_RESET}  {C_WARN}{ext_status}{C_RESET}{' ' * ext_pad}{C_HEADER}│{C_RESET}")
    
    key_label = "Auth Key"
    key_status = SERVER_AUTH_KEY
    key_text = f" {key_label}  {key_status}"
    key_pad = max(0, width - len(key_text))
    print(f"{C_HEADER}│{C_RESET} {C_MUTED}{key_label}{C_RESET}  {C_OK}{key_status}{C_RESET}{' ' * key_pad}{C_HEADER}│{C_RESET}")
    
    try:
        from . import __version__
        ver_label = "Version"
        ver_status = __version__
        ver_text = f" {ver_label}  {ver_status}"
        ver_pad = max(0, width - len(ver_text))
        print(f"{C_HEADER}│{C_RESET} {C_MUTED}{ver_label}{C_RESET}  {ver_status}{' ' * ver_pad}{C_HEADER}│{C_RESET}")
    except Exception:
        pass
        
    print(f"{C_HEADER}╰{'─' * width}╯{C_RESET}")
    print()


WORKSPACE_DIR = r"C:\Users\dedeep vasireddy\Downloads\test"
BACKGROUND_PROCESSES = {}

# Extension heartbeat tracking
_last_extension_ping = None
_HEARTBEAT_TIMEOUT = 10  # seconds — extension is "connected" if pinged within this window

ACTIVE_SESSION_TOKENS = set()

def verify_server_key(x_server_key: str):
    if not x_server_key or x_server_key != SERVER_AUTH_KEY:
        raise HTTPException(status_code=401, detail="Invalid server key. Please configure the correct key in the extension popup.")

def verify_session(x_session_token: str = Header(None)):
    if not ACTIVE_SESSION_TOKENS:
        raise HTTPException(status_code=401, detail="No active agent session initialized.")
    if x_session_token not in ACTIVE_SESSION_TOKENS:
        raise HTTPException(status_code=401, detail="Invalid session token.")

@app.post("/extension/init")
async def init_session(x_server_key: str = Header(None)):
    verify_server_key(x_server_key)
    token = uuid.uuid4().hex
    ACTIVE_SESSION_TOKENS.add(token)
    print(f"\n{C_OK}[+] New agent session initialized.{C_RESET}")
    return {"token": token}

def is_extension_connected():
    if _last_extension_ping is None:
        return False
    return (time.time() - _last_extension_ping) < _HEARTBEAT_TIMEOUT

@app.get("/extension/ping")
async def extension_ping(v: str = None, x_session_token: str = Header(None)):
    global _last_extension_ping
    
    if (not ACTIVE_SESSION_TOKENS) or (x_session_token in ACTIVE_SESSION_TOKENS):
        was_connected = is_extension_connected()
        _last_extension_ping = time.time()
        if not was_connected:
            print(f"\n{C_OK}[+] Extension connected{C_RESET}")
            
    return {"status": "ok", "key": SERVER_AUTH_KEY}

class ImageModel(BaseModel):
    base64: str

@app.post("/extension/save-image")
async def save_image(data: ImageModel, x_session_token: str = Header(None), x_server_key: str = Header(None)):
    verify_server_key(x_server_key)
    verify_session(x_session_token)
    import base64
    try:
        header, encoded = data.base64.split(",", 1)
        ext = "png"
        if "jpeg" in header or "jpg" in header:
            ext = "jpg"
        elif "webp" in header:
            ext = "webp"
        elif "svg" in header:
            ext = "svg"
            
        image_data = base64.b64decode(encoded)
        creations_dir = os.path.join(WORKSPACE_DIR, "agent-creations")
        os.makedirs(creations_dir, exist_ok=True)
        
        filename = f"generated_{uuid.uuid4().hex[:8]}.{ext}"
        filepath = os.path.join(creations_dir, filename)
        
        with open(filepath, "wb") as f:
            f.write(image_data)
            
        rel_path = f"agent-creations/{filename}"
        print(f"\n{C_OK}[+] Saved AI image to {rel_path}{C_RESET}")
        return {"status": "ok", "path": rel_path}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def cleanup_background_processes():
    print(f"\n{C_WARN}⏻  Shutting down — cleaning up background processes...{C_RESET}")
    for pid, data in BACKGROUND_PROCESSES.items():
        if data['status'] == 'running':
            try:
                proc = data['process']
                if platform.system() == "Windows":
                    subprocess.run(f"taskkill /F /T /PID {proc.pid}", shell=True, capture_output=True)
                else:
                    proc.terminate()
            except:
                pass

atexit.register(cleanup_background_processes)


@app.middleware("http")
async def request_logger(request: Request, call_next):
    """Compact single-line request logger, replacing uvicorn's default access log."""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000

    status = response.status_code
    if status < 300:
        color = C_OK
    elif status < 500:
        color = C_WARN
    else:
        color = C_ERR

    # The /extension/run-tool endpoint already prints its own detailed
    # banner + result, so skip the generic line there to avoid duplication.
    # Also skip /extension/ping to avoid flooding the log with heartbeats.
    if request.url.path not in ("/extension/run-tool", "/extension/ping"):
        print(f"{C_DIM}→{C_RESET} {request.method} {request.url.path}  "
              f"{color}{status}{C_RESET}  {C_DIM}{elapsed_ms:.0f}ms{C_RESET}")

    return response


# ============================================================
#  TUI Block Diff Engine (v3) — single-gutter, full-width highlight
#  style, matching editor-style inline diffs (Claude Code / VS Code).
# ============================================================


def _terminal_width(default: int = 72, cap: int = 88) -> int:
    # NOTE: this process's stdout is usually not a real TTY (it's a FastAPI
    # server, often piped/redirected), so shutil.get_terminal_size() falls
    # back to `default` rather than reflecting the actual viewer width. Keep
    # `default` conservative — if it's too wide, the padded highlight bar
    # wraps in the viewer and bleeds color onto the next visual line.
    try:
        size = shutil.get_terminal_size(fallback=(default, 20))
        cols = size.columns
        # A fallback tuple and a "real" detected size look identical here,
        # so only trust an unusually small detected width; otherwise stay
        # conservative rather than risk wrapping.
        if cols <= 0:
            cols = default
    except Exception:
        cols = default
    return max(40, min(cols, cap, default))


def _clip(text: str, max_len: int) -> str:
    if max_len <= 1:
        return text[:max_len]
    if len(text) > max_len:
        return text[: max_len - 1] + "…"
    return text


def print_terminal_diff(filepath: str, old_content: str, new_content: str, context_lines: int = 2,
                         large_line_threshold: int = 300, large_change_threshold: int = 120):
    """Render a single-gutter, full-width-highlight diff (Claude Code TUI style).

    For large diffs, unchanged/context lines are suppressed entirely (only a
    collapsed "N unchanged lines" marker is shown) to keep the output readable.
    """
    old_lines = old_content.splitlines()
    new_lines = new_content.splitlines()
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
    opcodes = matcher.get_opcodes()

    additions = sum(j2 - j1 for tag, i1, i2, j1, j2 in opcodes if tag in ("insert", "replace"))
    deletions = sum(i2 - i1 for tag, i1, i2, j1, j2 in opcodes if tag in ("delete", "replace"))
    is_new_file = old_content == "" and new_content != ""

    # Large diffs: drop context lines entirely, show changed lines only.
    total_lines = max(len(old_lines), len(new_lines))
    total_changes = additions + deletions
    if total_lines > large_line_threshold or total_changes > large_change_threshold:
        context_lines = 0

    width = _terminal_width()
    num_width = max(len(str(max(len(old_lines), len(new_lines), 1))), 2)
    content_width = max(10, width - num_width - 6)  # " N  m code" + safety margin

    # ---- Header: "filename  +N -N" -----------------------------
    tag_label = " (new file)" if is_new_file else ""
    print()
    header = f"{C_HEADER}{filepath}{C_RESET}{C_DIM}{tag_label}{C_RESET}"
    stats = f"  {C_ADD_NUM}+{additions}{C_RESET} {C_DEL_NUM}-{deletions}{C_RESET}"
    print(f"{header}{stats}")
    print(f"{C_GRAY}{'─' * width}{C_RESET}")

    if not opcodes or (len(opcodes) == 1 and opcodes[0][0] == "equal"):
        print(f"{C_DIM}  (no changes){C_RESET}\n")
        return

    def row(number, marker, text, bg="", fg="", mark_style=""):
        num_s = f"{number:>{num_width}}" if number is not None else " " * num_width
        body = _clip(text, content_width)
        if bg:
            # pad body so the background color fills the full row width
            padded = body.ljust(content_width)
            m = mark_style if mark_style else fg
            print(f"{bg}{fg} {num_s} {m}{marker}{fg} {padded} {C_RESET}")
        else:
            print(f"{C_MUTED} {num_s} {C_GRAY}{marker}{C_RESET}  {body}")

    def gap_marker(hidden):
        print(f"{C_DIM}   ⋮  {hidden} unchanged line{'s' if hidden != 1 else ''}{C_RESET}")

    new_ln = 1  # running "position in final file" counter, drives the single gutter

    for tag, i1, i2, j1, j2 in opcodes:
        if tag == "equal":
            block_len = i2 - i1
            if block_len == 0:
                continue

            if context_lines <= 0:
                # Large diff mode: skip unchanged lines entirely, just show the gap.
                new_ln += block_len
                gap_marker(block_len)
                continue

            if block_len > context_lines * 2:
                for k in range(context_lines):
                    row(new_ln, " ", old_lines[i1 + k])
                    new_ln += 1
                hidden = block_len - context_lines * 2
                new_ln += hidden  # skip numbering for hidden lines
                gap_marker(hidden)
                for k in range(block_len - context_lines, block_len):
                    row(new_ln, " ", old_lines[i1 + k])
                    new_ln += 1
            else:
                for k in range(block_len):
                    row(new_ln, " ", old_lines[i1 + k])
                    new_ln += 1
            continue

        if tag in ("delete", "replace"):
            for i in range(i1, i2):
                row(new_ln, "-", old_lines[i], bg=C_DEL_BG, fg=C_DEL_FG, mark_style=C_DEL_MARK)

        if tag in ("insert", "replace"):
            for j in range(j1, j2):
                row(new_ln, "+", new_lines[j], bg=C_ADD_BG, fg=C_ADD_FG, mark_style=C_ADD_MARK)
                new_ln += 1


def strip_ansi(text: str) -> str:
    ansi_escape = re.compile(r'\x1b\[([0-9]{1,3}(;[0-9]{1,3})*)?[m|K]')
    return ansi_escape.sub('', text)

def truncate_output(text: str, max_chars=12000) -> str:
    if len(text) > max_chars:
        return text[:max_chars] + f"\n\n...[OUTPUT TRUNCATED]"
    return text

def stream_process_output(pid: str, process: subprocess.Popen):
    try:
        for line in iter(process.stdout.readline, ''):
            BACKGROUND_PROCESSES[pid]['logs'].append(line)
    except Exception as e:
        BACKGROUND_PROCESSES[pid]['logs'].append(f"\n[Stream Error: {str(e)}]\n")
    finally:
        process.stdout.close()
        BACKGROUND_PROCESSES[pid]['status'] = 'exited'

def secure_path(path: str) -> str:
    filepath = os.path.abspath(os.path.join(WORKSPACE_DIR, path))
    if not filepath.startswith(os.path.abspath(WORKSPACE_DIR)):
        raise HTTPException(status_code=400, detail="Security Error: Path traversal detected.")
    return filepath

class WorkspaceModel(BaseModel):
    path: str

class ToolModel(BaseModel):
    tool_call: str

@app.post("/set-workspace")
async def set_workspace(data: WorkspaceModel, x_server_key: str = Header(None)):
    verify_server_key(x_server_key)
    global WORKSPACE_DIR
    new_path = data.path.strip()
    if new_path and os.path.exists(new_path):
        WORKSPACE_DIR = new_path
        print(f"\n[Workspace Updated]: {WORKSPACE_DIR}\n")
        return {"status": "success", "workspace": WORKSPACE_DIR}
    raise HTTPException(status_code=400, detail="Invalid workspace path")

@app.get("/status")
async def get_status(x_server_key: str = Header(None)):
    verify_server_key(x_server_key)
    active_procs = []
    for pid, data in BACKGROUND_PROCESSES.items():
        recent_logs = list(data['logs'])[-5:] 
        active_procs.append({
            "pid": pid,
            "status": data['status'],
            "logs": strip_ansi("".join(recent_logs))
        })
    return {
        "workspace": WORKSPACE_DIR,
        "processes": active_procs
    }

def _identify_tool(tool_raw: str):
    """Parse which tool tag was used and build a short human-readable detail string."""
    m = re.search(r"<tool='view_dir'>(.*?)</tool>", tool_raw, re.DOTALL)
    if m:
        return "view_dir", (m.group(1).strip() or ".")

    m = re.search(r"<tool='read'>(.*?)</tool>", tool_raw, re.DOTALL)
    if m:
        return "read", m.group(1).strip()

    m = re.search(r"<tool='write'\s+path='(.*?)'>(.*?)</tool>", tool_raw, re.DOTALL)
    if m:
        return "write", m.group(1).strip()

    m = re.search(r"<tool='patch'\s+path='(.*?)'>\s*<search>(.*?)</search>\s*<replace>(.*?)</replace>\s*</tool>", tool_raw, re.DOTALL)
    if m:
        return "patch", m.group(1).strip()

    m = re.search(r"<tool='search_code'\s+query='(.*?)'>(.*?)</tool>", tool_raw, re.DOTALL)
    if m:
        return "search_code", f"\"{m.group(1).strip()}\""

    m = re.search(r"<tool='read_lines'\s+path='(.*?)'\s+start='(\d+)'\s+end='(\d+)'></tool>", tool_raw, re.DOTALL)
    if m:
        return "read_lines", f"{m.group(1).strip()}  L{m.group(2)}-{m.group(3)}"

    m = re.search(r"<tool='terminal_run'>(.*?)</tool>", tool_raw, re.DOTALL)
    if m:
        return "terminal_run", m.group(1).strip()

    m = re.search(r"<tool='terminal_bg'>(.*?)</tool>", tool_raw, re.DOTALL)
    if m:
        return "terminal_bg", m.group(1).strip()

    m = re.search(r"<tool='terminal_logs'\s+pid='(.*?)'></tool>", tool_raw, re.DOTALL)
    if m:
        return "terminal_logs", f"pid={m.group(1).strip()}"

    m = re.search(r"<tool='terminal_kill'\s+pid='(.*?)'></tool>", tool_raw, re.DOTALL)
    if m:
        return "terminal_kill", f"pid={m.group(1).strip()}"

    m = re.search(r"<tool='cron_monitor'\s+pid='(.*?)'\s+delay='(\d+)'></tool>", tool_raw, re.DOTALL)
    if m:
        return "cron_monitor", f"pid={m.group(1).strip()}  delay={m.group(2)}s"

    return None, ""


def _short_preview(output: str, max_len: int = 90) -> str:
    if not output:
        return ""
    first_line = str(output).splitlines()[0] if output else ""
    if len(first_line) > max_len:
        first_line = first_line[: max_len - 1] + "…"
    return first_line


@app.post("/extension/run-tool")
async def run_tool(data: ToolModel, x_session_token: str = Header(None), x_server_key: str = Header(None)):
    verify_server_key(x_server_key)
    verify_session(x_session_token)
    global WORKSPACE_DIR
    tool_raw = data.tool_call

    tool_name, detail = _identify_tool(tool_raw)
    print_tool_start(tool_name, detail)
    start = time.perf_counter()

    view_match = re.search(r"<tool='view_dir'>(.*?)</tool>", tool_raw, re.DOTALL)
    read_match = re.search(r"<tool='read'>(.*?)</tool>", tool_raw, re.DOTALL)
    write_match = re.search(r"<tool='write'\s+path='(.*?)'>(.*?)</tool>", tool_raw, re.DOTALL)
    patch_match = re.search(r"<tool='patch'\s+path='(.*?)'>\s*<search>(.*?)</search>\s*<replace>(.*?)</replace>\s*</tool>", tool_raw, re.DOTALL)
    search_code_match = re.search(r"<tool='search_code'\s+query='(.*?)'>(.*?)</tool>", tool_raw, re.DOTALL)
    read_lines_match = re.search(r"<tool='read_lines'\s+path='(.*?)'\s+start='(\d+)'\s+end='(\d+)'></tool>", tool_raw, re.DOTALL)
    term_run_match = re.search(r"<tool='terminal_run'>(.*?)</tool>", tool_raw, re.DOTALL)
    term_bg_match = re.search(r"<tool='terminal_bg'>(.*?)</tool>", tool_raw, re.DOTALL)
    term_logs_match = re.search(r"<tool='terminal_logs'\s+pid='(.*?)'></tool>", tool_raw, re.DOTALL)
    term_kill_match = re.search(r"<tool='terminal_kill'\s+pid='(.*?)'></tool>", tool_raw, re.DOTALL)
    cron_match = re.search(r"<tool='cron_monitor'\s+pid='(.*?)'\s+delay='(\d+)'></tool>", tool_raw, re.DOTALL)

    try:
        if view_match:
            sub_dir = view_match.group(1).strip()
            target_dir = secure_path(sub_dir) if sub_dir else WORKSPACE_DIR
            tree = []
            for root, dirs, files in os.walk(target_dir):
                for f in files:
                    rel_path = os.path.relpath(os.path.join(root, f), WORKSPACE_DIR)
                    if not any(part.startswith('.') or part == 'node_modules' or part == '__pycache__' for part in rel_path.split(os.sep)):
                        tree.append(rel_path)
            result = {"output": truncate_output("\n".join(tree) if tree else "Directory is empty.")}

        elif read_match:
            filepath = secure_path(read_match.group(1).strip())
            if not os.path.exists(filepath):
                result = {"output": "Error: File not found."}
            else:
                with open(filepath, 'r', encoding='utf-8') as f:
                    result = {"output": truncate_output(f.read())}

        elif read_lines_match:
            filepath = secure_path(read_lines_match.group(1).strip())
            start_line, end_line = int(read_lines_match.group(2)), int(read_lines_match.group(3))
            if not os.path.exists(filepath):
                result = {"output": "Error: File not found."}
            else:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                chunk = lines[max(0, start_line-1) : end_line]
                formatted_chunk = "".join([f"{i+start_line}: {line}" for i, line in enumerate(chunk)])
                result = {"output": truncate_output(f"--- Lines {start_line} to {end_line} ---\n{formatted_chunk}")}

        elif search_code_match:
            query, sub_dir = search_code_match.group(1).strip(), search_code_match.group(2).strip()
            target_dir = secure_path(sub_dir) if sub_dir else WORKSPACE_DIR
            results = []
            for root, dirs, files in os.walk(target_dir):
                if any(part.startswith('.') or part == 'node_modules' for part in root.split(os.sep)): continue
                for f in files:
                    filepath = os.path.join(root, f)
                    rel_path = os.path.relpath(filepath, WORKSPACE_DIR)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as file:
                            for line_num, line in enumerate(file, 1):
                                if query in line: results.append(f"{rel_path}:{line_num}: {line.strip()}")
                    except: pass
            result = {"output": truncate_output("\n".join(results) if results else "No matches found.")}

        elif write_match:
            path = write_match.group(1).strip()
            filepath = secure_path(path)
            content = re.sub(r'^```[a-zA-Z]*\n|\n```$', '', write_match.group(2).strip(), flags=re.MULTILINE)

            old_content = ""
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    old_content = f.read()

            print_terminal_diff(path, old_content, content)

            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            result = {"output": f"Successfully wrote {path}"}

        elif patch_match:
            path = patch_match.group(1).strip()
            filepath = secure_path(path)
            search = re.sub(r'^```[a-zA-Z]*\n|\n```$', '', patch_match.group(2).strip('\n'), flags=re.MULTILINE)
            replace = re.sub(r'^```[a-zA-Z]*\n|\n```$', '', patch_match.group(3).strip('\n'), flags=re.MULTILINE)

            if not os.path.exists(filepath):
                result = {"output": "Error: File not found."}
            else:
                with open(filepath, 'r', encoding='utf-8') as f:
                    original = f.read()
                if search not in original:
                    result = {"output": "Error: Search block not found exactly as written."}
                else:
                    new_content = original.replace(search, replace, 1)
                    print_terminal_diff(path, original, new_content)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    result = {"output": f"Patch applied successfully to {path}."}

        elif term_run_match:
            cmd = term_run_match.group(1).strip()
            env = os.environ.copy()
            env["FORCE_COLOR"] = "true"
            
            pid = str(uuid.uuid4())[:8]
            process = subprocess.Popen(cmd, shell=True, cwd=WORKSPACE_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
            BACKGROUND_PROCESSES[pid] = {'process': process, 'logs': deque(maxlen=500), 'status': 'running'}
            threading.Thread(target=stream_process_output, args=(pid, process), daemon=True).start()

            # Wait up to 5 seconds to see if it finishes quickly
            start_time = time.time()
            while time.time() - start_time < 5.0:
                if process.poll() is not None:
                    break
                await asyncio.sleep(0.1)

            # Give the log thread a tiny bit of time to flush if it just exited
            await asyncio.sleep(0.1)
            
            logs = "".join(list(BACKGROUND_PROCESSES[pid]['logs']))
            
            if process.poll() is not None:
                # Process finished quickly, treat as normal terminal_run
                try:
                    del BACKGROUND_PROCESSES[pid]
                except KeyError:
                    pass
                output = strip_ansi(logs) if logs.strip() else "Executed."
                result = {"output": truncate_output(output)}
            else:
                # Still running, auto-background it!
                partial = strip_ansi(logs)
                result = {"output": truncate_output(f"Status: ONGOING (Process auto-backgrounded after 5s)\nPID: {pid}\n\nOutput so far:\n{partial}\n\nInstruction: This process is still running. Use terminal_logs <pid='{pid}'> to check on it later, or terminal_kill to stop it.")}

        elif term_bg_match:
            cmd = term_bg_match.group(1).strip()
            pid = str(uuid.uuid4())[:8]
            env = os.environ.copy()
            env["FORCE_COLOR"] = "true"
            process = subprocess.Popen(cmd, shell=True, cwd=WORKSPACE_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
            BACKGROUND_PROCESSES[pid] = {'process': process, 'logs': deque(maxlen=500), 'status': 'running'}
            threading.Thread(target=stream_process_output, args=(pid, process), daemon=True).start()
            result = {"output": f"Process started. PID: {pid}. Use terminal_logs to view."}

        elif term_logs_match:
            pid = term_logs_match.group(1).strip()
            if pid not in BACKGROUND_PROCESSES:
                result = {"output": "Error: PID not found."}
            else:
                logs = "".join(list(BACKGROUND_PROCESSES[pid]['logs'])) or "No output yet."
                result = {"output": truncate_output(strip_ansi(f"STATUS: {BACKGROUND_PROCESSES[pid]['status']}\nLOGS:\n{logs}"))}

        elif term_kill_match:
            pid = term_kill_match.group(1).strip()
            if pid in BACKGROUND_PROCESSES:
                proc = BACKGROUND_PROCESSES[pid]['process']
                if platform.system() == "Windows":
                    subprocess.run(f"taskkill /F /T /PID {proc.pid}", shell=True, capture_output=True)
                else:
                    proc.terminate()
                BACKGROUND_PROCESSES[pid]['status'] = 'killed'
                result = {"output": f"Process {pid} terminated."}
            else:
                result = {"output": "Error: PID not found."}

        elif cron_match:
            pid = cron_match.group(1).strip()
            delay = int(cron_match.group(2).strip())
            if pid not in BACKGROUND_PROCESSES:
                result = {"output": "Error: PID not found."}
            else:
                safe_delay = min(delay, 120)
                await asyncio.sleep(safe_delay)
                logs = "".join(list(BACKGROUND_PROCESSES[pid]['logs'])) or "No output yet."
                status = BACKGROUND_PROCESSES[pid]['status']
                result = {"output": truncate_output(strip_ansi(f"[WOKE UP AFTER {safe_delay}s]\nSTATUS: {status}\nLOGS:\n{logs}"))}

        else:
            result = {"output": "Error: Unrecognized tool tag."}

    except Exception as e:
        result = {"output": f"Error: {str(e)}"}

    elapsed_ms = (time.perf_counter() - start) * 1000
    output_text = str(result.get("output", ""))
    ok = not output_text.startswith("Error")
    print_tool_end(ok, elapsed_ms, note=_short_preview(output_text))
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5505, access_log=False)