(() => {
  const root = document.querySelector('[data-provenance-registry]');
  if (!root) return;

  const value = item => item || 'Not pinned for this release.';
  const row = (label, item) => `<div><dt>${label}</dt><dd>${value(item)}</dd></div>`;

  fetch('/research-registry.json')
    .then(response => {
      if (!response.ok) throw new Error(`registry ${response.status}`);
      return response.json();
    })
    .then(registry => {
      const entries = new Map(registry.entries.map(entry => [entry.slug, entry]));
      root.querySelectorAll('.repo-explained[id^="research-"]').forEach(card => {
        const slug = card.id.replace('research-', '');
        const entry = entries.get(slug);
        if (!entry) return;
        const p = entry.provenance;
        const drawer = document.createElement('details');
        drawer.className = 'provenance-drawer';
        drawer.innerHTML = `<summary>Evidence record / ${entry.name}</summary><dl>${row('Evidence date', entry.evidence_date)}${row('Data window', p.data_window)}${row('Benchmark', p.benchmark)}${row('Costs', p.costs)}${row('Validation stage', p.validation_stage)}${row('Code commit', p.code_commit)}${row('Limitations', p.limitations)}</dl><p><a href="${entry.methods}" target="_blank" rel="noopener noreferrer">Repository methods ↗</a></p>`;
        card.insertAdjacentElement('afterend', drawer);
      });
    })
    .catch(error => {
      const notice = document.createElement('p');
      notice.className = 'provenance-error';
      notice.textContent = 'Evidence records are temporarily unavailable. Repository links remain authoritative.';
      root.prepend(notice);
      console.error('provenance registry unavailable', error);
    });
})();
