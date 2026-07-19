# Contributing to Browse Code

First off, thank you for considering contributing to Browse Code! It's people like you that make Browse Code such a great tool for turning LLMs into autonomous agents.

## 🧠 How to Contribute

### 1. Reporting Bugs
If you find a bug, please create a new issue on GitHub. Include:
- Your operating system and browser version.
- The AI platform you were using (ChatGPT, Claude, Gemini, etc.).
- Steps to reproduce the bug.
- Any relevant console errors from the extension background page or your local terminal.

### 2. Suggesting Enhancements
Have an idea to make Browse Code better? We'd love to hear it! Open an issue and describe your idea. The more details you can provide about the use case and how it should work, the better.

### 3. Submitting Pull Requests
1. **Fork the repo** and create your branch from `main`.
2. **Clone your fork** locally.
3. Install the project in editable mode:
   ```bash
   pip install -e .
   ```
4. **Make your changes**. If you are editing the Chrome extension, you will find the source code in `browse_code/extension/`. Make sure to reload the extension in `chrome://extensions/` to test your changes.
5. **Commit your changes**. Please use conventional commits (e.g., `feat: added new tool`, `fix: patched regex bug`).
6. **Push to your fork** and submit a Pull Request.

## 🛠️ Architecture Overview

- **Python Backend (`server.py`)**: Runs locally, exposing a FastAPI server that executes terminal commands and reads/writes local files.
- **Chrome Extension (`content.js`, `background.js`)**: Injects an invisible workflow engine into the LLM chat window. It intercepts specific `<tool=>` XML tags, forwards them to the Python backend, and automatically injects the results back into the chat to achieve autonomous looping.

## 🤝 Code of Conduct
Please note that this project is released with a Contributor Code of Conduct. By participating in this project you agree to abide by its terms. Be respectful and constructive in all discussions.
