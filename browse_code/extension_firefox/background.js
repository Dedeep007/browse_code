chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === 'bg_fetch') {
        fetch(request.url, request.options)
            .then(async (res) => {
                const contentType = res.headers.get('content-type') || '';
                let data = null;
                let text = null;
                if (contentType.includes('application/json')) {
                    data = await res.json();
                } else {
                    text = await res.text();
                }
                sendResponse({
                    ok: res.ok,
                    status: res.status,
                    data: data,
                    text: text
                });
            })
            .catch(err => {
                sendResponse({ error: err.message });
            });
        return true; // Keep message channel open for async response
    }
});
