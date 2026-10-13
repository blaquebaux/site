// Native disclosure works without JavaScript; enhance dismissal when available.
const menu = document.querySelector('.bb-site-nav details');
const wordmark = document.querySelector('.bb-site-nav .bb-wordmark');
if (wordmark && !document.querySelector('.bb-site-nav .bb-positioning')) {
  const positioning = document.createElement('span');
  positioning.className = 'bb-positioning';
  positioning.textContent = 'Quantitative Intelligence for Finance';
  wordmark.insertAdjacentElement('afterend', positioning);
}
if (menu) {
  document.addEventListener('click', event => { if (!menu.contains(event.target)) menu.open = false; });
  document.addEventListener('keydown', event => { if (event.key === 'Escape' && menu.open) { menu.open = false; menu.querySelector('summary').focus(); } });
  menu.querySelectorAll('a').forEach(link => link.addEventListener('click', () => { menu.open = false; }));
}
