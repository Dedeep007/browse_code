# Browse Code

![PyPI version](https://badge.fury.io/py/browse-code.svg)
![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**Browse Code** is a CLI tool that turns any AI chatbot (ChatGPT, Gemini, Claude, HuggingFace) into an autonomous coding agent. It bridges your browser and local terminal, letting AI read/write files, run commands, and manage processes on your machine.

## How It Works

Browse Code has two parts:

1. **A local server** that exposes your file system and terminal to the AI via a secure API.
2. **A Chrome extension** that injects agent capabilities into AI chat interfaces.

When connected, you can ask ChatGPT/Gemini/Claude to edit files, run scripts, search code, and more — all executed locally on your machine.

## Setup

### Step 1: Install the package

```bash
pip install browse-code
```

### Step 2: Run the CLI

```bash
bc
```

> If `bc` is not found, add your Python Scripts folder to PATH:
> ```bash
> # Windows (PowerShell)
> $env:Path += ";$env:APPDATA\Python\Python312\Scripts"
>
> # Or run directly
> python -m browse_code.cli
> ```

### Step 3: First-run extension setup

On the first run, `bc` will guide you through a one-time Chrome extension setup:

1. It asks for your permission to extract the extension files.
2. It copies the extension to `~/.browse_code/extension/` and copies the path to your clipboard.
3. It opens `chrome://extensions/` in your browser automatically.
4. You enable **Developer mode** (top-right toggle), click **Load unpacked**, and paste the path.
5. Press Enter in the terminal and the server starts.

**You only do this once.** The extension stays loaded in Chrome across sessions.

### Step 4: Start an AI session

1. Open any supported AI chat (ChatGPT, Gemini, Claude, or HuggingFace Chat).
2. Click the Browse Code Bridge extension icon and set your workspace directory.
3. Click "Initialize Agent in Chat".
4. Start coding with AI — it now has full access to your local environment.

## Subsequent Usage

After the first-time setup, just run:

```bash
bc
```

The server starts immediately. Open your AI chat tab and you're ready to go. The server terminal will show:
- A startup banner with your workspace and endpoint
- `[+] Extension connected` when the browser extension connects
- Real-time logs of every file read, write, command execution, and diff

## Features

- **File Operations:** Read, write, and patch files with inline terminal diffs
- **Code Search:** Search across your entire codebase by keyword
- **Terminal Commands:** Run shell commands with full stdout/stderr capture
- **Background Processes:** Start, monitor, and kill long-running processes
- **Multi-Platform AI:** Works with ChatGPT, Gemini, Claude, and HuggingFace Chat
- **Extension Heartbeat:** Server detects when the browser extension connects/disconnects

## For Developers

1. Clone the repository:
   ```bash
   git clone https://github.com/Dedeep007/browse_code.git
   cd browse_code
   ```
2. Install in editable mode:
   ```bash
   pip install -e .
   ```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

## License

Distributed under the MIT License.
