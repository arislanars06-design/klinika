// Sahifa chizilishidan oldin tanlangan rejimni (kunduzgi/tungi) qo'llaydi, oq "miltillash" bo'lmasligi uchun.
(function () {
  var saved = null;
  try { saved = localStorage.getItem('nurmed_theme'); } catch (e) { /* ignore */ }
  var dark = saved ? saved === 'dark' : window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
})();
