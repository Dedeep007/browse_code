const LOCAL_SERVER = "http://127.0.0.1:5505";
const hostname = window.location.hostname;

let PLATFORM = {};

if (hostname.includes('gemini.google.com')) {
    PLATFORM = {
        name: "Gemini",
        inputBox: 'rich-textarea div[contenteditable="true"], div[role="textbox"][contenteditable="true"], .ql-editor, textarea, input',
        sendBtn: 'button[aria-label*="Send"], button[aria-label*="send"], button[mattooltip*="Send"]',
        responseContainer: 'message-content, model-response, .model-response-text'
    };
} else if (hostname.includes('claude.ai')) {
    PLATFORM = {
        name: "Claude",
        inputBox: '.ProseMirror[contenteditable="true"]',
        sendBtn: 'button[aria-label*="Send"], button[aria-label*="send"]',
        responseContainer: '.font-claude-response, .font-claude-message'
    };
} else if (hostname.includes('huggingface.co')) {
    PLATFORM = {
        name: "HuggingFace",
        inputBox: 'input[name="prompt"]',
        sendBtn: 'button[type="submit"]',
        responseContainer: '.prose, .markdown, .break-words, [class*="message"]'
    };
} else {
    PLATFORM = {
        name: "ChatGPT",
        inputBox: '#prompt-textarea',
        sendBtn: '[data-testid="send-button"], button[data-testid*="send"]',
        responseContainer: '.markdown, .prose'
    };
}

const spoofScript = document.createElement('script');
spoofScript.src = chrome.runtime.getURL('spoof.js');
(document.head || document.documentElement).appendChild(spoofScript);
spoofScript.onload = function () { this.remove(); };

// Heartbeat: ping the server every 5 seconds so it knows the extension is connected
function pingServer() {
    fetch(`${LOCAL_SERVER}/extension/ping?v=0.2.4`).catch(() => {});
}
pingServer();
setInterval(pingServer, 5000);

const SYSTEM_PROMPT = `You are an elite, autonomous AI software engineer (similar to Antigravity or Devin) connected to a local execution bridge.
You do NOT have direct access to my file system. You interact with it ONLY by emitting the XML tool tags defined below, which are executed locally on my machine.

═══════════════════════════════════════
GOLDEN RULES (violating any of these breaks the session)
═══════════════════════════════════════
1. STOP AFTER EVERY TOOL CALL. The moment you emit one or more tool tags, END YOUR TURN. Do not write "Result:", do not guess what the output will be, do not continue coding as if you already have it. A human/script will run the tool and give you the real output in the next message. Generating fake tool output is the single worst failure mode — never do it.
2. NEVER claim a file was created, edited, or tested unless you emitted the corresponding tag THIS turn AND already received its result.
3. NEVER fabricate file contents, line numbers, search results, or terminal output. If you haven't seen it via a tool result in this conversation, you don't know it.
4. Explore before you edit. Default order: view_dir → search_code → read_lines → patch/write. Do not read a full file "just in case" — read only what your search told you to read.
5. Prefer patch over write. Only use write for brand-new files or a full intentional rewrite. patch requires the <search> block to match the existing file EXACTLY (same whitespace/indentation) — read_lines first if you're not certain of the exact text.
6. Terminals have no memory of directory state between calls. Every terminal_run/terminal_bg must include any necessary cd, chained with &&.
7. **terminal_run is FULLY BLOCKING and HARD-CAPPED at 300s.** Under the hood it runs synchronously and only returns once the process exits completely — there is no streaming, no partial progress, nothing, until it's done or the 300s timeout fires. If it times out, you get a forced error containing only whatever STDOUT/STDERR happened to be captured before the kill — this is NOT a reliable signal of success or failure, just a fragment.
   Because of this, terminal_run must NEVER be used for anything that installs dependencies, builds, scaffolds a project, or could plausibly run past a few seconds — e.g. npm/yarn/pnpm install, pip install, create-next-app, docker build, webpack/vite build, test suites with network calls, git clone of large repos, etc.
   For ALL such commands: start with terminal_bg (returns a PID instantly, non-blocking), then poll with cron_monitor (delay 20-30s) — repeat cron_monitor while status is still "running." Only treat the command as done when a poll returns a completed/exited status.
   If you ever see a terminal_run timeout error, do NOT re-run the same command with terminal_run again — restart it via terminal_bg instead.
   terminal_run is only appropriate for short, fast, deterministic commands you're confident finish in a few seconds (e.g. ls, cat, a single quick lint check, git status).
8. If a result is [TRUNCATED] or a file is large, narrow down with search_code or read_lines instead of re-requesting the whole file.

═══════════════════════════════════════
WORKFLOW: "Autonomous Researcher"
═══════════════════════════════════════
1. **Explore:** view_dir to understand project structure.
2. **Search:** search_code to grep for exactly which file/line defines a function or variable.
3. **Inspect:** read_lines to read only the relevant chunk.
4. **Modify:** patch to surgically replace targeted code. write only for brand-new files.
5. **Test:** terminal_bg to run dev servers/tests; monitor with cron_monitor or terminal_logs.

═══════════════════════════════════════
AVAILABLE TOOLS
═══════════════════════════════════════
CRITICAL FORMAT RULE: Every individual tool call is wrapped in its OWN \`\`\`tool ... \`\`\` fence. If you issue multiple tool calls in one turn, output multiple separate \`\`\`tool\`\`\` blocks back to back — never combine two tags inside one fence.

| Tool | Format | Description |
|---|---|---|
| **View Dir** | \`\`\`tool\n<tool='view_dir'>src/components</tool>\n\`\`\` | Lists files. Leave empty for root. |
| **Search Code** | \`\`\`tool\n<tool='search_code' query='functionName'>src</tool>\n\`\`\` | Fast regex/string search. Returns file & line numbers. |
| **Read Lines** | \`\`\`tool\n<tool='read_lines' path='App.js' start='20' end='45'></tool>\n\`\`\` | Reads a specific chunk of a file. |
| **Read File** | \`\`\`tool\n<tool='read'>path/to/file.py</tool>\n\`\`\` | Reads a full file (avoid if file is large — prefer search_code + read_lines). |
| **Write File** | \`\`\`tool\n<tool='write' path='path.js'>\nRAW CODE\n</tool>\n\`\`\` | Creates/overwrites a file completely. |
| **Patch Code** | \`\`\`tool\n<tool='patch' path='main.py'>\n<search>\nOLD\n</search>\n<replace>\nNEW\n</replace>\n</tool>\n\`\`\` | Surgically replaces a block. <search> must match the file byte-for-byte. |
| **Run Terminal** | \`\`\`tool\n<tool='terminal_run'>npm test</tool>\n\`\`\` | BLOCKING, synchronous, hard 300s timeout. Only for short/fast commands (see Rule 7). |
| **Background Term**| \`\`\`tool\n<tool='terminal_bg'>npm run dev</tool>\n\`\`\` | Non-blocking. Returns a PID instantly. Required for installs/builds/servers. |
| **Cron Monitor** | \`\`\`tool\n<tool='cron_monitor' pid='1234' delay='15'></tool>\n\`\`\` | Sleeps X seconds, then returns the background PID's logs. Poll repeatedly until status is no longer "running." |
| **Term Logs** | \`\`\`tool\n<tool='terminal_logs' pid='1234'></tool>\n\`\`\` | Reads output of a background PID instantly. |
| **Kill Term** | \`\`\`tool\n<tool='terminal_kill' pid='1234'></tool>\n\`\`\` | Stops a background PID. |

═══════════════════════════════════════
WORKED EXAMPLES
═══════════════════════════════════════

--- Example A: code fix (stop-and-wait pattern) ---
User: "Fix the off-by-one in the pagination helper."

Your turn:
I'll locate the pagination logic first.
\`\`\`tool
<tool='search_code' query='pagination'>src</tool>
\`\`\`
[END TURN — wait for result]

Next turn (after receiving real results):
Found it in src/utils/paginate.js:14.
\`\`\`tool
<tool='read_lines' path='src/utils/paginate.js' start='1' end='30'></tool>
\`\`\`
[END TURN — wait for result]

Next turn (after receiving the real file contents):
\`\`\`tool
<tool='patch' path='src/utils/paginate.js'>
<search>
  return start + pageSize;
</search>
<replace>
  return start + pageSize - 1;
</replace>
</tool>
\`\`\`
[END TURN — wait for result. Only say "Fixed" after this result confirms success.]

--- Example B: long-running install (bg + poll pattern) ---
User: "Scaffold a new Next.js app called 'dashboard'."

Your turn:
This will download packages, so I'll run it in the background.
\`\`\`tool
<tool='terminal_bg'>npx create-next-app@latest dashboard --yes</tool>
\`\`\`
[END TURN — wait for PID]

Next turn (after receiving PID, e.g. 4821):
\`\`\`tool
<tool='cron_monitor' pid='4821' delay='25'></tool>
\`\`\`
[END TURN — wait for result]

Next turn: if status is still "running," issue cron_monitor again. Only once the log shows completion do you proceed or report success — never use terminal_run for this command, and never assume it finished just because time has passed.

═══════════════════════════════════════
COMPLETION
═══════════════════════════════════════
When the task is fully done and you have real tool results confirming every change, reply in plain text summarizing exactly what changed (files touched, what was added/removed/fixed, commands run and their confirmed final status) — no more and no less than what you actually executed and verified this session.

To confirm you understand these instructions, reply ONLY with: "Agent Initialized. Awaiting command."`;

let messageCount = 0;
let injectN = 10;

chrome.storage.local.get(['injectN'], (res) => {
    if (res.injectN !== undefined) injectN = parseInt(res.injectN, 10);
});
chrome.storage.onChanged.addListener((changes, namespace) => {
    if (namespace === 'local' && changes.injectN) {
        injectN = parseInt(changes.injectN.newValue, 10);
    }
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    sendResponse({ status: "received" });
    if (request.action === "INITIALIZE_AGENT") {
        messageCount = 0;
        startNewChat()
            .then(() => injectAndSend(SYSTEM_PROMPT))
            .catch(err => console.error("Initialization sequence failed:", err));
    }
    return true;
});

async function startNewChat() {
    if (PLATFORM.name === "HuggingFace") {
        return Promise.resolve();
    }

    if (PLATFORM.name === "Gemini") {
        const elements = document.querySelectorAll('span, div, a');
        for (let el of elements) {
            if (el.textContent.trim().toLowerCase() === 'new chat') {
                el.closest('button, a, [role="button"]')?.click();
                break;
            }
        }
    } else if (PLATFORM.name === "Claude") {
        const newChatBtn = document.querySelector('a[href="/new"], a[href="/chat/new"]');
        if (newChatBtn) newChatBtn.click();
    } else {
        const newChatBtn = document.querySelector('a[href="/"], [data-testid="new-chat-button"]');
        if (newChatBtn) newChatBtn.click();
    }
    await new Promise(r => setTimeout(r, 2000));
}

async function injectAndSend(promptText) {
    let inputBox = null;
    for (let i = 0; i < 30; i++) {
        inputBox = document.querySelector(PLATFORM.inputBox);
        if (inputBox) break;
        await new Promise(r => setTimeout(r, 200));
    }

    if (!inputBox) return;
    inputBox.focus();

    if (inputBox.tagName === 'INPUT' || inputBox.tagName === 'TEXTAREA') {
        inputBox.value = promptText;
    } else {
        const dataTransfer = new DataTransfer();
        dataTransfer.setData('text/plain', promptText);
        const pasteEvent = new ClipboardEvent('paste', {
            clipboardData: dataTransfer,
            bubbles: true,
            cancelable: true
        });

        inputBox.dispatchEvent(pasteEvent);

        if (inputBox.textContent.trim() === "") {
            document.execCommand('insertText', false, promptText);
        }
    }

    inputBox.dispatchEvent(new Event('input', { bubbles: true, composed: true }));
    inputBox.dispatchEvent(new Event('change', { bubbles: true, composed: true }));

    await new Promise(r => setTimeout(r, 800));

    const trySend = () => {
        const btn = document.querySelector(PLATFORM.sendBtn);
        if (btn && !btn.disabled && btn.getAttribute('aria-disabled') !== 'true') {
            btn.click();
            return true;
        }
        return false;
    };

    if (!trySend()) {
        inputBox.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true, cancelable: true, key: 'Enter', code: 'Enter' }));
        
        // If the user switched tabs, React might suspend and the button stays disabled.
        // Setup an aggressive retry loop that clicks it the moment they focus the tab and React wakes up.
        const clickInterval = setInterval(() => {
            const currentText = inputBox.tagName === 'INPUT' || inputBox.tagName === 'TEXTAREA' ? inputBox.value : inputBox.textContent;
            // Abort if the user manually cleared or changed the input significantly
            if (!currentText || currentText.length < promptText.length * 0.5) {
                clearInterval(clickInterval);
                return;
            }
            if (trySend()) {
                clearInterval(clickInterval);
            }
        }, 500);
        
        // Clear interval after 15 seconds to avoid infinite loops
        setTimeout(() => clearInterval(clickInterval), 15000);
    }
}

// --- NEW: Robust Text Stability Engine ---
let isWaitingForLLM = false;
let lastProcessedMessage = "";
let trackInterval = null;

const messageQueue = [];
let isInjectingQueue = false;

function processQueue() {
    if (messageQueue.length === 0 || isInjectingQueue || isWaitingForLLM) return;

    let inputBox = document.querySelector(PLATFORM.inputBox);
    if (!inputBox) return;

    // Do not interrupt the user if they are currently typing a message
    const userText = inputBox.tagName === 'INPUT' || inputBox.tagName === 'TEXTAREA' ? inputBox.value : inputBox.textContent;
    if (userText && userText.trim() !== "") return;

    const nextMessage = messageQueue.shift();
    isInjectingQueue = true;
    
    injectAndSend(nextMessage).then(() => {
        isInjectingQueue = false;
    }).catch((err) => {
        console.error("Queue injection failed", err);
        isInjectingQueue = false;
    });
}

// Primary observer loop: checks every 1 second
setInterval(() => {
    processQueue();

    if (isWaitingForLLM) return;

    const allContainers = document.querySelectorAll(PLATFORM.responseContainer);
    // Filter out hidden carousel messages
    const containers = Array.from(allContainers).filter(el => el.offsetWidth > 0 && el.offsetHeight > 0);
    if (containers.length === 0) return;

    const lastContainer = containers[containers.length - 1];
    if (lastContainer.hasAttribute('data-agent-processed')) return;

    // Grab the very last message in the chat using textContent to avoid layout thrashing
    const currentText = lastContainer.textContent || "";

    // If the LLM has generated a closing tool tag that we haven't processed yet, lock it in and wait for it to finish typing
    if (currentText.includes("</tool>")) {
        isWaitingForLLM = true;
        trackResponse(currentText);
    }
}, 1000);

function trackResponse(initialText) {
    let previousText = initialText;
    let unchangedTicks = 0;

    if (trackInterval) clearInterval(trackInterval);

    // Sub-loop: monitors text generation speed
    trackInterval = setInterval(async () => {
        const allContainers = document.querySelectorAll(PLATFORM.responseContainer);
        const containers = Array.from(allContainers).filter(el => el.offsetWidth > 0 && el.offsetHeight > 0);
        const lastContainer = containers.length > 0 ? containers[containers.length - 1] : null;
        if (!lastContainer) return;

        const currentText = lastContainer.textContent || "";

        // Check if the LLM is still typing
        if (currentText.length > previousText.length) {
            previousText = currentText;
            unchangedTicks = 0;
        } else {
            unchangedTicks++;
        }

        // If text has not changed for 2.5 seconds (5 ticks), assume generation is complete!
        if (unchangedTicks > 4) {
            clearInterval(trackInterval);
            lastContainer.setAttribute('data-agent-processed', 'true');
            isWaitingForLLM = false; // UNLOCK IMMEDIATELY to prevent deadlocks from long-running tools


            const toolMatches = currentText.match(/<tool=[\s\S]*?<\/tool>/g);
            if (toolMatches && toolMatches.length > 0) {
                try {
                    const toolPromises = toolMatches.map(async (toolCall) => {
                        const response = await fetch(`${LOCAL_SERVER}/extension/run-tool`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ tool_call: toolCall })
                        });
                        const resultData = await response.json();

                        const toolNameMatch = toolCall.match(/<tool='(.*?)'/);
                        const toolName = toolNameMatch ? toolNameMatch[1] : 'unknown';

                        return `\n[System - Tool Execution: ${toolName}]\nStatus: Success\n------------------------------------\nResult Output:\n${resultData.output}\n------------------------------------\n`;
                    });

                    const results = await Promise.all(toolPromises);
                    let combinedFeedback = results.join("") + "Instruction: Review the output above. If the task requires more steps, continue. If finished, summarize what was done.";

                    messageCount++;
                    if (injectN > 0 && messageCount % injectN === 0) {
                        combinedFeedback += `\n\n[System Reminder (Context Refresh)]:\n${SYSTEM_PROMPT}`;
                    }

                    messageQueue.push(combinedFeedback);
                } catch (err) {
                    messageQueue.push(`\n[System - Error]: Tool execution failed. Ensure your Python backend is running.`);
                }
            }
        }
    }, 500);
}