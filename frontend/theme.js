(function () {
  'use strict';

  var STORAGE_KEY = 'sgs_theme';

  function getStoredTheme() {
    try {
      var s = localStorage.getItem(STORAGE_KEY);
      if (s === 'light' || s === 'dark') return s;
    } catch (_) {}
    return null;
  }

  function getSystemDark() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  }

  function resolveTheme() {
    var stored = getStoredTheme();
    if (stored) return stored;
    return getSystemDark() ? 'dark' : 'light';
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch (_) {}
  }

  applyTheme(resolveTheme());

  var SUN =
    '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>';
  var MOON =
    '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';

  function updateToggleButton(btn) {
    if (!btn) return;
    var dark = document.documentElement.getAttribute('data-theme') === 'dark';
    btn.innerHTML = dark ? SUN : MOON;
    btn.setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode');
    btn.setAttribute('title', dark ? 'Light mode' : 'Dark mode');
  }

  document.addEventListener('DOMContentLoaded', function () {
    var nav = document.querySelector('.site-nav .nav-inner');
    if (!nav || nav.querySelector('.theme-toggle')) return;

    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'theme-toggle';
    updateToggleButton(btn);

    btn.addEventListener('click', function () {
      var cur = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
      applyTheme(cur === 'dark' ? 'light' : 'dark');
      updateToggleButton(btn);
    });

    var logo = nav.querySelector('.nav-logo');
    var toggle = nav.querySelector('.nav-toggle');
    if (logo && toggle) {
      nav.insertBefore(btn, toggle);
    } else if (logo) {
      logo.insertAdjacentElement('afterend', btn);
    } else {
      nav.insertBefore(btn, nav.firstChild);
    }

    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function () {
      if (getStoredTheme()) return;
      applyTheme(getSystemDark() ? 'dark' : 'light');
      updateToggleButton(btn);
    });
  });
})();
