# Browse Code

![PyPI version](https://badge.fury.io/py/browse-code.svg)
![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**Browse Code** is a powerful CLI tool that bridges your local terminal environment with your browser. It runs a local backend server and injects an AI-assisted Chrome extension, enabling seamless automation, local file reads/writes, and background process management directly from the browser.

## Features

- **Local AI Bridge Server:** A fast, secure FastAPI-based server that exposes your local environment (reading files, listing directories, executing terminal commands, managing background processes).
- **Chrome Extension Integration:** Automatically sets up (with your permission) a Chrome extension that interacts with the backend.
- **Easy-to-use CLI:** Start your AI sessions with a single `bc` command.

## Installation

### For Users

Install the package directly via pip:

```bash
pip install browse-code
```

### For Developers

1. Clone the repository:
   ```bash
   git clone https://github.com/Dedeep007/browse_code.git
   cd browse_code
   ```
2. Install in editable mode:
   ```bash
   pip install -e .
   ```

## Usage

Once installed, simply run the CLI command:

```bash
bc
```

### What happens when you run `bc`?

**First run:**
1. The CLI asks if you want to set up the Chrome extension.
2. If you agree, it extracts the extension to `~/.browse_code/extension/` and copies the path to your clipboard.
3. It opens `chrome://extensions/` automatically.
4. You just need to enable "Developer mode", click "Load unpacked", and paste the path.
5. Once done, press Enter and the server starts.

**Every run after that:**
The server starts immediately with no prompts. The extension stays loaded in Chrome across sessions.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

## License

Distributed under the MIT License.
