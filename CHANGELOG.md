# Changelog

All notable changes to this project will be documented in this file.

## [v0.2.56] - 2026-07-19
### Performance
- **Massive UI Optimization**: Completely eliminated browser freezing and lag during LLM generation. The extension now uses lightweight `innerHTML.length` caching to detect typing and only runs the heavy Shadow DOM recursive parser (`getDeepText`) *once* when generation completes.

## [v0.2.55] - 2026-07-19
### Fixed
- **Stuck Injection Fix**: Added a global background watchdog interval. If the AI finishes generating an automated system message and React suspends the "Send" button due to focus loss, the extension will now forcefully bypass the suspension and hit send.

## [v0.2.54] - 2026-07-19
### Added
- **Antigravity-Style Editing**: Replaced the brittle `<tool='patch'>` string replacement with a highly robust `<tool='replace'>` implementation. It now requires exact `start` and `end` bounds to eliminate hallucination and context-matching failures.
- **True Regex Search**: Upgraded the backend `search_code` tool to compile and execute true Python regex (`re.compile`), rather than relying on basic case-sensitive substring matching.

## [v0.2.53] - 2026-07-19
### Fixed
- **RLHF Override**: Added a massive critical directive to the `SYSTEM_PROMPT` to prevent Claude 3.5 Sonnet and Gemini 1.5 Pro from refusing to emit custom XML tool tags (bypassing their safety fine-tuning against "fabricating" unrecognized tool execution).

## [v0.2.52] - 2026-07-19
### Fixed
- **Malformed Tool Handling**: The primary observer loop now intercepts malformed/unclosed XML tool tags (caused by token limits or hallucination) and injects a real-time error back to the AI prompting it to self-correct.

## [Earlier Versions]
- **Extension & Python Backend**: Built and released the foundational bridge between web AI UIs and the local execution environment, bringing autonomous workflow execution to ChatGPT, Claude, Gemini, and HuggingFace Chat.
