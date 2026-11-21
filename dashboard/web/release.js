'use strict';
// One UI release identifier shared by every page; this is not a model version.
(() => {
  const release = Object.freeze({version: '0.8.0', sprint: '08', name: 'AI Journey'});
  if (typeof module !== 'undefined') module.exports = release;
  if (typeof document === 'undefined') return;
  document.querySelectorAll('[data-release]').forEach(el => {
    el.textContent = `v${release.version} · Sprint ${release.sprint}`;
    el.dir = 'ltr';
  });
})();
