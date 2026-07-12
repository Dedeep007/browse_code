document.addEventListener('DOMContentLoaded', () => {
    const dirInput = document.getElementById('dir-input');
    const injectNInput = document.getElementById('inject-n-input');
    const saveBtn = document.getElementById('save-btn');
    const initBtn = document.getElementById('init-btn');
    const processList = document.getElementById('process-list');

    chrome.storage.local.get(['workspaceDir', 'injectN', 'serverKey'], (result) => {
        if (result.workspaceDir) {
            dirInput.value = result.workspaceDir;
        }
        if (result.workspaceDir && result.serverKey) {
            syncWithServer(result.workspaceDir, result.serverKey);
        }
        if (result.injectN !== undefined && injectNInput) {
            injectNInput.value = result.injectN;
        }
    });

    saveBtn.addEventListener('click', () => {
        const path = dirInput.value.trim();
        let injectN = 10;
        if (injectNInput) {
            const val = parseInt(injectNInput.value, 10);
            if (!isNaN(val)) injectN = val;
        }
        
        chrome.storage.local.get(['serverKey'], (result) => {
            chrome.storage.local.set({ workspaceDir: path, injectN: injectN }, () => {
                saveBtn.textContent = "Saved!";
                setTimeout(() => saveBtn.textContent = "Save Settings", 1500);
                if (result.serverKey) {
                    syncWithServer(path, result.serverKey);
                }
            });
        });
    });

    initBtn.addEventListener('click', () => {
        const path = dirInput.value.trim();
        if (!path) {
            initBtn.innerText = 'Workspace directory required!';
            setTimeout(() => initBtn.innerText = 'Initialize Agent in Chat', 3000);
            return;
        }

        initBtn.innerText = 'Initializing...';
        chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
            const activeTab = tabs[0];
            const validUrls = ['chatgpt.com', 'gemini.google.com', 'claude.ai', 'huggingface.co'];
            
            if (activeTab && validUrls.some(url => activeTab.url.includes(url))) {
                chrome.tabs.sendMessage(activeTab.id, { action: "INITIALIZE_AGENT" }, () => {
                    if (chrome.runtime.lastError) {
                        initBtn.innerText = 'Error: Refresh Tab First!';
                        setTimeout(() => initBtn.innerText = 'Initialize Agent in Chat', 3000);
                    } else {
                        initBtn.innerText = 'Initialize Agent in Chat';
                    }
                });
            } else {
                initBtn.innerText = 'Not a valid AI chat tab';
                setTimeout(() => initBtn.innerText = 'Initialize Agent in Chat', 3000);
            }
        });
    });

    function syncWithServer(path, key) {
        if (!path || !key) return;
        fetch('http://127.0.0.1:5505/set-workspace', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-Server-Key': key
            },
            body: JSON.stringify({ path: path })
        }).catch(err => console.error("Bridge server not running"));
    }

    function pollStatus() {
        chrome.storage.local.get(['serverKey'], (result) => {
            if (!result.serverKey) return;
            fetch('http://127.0.0.1:5505/status', {
                headers: { 'X-Server-Key': result.serverKey }
            })
                .then(res => res.json())
                .then(data => {
                if (!data.processes || data.processes.length === 0) {
                    processList.innerHTML = '<div style="color: #94a3b8;">No active background processes...</div>';
                    return;
                }
                
                let html = '';
                data.processes.forEach(proc => {
                    const statusColor = proc.status === 'running' ? '#10b981' : '#ef4444';
                    html += `
                    <div class="process-card">
                        <div><span class="pid">[PID: ${proc.pid}]</span> - <span style="color:${statusColor}">${proc.status.toUpperCase()}</span></div>
                        <div class="log-preview">${proc.logs || 'Waiting for output...'}</div>
                    </div>`;
                });
                processList.innerHTML = html;
            })
            .catch(() => {
                processList.innerHTML = '<div style="color: #ef4444;">Disconnected from local server.</div>';
            });
    }

    setInterval(pollStatus, 1500);
    pollStatus();
});