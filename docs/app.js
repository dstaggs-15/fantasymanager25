(async function () {
  const el = document.getElementById('status');
  const notesEl = document.getElementById('notes');
  try {
    const res = await fetch('./data/status.json', { cache: 'no-store' });
    const s = await res.json();
    el.textContent = `Last updated (UTC): ${s.generated_utc} — Season: ${s.season ?? '—'} Week: ${s.week ?? '—'}`;
    notesEl.textContent = s.notes || '';
  } catch {
    el.textContent = 'Status unavailable (check Actions).';
  }
})();
