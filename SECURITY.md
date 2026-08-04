# Security Policy

## Supported Versions

Browse Code is actively developed. Security updates are applied to the latest minor version series. Please ensure you are running the latest version using `pip install --upgrade browse-code`.

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| < 0.2.x | :x:                |

## Security Model

Browse Code runs a local Python server that exposes access to your local filesystem and terminal to AI chatbots via a browser extension. 

Because this tool grants autonomous terminal execution and file modification capabilities to the AI, it inherently trusts the AI model's outputs. You should only use this tool with trusted AI providers (like Claude, Gemini, ChatGPT) and you should always monitor what the AI is doing.

The local server runs exclusively on `127.0.0.1:5505` and generates a secure, randomized `X-Session-Token` on startup to ensure that only the authenticated browser extension running in the active chat tab can interact with it. 

## Reporting a Vulnerability

If you discover a security vulnerability within Browse Code (e.g., an unauthorized cross-origin bypass, a way for external sites to execute code, or an authentication flaw in the bridge), please report it responsibly.

**Do not open a public issue.** Instead, please send an email to the repository owner directly or use GitHub's private vulnerability reporting feature on the repository. 

We will acknowledge receipt of your vulnerability report within 48 hours and strive to send you regular updates about our progress. If the vulnerability is confirmed, we will release a patch as quickly as possible.
