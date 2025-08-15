(async function () {
  const table = (rows) => `
    <table class="table">
      <thead>
        <tr>
          <th>Team</th>
          <th>Players</th>
        </tr>
      </thead>
      <tbody>
        ${rows.map(r => `
          <tr>
            <td>${r.team} <small class="muted">(${r.abbrev})</small></td>
            <td>${r.player_count}</td>
          </tr>`).join("")}
      </tbody>
    </table>`;

  const src = 'data/team_rosters.json';
  document.querySelector('#source').textContent = src;

  try {
    const res = await fetch(src, { cache: 'no-cache' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    if (!data || !Array.isArray(data.rows)) throw new Error('Bad JSON shape');

    const container = document.querySelector('#list');
    container.innerHTML = table(data.rows);

  } catch (err) {
    document.querySelector('#list').innerHTML =
      `<p class="error">Failed to load team_rosters.json (${err.message}).</p>`;
  }
})();
