async function load() {
  const tbody = document.getElementById('tbody');
  const last = document.getElementById('lastUpdate');

  try {
    const res = await fetch('data/latest.json', { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const j = await res.json();

    const rows = Array.isArray(j.rows) ? j.rows : [];
    tbody.innerHTML = rows.map(r => `
      <tr>
        <td class="left">${r.teamName ?? '—'}</td>
        <td>${r.wins ?? 0}</td>
        <td>${r.losses ?? 0}</td>
        <td>${Math.round(Number(r.pointsFor ?? 0))}</td>
        <td>${Math.round(Number(r.pointsAgainst ?? 0))}</td>
      </tr>
    `).join('');

    last.textContent = `Last updated (UTC): ${j.generated_utc ?? '—'}`;
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="5" class="left">Failed to load data/latest.json (${e.message}).</td></tr>`;
    last.textContent = 'Last updated: —';
  }
}

document.addEventListener('DOMContentLoaded', load);
