/* Applies a saved light/dark choice before first paint. No other storage, no cookies. */
try {
  var t = localStorage.getItem('v3r1t4s-theme');
  if (t === 'light' || t === 'dark') document.documentElement.setAttribute('data-theme', t);
} catch (e) {}
