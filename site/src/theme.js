/* Applies a saved light/dark choice before first paint. Dark is the CSS default; the OS light preference applies
   when nothing is saved. One localStorage key (v3r1t4s-theme), no cookies. */
try {
  var t = localStorage.getItem('v3r1t4s-theme');
  if (t === 'light' || t === 'dark') document.documentElement.setAttribute('data-theme', t);
} catch (e) {}
