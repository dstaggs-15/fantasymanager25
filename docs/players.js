(async function () {
  const src = 'data/players_summary.json';
  document.querySelector('#source').textContent = src;

  const row = p => `
    <tr>
      <td>${p.name}</td>
      <td>${p.pos ?? ''}</td>
      <td>${p.proTeam ?? ''}</td>
      <td>${p.proj_season ?? ''}</td>
      <td>${p.owned_pct != null ? (p.owned_pct.toFixed ? p.owned_pct.toFixed(1) : p.owned_pct) : ''}</td>
    </tr>`;

  try {
    const res = await fetch(src, { cache: 'no-cache' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const rows = (data.rows || []).slice(0, 300); // keep page light

    document.querySelector('#count').textContent = `(${rows.length})`;

    document.querySelector('#list').innerHTML = `
      <table class="table">
        <thead>
          <tr>
            <th>Name</th><th>Pos</th><th>Team</th><th>Proj Season</th><th>Owned %</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map(row).join("")}
        </tbody>
      </table>`;
  } catch (err) {
    document.querySelector('#list').innerHTML =
      `<p class="error">Failed to load players_summary.json (${err.message}).</p>`;
  }
})();
