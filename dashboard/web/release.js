'use strict';
// One UI release identifier shared by every page; this is not a model version.
(() => {
  const release = Object.freeze({version: '0.6.0', sprint: '06', name: 'AI Journey'});
  if (typeof module !== 'undefined') module.exports = release;
  if (typeof document === 'undefined') return;
  document.querySelectorAll('[data-release]').forEach(el => {
    el.textContent = `v${release.version} · Sprint ${release.sprint} · ${release.name}`;
    el.dir = 'ltr';
  });
})();
