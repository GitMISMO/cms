/* Shown inside the CMS (page.html?embed=1, Jonna 27 Oct 2026): no masthead of its own, the CMS's
   light or dark theme, links that open the CMS's own views stay in the CMS, and the page's
   height is reported so its view needs no scroll bar of its own. Used by My Approvals, the
   Email Playbook and Help. */
(function () {
  var root = document.documentElement;
  var EMBED = /[?&]embed=1\b/.test(location.search) && window.parent !== window;
  if (!EMBED) return;
  root.classList.add('embed');
  var page = (location.pathname.split('/').pop() || '').replace(/\.html$/, '');
  var syncTheme = function () { try { var t = window.parent.document.documentElement.getAttribute('data-theme'); if (t) root.setAttribute('data-theme', t); else root.removeAttribute('data-theme'); } catch (e) {} };
  syncTheme();
  try { new MutationObserver(syncTheme).observe(window.parent.document.documentElement, { attributes: true, attributeFilter: ['data-theme'] }); } catch (e) {}
  var tell = function () { try { window.parent.postMessage({ embedHeight: document.documentElement.scrollHeight, page: page }, location.origin); } catch (e) {} };
  window.addEventListener('load', tell);
  document.addEventListener('DOMContentLoaded', function () {
    tell();
    if (window.ResizeObserver) new ResizeObserver(tell).observe(document.body);
    /* "/cms/#records" and the like open that view in the CMS around this page */
    document.addEventListener('click', function (e) {
      var a = e.target && e.target.closest ? e.target.closest('a[href]') : null;
      if (!a) return;
      var m = a.getAttribute('href').match(/^(?:\/cms\/|index\.html)?#([a-z-]+)$/i);
      if (!m) return;
      e.preventDefault();
      try { var b = window.parent.document.querySelector('.navlink[data-view="' + m[1] + '"]'); if (b) b.click(); } catch (x) {}
    });
  });
})();
