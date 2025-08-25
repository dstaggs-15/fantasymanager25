/* Dashboard visuals.
   Uses:
   - ./data/analysis/player_points_weekly.json   // { "2025-W02": { playerId: {pos,team,opp,points}, ... } }
   - ./data/analysis/player_form_last4.json      // { "2025-W02": { playerId: 12.3, ... } }
   - ./data/analysis/players.json                // { playerId: {name,pos,team} }
*/

async function j(path){ return fetch(path).then(r=>r.json()); }

function parseKey(k){ // "2025-W02" -> {season:2025, week:2}
  const m = /(\d+)-W(\d+)/.exec(k)||[];
  return { season: +m[1], week: +m[2] };
}
function sortKeys(ks){
  return ks.slice().sort((a,b)=>{
    const A=parseKey(a), B=parseKey(b);
    return A.season===B.season ? A.week-B.week : A.season-B.season;
  });
}
function fmt(n){ return Number(n).toFixed(1); }

let WEEKLY={}, L4={}, PLAYERS={};
let latestKey="", latestSeason=0, latestWeek=0;

let barChart, donutChart, scatterChart, lineChart;

(async function init(){
  [WEEKLY, L4, PLAYERS] = await Promise.all([
    j('./data/analysis/player_points_weekly.json'),
    j('./data/analysis/player_form_last4.json'),
    j('./data/analysis/players.json').catch(()=> ({}))
  ]);

  const keys = sortKeys(Object.keys(WEEKLY));
  latestKey = keys[keys.length-1] || "";
  ({season:latestSeason, week:latestWeek} = parseKey(latestKey));

  document.getElementById('lastUpdated').textContent = latestKey ? `· Data: ${latestKey}` : '';

  // Populate team select + player datalist
  const teams = new Set(Object.values(WEEKLY[latestKey]||{}).map(v=>v.team));
  const teamSelect = document.getElementById('teamSelect');
  [...teams].sort().forEach(t=>{
    const o=document.createElement('option'); o.value=t; o.textContent=t; teamSelect.appendChild(o);
  });
  const dl = document.getElementById('playersList');
  Object.entries(PLAYERS).forEach(([pid,p])=>{
    const opt=document.createElement('option'); opt.value=p.name; dl.appendChild(opt);
  });

  // Wire controls
  document.getElementById('posSelect').addEventListener('change', renderBar);
  document.getElementById('teamSelect').addEventListener('change', renderDonut);
  document.getElementById('posScatter').addEventListener('change', renderScatter);
  document.getElementById('playerInput').addEventListener('change', renderLine);

  renderBar();
  renderDonut();
  renderHot();
  renderScatter();
  renderLine();       // empty -> no plot until you pick, but safe to call
  renderHeatmap();
})();

// ---------- Top10 Bar ----------
function renderBar(){
  const pos = document.getElementById('posSelect').value;
  const row = WEEKLY[latestKey] || {};
  const arr = Object.entries(row)
    .map(([pid,v])=>({pid, ...v, name:(PLAYERS[pid]?.name)||pid}))
    .filter(x=> x.pos===pos)
    .sort((a,b)=> b.points-a.points)
    .slice(0,10);
  const labels = arr.map(x=> x.name);
  const values = arr.map(x=> x.points);

  const ctx = document.getElementById('barTop10').getContext('2d');
  barChart && barChart.destroy();
  barChart = new Chart(ctx, {
    type:'bar',
    data:{ labels, datasets:[{ label:`${pos} · last week points`, data:values }]},
    options:{ responsive:true, plugins:{ legend:{display:false}, tooltip:{callbacks:{
      afterLabel:(ctx)=>{
        const x = arr[ctx.dataIndex];
        return ` ${x.team} vs ${x.opp}`;
      }}}}
  });
}

// ---------- Team Share Donut ----------
function renderDonut(){
  const team = document.getElementById('teamSelect').value || '';
  const row = WEEKLY[latestKey] || {};
  const vals = {QB:0,RB:0,WR:0,TE:0,K:0,DST:0};
  Object.values(row).forEach(v=>{ if(v.team===team){ vals[v.pos] = (vals[v.pos]||0)+Number(v.points||0); }});
  const labels = Object.keys(vals);
  const data = labels.map(k=> vals[k]);

  const ctx = document.getElementById('donutTeamShare').getContext('2d');
  donutChart && donutChart.destroy();
  donutChart = new Chart(ctx,{
    type:'doughnut',
    data:{ labels, datasets:[{ data }]},
    options:{ plugins:{ legend:{ position:'bottom' } } }
  });
}

// ---------- Hot Hand list ----------
function renderHot(){
  const row = WEEKLY[latestKey] || {};
  const l4row = L4[latestKey] || {};
  const arr = Object.entries(row).map(([pid,v])=>{
    const l4 = Number(l4row[pid]||0);
    return {pid, name: (PLAYERS[pid]?.name)||pid, ...v, l4, diff: Number(v.points)-l4};
  }).filter(x=> ['QB','RB','WR','TE'].includes(x.pos))
    .sort((a,b)=> b.diff - a.diff)
    .slice(0,12);

  const el = document.getElementById('hotList');
  el.innerHTML = arr.map(x=>{
    const cls = x.diff>=0 ? 'style="color:#10b981"' : 'style="color:#f87171"';
    return `<div>${x.name} <span class="pill">${x.pos}</span> — Week: <b>${fmt(x.points)}</b> · L4: ${fmt(x.l4)} · <b ${cls}>${x.diff>=0?'+':''}${fmt(x.diff)}</b></div>`;
  }).join('');
}

// ---------- Consistency Scatter (avg vs stdev up to latest week) ----------
function renderScatter(){
  const pos = document.getElementById('posScatter').value;
  // Build time series per player this season
  const keys = sortKeys(Object.keys(WEEKLY)).filter(k=> parseKey(k).season===latestSeason && parseKey(k).week<=latestWeek);
  const pointsByPlayer = new Map();
  keys.forEach(k=>{
    Object.entries(WEEKLY[k]||{}).forEach(([pid,v])=>{
      if(v.pos!==pos) return;
      if(!pointsByPlayer.has(pid)) pointsByPlayer.set(pid, []);
      pointsByPlayer.get(pid).push(Number(v.points||0));
    });
  });
  const rows = [];
  for(const [pid, arr] of pointsByPlayer){
    if(arr.length<4) continue; // need sample
    const avg = arr.reduce((a,b)=>a+b,0)/arr.length;
    const sd = Math.sqrt(arr.map(x=>(x-avg)**2).reduce((a,b)=>a+b,0)/arr.length);
    rows.push({x:avg, y:sd, pid, name:(PLAYERS[pid]?.name)||pid});
  }
  rows.sort((a,b)=> b.x-a.x);
  const data = rows.slice(0,60); // cap for readability

  const ctx = document.getElementById('scatterCons').getContext('2d');
  scatterChart && scatterChart.destroy();
  scatterChart = new Chart(ctx,{
    type:'scatter',
    data:{ datasets:[{ data, parsing:false, showLine:false }]},
    options:{
      plugins:{ legend:{display:false}, tooltip:{callbacks:{
        label:(ctx)=> `${ctx.raw.name}: avg ${fmt(ctx.raw.x)}, stdev ${fmt(ctx.raw.y)}`
      }}},
      scales:{ x:{ title:{display:true, text:'Avg Pts'}}, y:{ title:{display:true, text:'Stdev (lower = steadier)'}}}
    }
  });
}

// ---------- Player Trend ----------
function findPlayerIdByName(name){
  name = (name||'').toLowerCase().trim();
  if(!name) return null;
  for(const [pid,p] of Object.entries(PLAYERS)){ if((p.name||'').toLowerCase()===name) return pid; }
  // fallback: partial match
  for(const [pid,p] of Object.entries(PLAYERS)){ if((p.name||'').toLowerCase().includes(name)) return pid; }
  return null;
}
function renderLine(){
  const name = document.getElementById('playerInput').value;
  const pid = findPlayerIdByName(name);
  const ctx = document.getElementById('linePlayer').getContext('2d');
  lineChart && lineChart.destroy();
  if(!pid){ lineChart = new Chart(ctx,{type:'line', data:{labels:[],datasets:[]}, options:{plugins:{legend:{display:false}}}}); return; }

  const keys = sortKeys(Object.keys(WEEKLY));
  const series = [];
  keys.forEach(k=>{
    const v = WEEKLY[k][pid];
    if(v) series.push({k, pts:Number(v.points||0)});
  });
  const last8 = series.slice(-8);
  const labels = last8.map(s=> s.k);
  const vals = last8.map(s=> s.pts);
  // rolling 4
  const roll4 = vals.map((_,i,arr)=>{
    const start = Math.max(0, i-3);
    const seg = arr.slice(start, i+1);
    return seg.reduce((a,b)=>a+b,0)/seg.length;
  });

  lineChart = new Chart(ctx,{
    type:'line',
    data:{ labels,
      datasets:[
        { label:'Game points', data:vals },
        { label:'4‑game avg', data:roll4 }
      ]},
    options:{ plugins:{ legend:{ position:'bottom' }}}
  });
}

// ---------- Mini Heatmap (top 12 from last week, last 6 games) ----------
function renderHeatmap(){
  const container = document.getElementById('heatmap');
  container.innerHTML = ''; // 7 columns label + 6 weeks grid
  const latestRow = WEEKLY[latestKey] || {};
  const top12 = Object.entries(latestRow).sort((a,b)=> b[1].points - a[1].points).slice(0,12);

  // Build a map: player -> last 6 values
  const keys = sortKeys(Object.keys(WEEKLY)).slice(-6);
  const byPlayer = new Map();
  top12.forEach(([pid])=>{
    const vals=[];
    keys.forEach(k=>{
      const v=WEEKLY[k][pid];
      vals.push(Number(v?.points||0));
    });
    byPlayer.set(pid, vals);
  });

  // Simple color scale
  function color(v){
    if(v<=8) return '#1f2937';   // low
    if(v<=16) return '#0ea5e9';  // med
    return '#10b981';            // high
  }

  // Render rows: name left (spanning full width), then 6 cells
  byPlayer.forEach((vals,pid)=>{
    const name=(PLAYERS[pid]?.name)||pid;
    const lab=document.createElement('div');
    lab.textContent = name;
    lab.style.gridColumn='1 / span 7';
    lab.style.marginTop='6px';
    lab.style.color='#e5e7eb';
    container.appendChild(lab);

    vals.forEach(v=>{
      const c=document.createElement('div');
      c.className='cell';
      c.style.background = color(v);
      container.appendChild(c);
    });
  });
}
