(() => {
  'use strict';

  const banner = document.querySelector('[data-pwa-banner]');
  const installButton = document.querySelector('[data-pwa-install]');
  const dismissButton = document.querySelector('[data-pwa-dismiss]');
  const instructions = document.querySelector('[data-pwa-instructions]');
  let installPrompt = null;

  // Save only the account email for convenience; passwords remain out of browser storage.
  const emailStorageKey = 'schoolnet-account-email';
  document.querySelectorAll('[data-persist-email="true"]').forEach(input => {
    const saveEmail = () => {
      try {
        const email = input.value.trim();
        if (email) window.localStorage.setItem(emailStorageKey, email);
        else window.localStorage.removeItem(emailStorageKey);
      } catch (_) { /* Do not block account entry if browser storage is unavailable. */ }
    };
    try {
      const savedEmail = window.localStorage.getItem(emailStorageKey);
      if (!input.value && savedEmail) input.value = savedEmail;
      else if (input.value) saveEmail();
    } catch (_) { /* Browser storage may be disabled; the server-rendered form still works. */ }
    input.addEventListener('input', saveEmail);
    input.form?.addEventListener('submit', saveEmail);
  });

  const isInstalled = window.matchMedia('(display-mode: standalone)').matches
    || window.navigator.standalone === true;
  let wasDismissed = false;
  try { wasDismissed = window.localStorage.getItem('schoolnet-install-dismissed') === 'yes'; } catch (_) { /* Storage may be unavailable. */ }

  if (banner && !isInstalled && !wasDismissed) banner.hidden = false;

  window.addEventListener('beforeinstallprompt', event => {
    event.preventDefault();
    installPrompt = event;
    if (banner && !isInstalled && !wasDismissed) banner.hidden = false;
    if (installButton) installButton.textContent = 'Install';
    if (instructions) instructions.hidden = true;
  });

  if (installButton) {
    installButton.addEventListener('click', async () => {
      if (!installPrompt) {
        if (instructions) instructions.hidden = !instructions.hidden;
        return;
      }
      installPrompt.prompt();
      try { await installPrompt.userChoice; } catch (_) { /* The browser owns the prompt result. */ }
      installPrompt = null;
      if (banner) banner.hidden = true;
    });
  }

  if (dismissButton) {
    dismissButton.addEventListener('click', () => {
      if (banner) banner.hidden = true;
      try { window.localStorage.setItem('schoolnet-install-dismissed', 'yes'); } catch (_) { /* Dismiss for this page view only. */ }
    });
  }

  if ('serviceWorker' in navigator && window.isSecureContext) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/service-worker.js', { scope: '/' }).catch(() => {
        // The online app remains fully usable if service-worker installation is unavailable.
      });
    }, { once: true });
  }
})();
