(async function () {
  const el = document.getElementById('status');
  const notesEl = document.getElementById('notes');
  try {
    const res = await fetch('./data/status.json', { cache: 'no-store' });
    if (!res.ok) throw new Error('status.json missing');
    const s = await res.json();
    el.textContent = `Last updated (UTC): ${s.generated_utc} — Season: ${s.season ?? '—'} Week: ${s.week ?? '—'}`;
    if (s.notes) notesEl.textContent = s.notes;
  } catch (e) {
    el.textContent = 'Status unavailable (check Actions).';
  }
})();
