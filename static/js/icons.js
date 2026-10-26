/* Server templates render icons inline; this helper preserves their decorative, non-interactive semantics. */
(() => {
  'use strict';
  document.querySelectorAll('svg.icon').forEach(icon => {
    icon.setAttribute('aria-hidden', 'true');
    icon.setAttribute('focusable', 'false');
  });
})();
