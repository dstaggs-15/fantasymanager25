async function load(){
  const container = document.getElementById('container');
  try{
    const res = await fetch('data/team_rosters.json', {cache:'no-store'});
    if(!res.ok) throw new Error(`HTTP ${res.status}`);
    const j = await res.json();
    const teams = Array.isArray(j.teams) ? j.teams : [];

    if(!teams.length){
      container.innerHTML = `<div class="sub">No team data yet. This usually fills after the first successful ESPN roster fetch.</div>`;
      return;
    }

    container.innerHTML = teams.map(t => {
      const rows = (t.players || []).map(p => `
        <tr>
          <td>${p.name ?? '—'}</td>
          <td>${p.position ?? '—'}</td>
          <td>${p.nfl ?? '—'}</td>
          <td class="num">${p.projected != null ? Number(p.projected).toFixed(2) : '—'}</td>
          <td class="num">${p.actual != null ? Number(p.actual).toFixed(2) : '—'}</td>
        </tr>
      `).join('');

      return `
        <div class="card">
          <div class="team">${t.teamName ?? ('Team ' + (t.teamId ?? ''))}</div>
          <table>
            <thead>
              <tr>
                <th>Player</th><th>Position</th><th>NFL</th><th class="num">Projected</th><th class="num">Actual</th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      `;
    }).join('');
  }catch(e){
    container.innerHTML = `<div class="sub">Failed to load team_rosters.json (${e.message}).</div>`;
  }
}

document.addEventListener('DOMContentLoaded', load);
