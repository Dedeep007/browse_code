Object.defineProperty(document, 'visibilityState', { get: () => 'visible' });
Object.defineProperty(document, 'hidden', { get: () => false });
window.addEventListener('visibilitychange', (e) => e.stopImmediatePropagation(), true);