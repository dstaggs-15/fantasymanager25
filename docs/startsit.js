/* Start/Sit comparator UI
   Inputs:
   - ./data/analysis/start_sit_report.json  // built by start_sit_calculator.py
   - ./data/analysis/players.json           // from player_points.py
*/
async function j(p){ return fetch(p, {cache:'no-store'}).then(r=>r.json()); }

let REPORT={}, PLAYERS={};
let latestKey = "";

function parseKey(k){ const m=/(\d+)-W(\d+)/.exec(k)||[]; return {season:+m[1], week:+m[2]}; }
function sortKeys(ks){
  return ks.slice().sort((a,b)=>{
    const A=parseKey(a), B=parseKey(b);
    return A.season===B.season ? A.week-B.week : A.season-B.season;
  });
}

(async function init(){
  REPORT = await j('./data/analysis/start_sit_report.json').catch(()=> ({}));
  PLAYERS = await j('./data/analysis/players.json').catch(()=> ({}));
  const keys = sortKeys(Object.keys(REPORT));
  latestKey = keys[keys.length-1] || '';
  document.getElementById('meta').textContent = latestKey ? `Data: ${latestKey}` : 'No data found';

  // build datalist
  const dl = document.getElementById('playersList');
  const seen = new Set();
  if(latestKey && REPORT[latestKey]){
    Object.entries(REPORT[latestKey]).forEach(([pid,p])=>{
      const nm = p.player || (PLAYERS[pid]?.name) || '';
      if(!nm || seen.has(nm)) return;
      const o=document.createElement('option'); o.value=nm; dl.appendChild(o);
      seen.add(nm);
    });
  } else {
    // fallback to players.json if report empty
    Object.values(PLAYERS).forEach(p=>{
      const o=document.createElement('option'); o.value=p.name; dl.appendChild(o);
    });
  }

  document.getElementById('go').onclick = compare;
})();

function findByNameLatest(name){
  name = (name||'').toLowerCase().trim();
  if(!latestKey || !REPORT[latestKey]) return null;
  let best = null;
  for(const [pid, p] of Object.entries(REPORT[latestKey])){
    const nm = (p.player || PLAYERS[pid]?.name || '').toLowerCase();
    if(nm === name || (name && nm.includes(name))) { best = {pid, ...p}; break; }
  }
  return best;
}

let radarA, radarB;

function compare(){
  const aName = document.getElementById('p1').value;
  const bName = document.getElementById('p2').value;
  const A = findByNameLatest(aName);
  const B = findByNameLatest(bName);

  const result = document.getElementById('result');
  const headline = document.getElementById('headline');

  if(!A || !B){
    result.style.display = 'block';
    headline.innerHTML = '⚠ Could not find one or both players in the latest week.';
    document.getElementById('aName').textContent = aName||'—';
    document.getElementById('bName').textContent = bName||'—';
    document.getElementById('aMeta').textContent = '';
    document.getElementById('bMeta').textContent = '';
    return;
  }

  const winner = A.score >= B.score ? 'A' : 'B';
  const diff = Math.abs(A.score - B.score).toFixed(1);
  const wName = winner==='A' ? (A.player||aName) : (B.player||bName);
  headline.innerHTML = `Recommend: <span class="${winner==='A'?'winner':'loser'}">${wName}</span> (by +${diff})`;

  // Names + meta
  document.getElementById('aName').textContent = `${A.player||aName} · ${A.pos} · ${A.team} vs ${A.opp} · Score ${A.score}`;
  document.getElementById('bName').textContent = `${B.player||bName} · ${B.pos} · ${B.team} vs ${B.opp} · Score ${B.score}`;
  document.getElementById('aMeta').textContent = explain(A.components);
  document.getElementById('bMeta').textContent = explain(B.components);

  // Radar charts
  const labels = ['usage','eff','oline','opp','env','cons'];
  const ctxA = document.getElementById('aRadar').getContext('2d');
  const ctxB = document.getElementById('bRadar').getContext('2d');
  radarA && radarA.destroy(); radarB && radarB.destroy();

  const toPct = c => labels.map(k=> Math.round(100*(c[k] ?? 0.5)));

  radarA = new Chart(ctxA, {
    type:'radar',
    data:{ labels: labels.map(x=>x.toUpperCase()), datasets:[{ label:'Components', data: toPct(A.components) }]},
    options:{ scales:{ r:{ suggestedMin:0, suggestedMax:100 }}, plugins:{legend:{display:false}} }
  });
  radarB = new Chart(ctxB, {
    type:'radar',
    data:{ labels: labels.map(x=>x.toUpperCase()), datasets:[{ label:'Components', data: toPct(B.components) }]},
    options:{ scales:{ r:{ suggestedMin:0, suggestedMax:100 }}, plugins:{legend:{display:false}} }
  });

  result.style.display = 'block';
}

function explain(c){
  // Return top 3 components by strength as readable text
  const entries = Object.entries(c||{}).sort((a,b)=> b[1]-a[1]).slice(0,3);
  return 'Top drivers: ' + entries.map(([k,v])=> `${k.toUpperCase()} ${Math.round(v*100)}%`).join(' • ');
}
