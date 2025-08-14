// Reads: data/status.json and data/espn_mStandings.json
// Accepts either nested ESPN JSON or a flat array written by our fetcher.

const tbody = document.getElementById('tbody');
const lastUpdate = document.getElementById('lastUpdate');
const emptyEl = document.getElementById('empty');
const errEl = document.getElementById('error');
const spin = document.getElementById('spin');
const statusText = document.getElementById('statusText');
const refreshBtn = document.getElementById('refreshBtn');
const countEl = document.getElementById('count');

let timer, secs = 60;

function startCountdown(){
  clearInterval(timer);
  secs = 60;
  countEl.textContent = secs;
  timer = setInterval(()=>{
    secs -= 1;
    if(secs <= 0){ clearInterval(timer); load(); }
    countEl.textContent = secs;
  }, 1000);
}

function rowHtml(t){
  return `<tr>
      <td class="left">${t.teamName}</td>
      <td>${t.wins}</td>
      <td>${t.losses}</td>
      <td>${t.pointsFor}</td>
      <td>${t.pointsAgainst}</td>
    </tr>`;
}

function highlightLeader(rows){
  let bestIdx = -1, best = {wins:-1, pf:-1};
  rows.forEach((t, i) => {
    const w = Number(t.wins ?? -1);
    const pf = Number(t.pointsFor ?? -1);
    if (w > best.wins || (w === best.wins && pf > best.pf)) {
      bestIdx = i; best = {wins:w, pf:pf};
    }
  });
  if(bestIdx >= 0 && tbody.rows[bestIdx]){
    tbody.rows[bestIdx].classList.add('leader');
    const nameCell = tbody.rows[bestIdx].cells[0];
    nameCell.innerHTML = nameCell.innerHTML + `<span class="badge">Leader</span>`;
  }
}

async function fetchJson(path){
  const res = await fetch(path, { cache: 'no-store' });
  if(!res.ok) throw new Error(`${path} HTTP ${res.status}`);
  return await res.json();
}

// Map ESPN standings JSON -> flat rows for table
function mapStandings(json){
  // Case 1: already flat array from our fetcher
  if (Array.isArray(json)) {
    return json.map(x => ({
      teamName: x.teamName ?? '—',
      wins: Number(x.wins ?? 0),
      losses: Number(x.losses ?? 0),
      pointsFor: Number(x.pointsFor ?? 0),
      pointsAgainst: Number(x.pointsAgainst ?? 0),
    })).sort((a,b)=> (b.wins - a.wins) || (b.pointsFor - a.pointsFor));
  }

  // Case 2: our fetcher wrapped the raw ESPN object under { fetched_at, data: {...} }
  const payload = (json && json.data) ? json.data : json;

  // ESPN nested shape: payload.standings.entries = [ { team, stats: [...] } ]
  const entries = payload?.standings?.entries ?? payload?.entries ?? [];
  const rows = entries.map(e => {
    const teamName =
      e?.team?.displayName ||
      (e?.team?.location && e?.team?.nickname ? `${e.team.location} ${e.team.nickname}` :
       (e?.team?.nickname || e?.team?.location || '—'));

    const get = (name) => {
      const s = (e?.stats || []).find(x => x?.name === name);
      return (s && (s.value ?? s.displayValue)) ?? 0;
    };

    return {
      teamName,
      wins: Number(get('wins')),
      losses: Number(get('losses')),
      pointsFor: Number(get('pointsFor')),
      pointsAgainst: Number(get('pointsAgainst')),
    };
  });

  rows.sort((a,b)=> (b.wins - a.wins) || (b.pointsFor - a.pointsFor));
  return rows;
}

async function load(){
  spin.style.visibility = 'visible';
  statusText.textContent = 'Fetching data';
  errEl.classList.add('hidden');

  try{
    const [statusJson, standingsJson] = await Promise.all([
      fetchJson('data/status.json').catch(()=>({generated_utc: null})),
      fetchJson('data/espn_mStandings.json')
    ]);

    const ts = statusJson.generated_utc || new Date().toISOString();
    lastUpdate.textContent = `Last updated (UTC): ${ts}`;

    const rows = mapStandings(standingsJson);
    tbody.innerHTML = '';
    if(!rows.length){
      emptyEl.classList.remove('hidden');
    } else {
      emptyEl.classList.add('hidden');
      rows.forEach(t => tbody.insertAdjacentHTML('beforeend', rowHtml(t)));
      highlightLeader(rows);
    }

    statusText.textContent = 'Up to date';
  } catch(err){
    console.error(err);
    errEl.classList.remove('hidden');
    statusText.textContent = 'Fetch failed';
  } finally{
    spin.style.visibility = 'hidden';
    startCountdown();
  }
}

refreshBtn.addEventListener('click', ()=> load());
document.addEventListener('DOMContentLoaded', load);
