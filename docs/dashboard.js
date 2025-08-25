/* Dashboard visuals with robust loading + visible error messages.
   Files expected (under docs/data/analysis/):
   - player_points_weekly.json   // { "2025-W02": { playerId: {pos,team,opp,points}, ... } }
   - player_form_last4.json      // { "2025-W02": { playerId: 12.3, ... } }
   - players.json                // { playerId: {name,pos,team} }
*/

const STATUS = { ok:[], fail:[] };

function showStatus() {
  const el = document.getElementById('lastUpdated');
  const msg = [
    STATUS.fail.length ? `⚠ data errors: ${STATUS.fail.join(', ')}` : 'ready',
    STATUS.ok.length ? `· loaded: ${STATUS.ok.join(', ')}` : ''
  ].join(' ');
  el.textContent = (window._latestKey ? `· Data: ${window._latestKey} ` : '· ') + msg;
}

async function j(path, label){
  try {
    const res = await fetch(path, {cache:'no-store'});
    if(!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    const data = await res.json();
    STATUS.ok.push(label);
    showStatus();
    return data;
  } catch (e) {
    STATUS.fail.push(`${label} (${e.message||e})`);
    console.error(`Failed to load ${label} at ${path}:`, e);
    showStatus();
    return null;
  }
}

function parseKey(k){ const m = /(\d+)-W(\d+)/.exec(k)||[]; return { season:+m[1], week:+m[2] }; }
function sortKeys(ks){
  return ks.slice().sort((a,b)=>{
    const A=parseKey(a), B=parseKey(b);
    if(!A.season||!A.week) return -1;
    if(!B.season||!B.week) return 1;
    return A.season===B.season ? A.week-B.week : A.season-B.season;
  });
}
function fmt(n){ return Number(n).toFixed(1); }
function ensure(el){ if(!el){ throw new Error('Required canvas/input not found'); } return el; }

let WEEKLY={}, L4={}, PLAYERS={};
let barChart, donutChart, scatterChart, lineChart;

async function init(){
  // Try both "./" and no "./" paths to avoid path resolution issues on some hosts
  WEEKLY = await (await j('./data/analysis/player_points_weekly.json','weekly')) 
        || await j('data/analysis/player_points_weekly.json','weekly (alt)');
  L4     = await (await j('./data/analysis/player_form_last4.json','last4')) 
        || await j('data/analysis/player_form_last4.json','last4 (alt)');
  PLAYERS= await (await j('./data/analysis/players.json','players')) 
        || await j('data/analysis/players.json','players (alt)') 
        || {};

  const keys = WEEKLY ? sortKeys(Object.keys(WEEKLY)) : [];
  window._latestKey = keys.length ? keys[keys.length-1] : '';
  const latestKey = window._latestKey;

  // If no weekly data, tell the user plainly and stop
  if(!latestKey){
    document.getElementById('lastUpdated').textContent =
      '⚠ No weekly data found. Check that docs/data/analysis/player_points_weekly.json exists and is committed.';
    return;
  }

  // Populate controls
  try {
    const teams = new Set(Object.values(WEEKLY[latestKey]||{}).map(v=>v.team).filter(Boolean));
    const teamSelect = ensure(document.getElementById('teamSelect'));
    teamSelect.innerHTML = '';
    [...teams].sort().forEach(t=>{
      const o=document.createElement('option'); o.value=t; o.textContent=t; teamSelect.appendChild(o);
    });
  } catch (e) {
    console.error('Team select build failed:', e);
  }

  try {
    const dl = ensure(document.getElementById('playersList'));
    dl.innerHTML='';
    Object.entries(PLAYERS).forEach(([pid,p])=>{
      const opt=document.createElement('option'); opt.value=p.name; dl.appendChild(opt);
    });
  } catch (e) {
    console.error('Players datalist build failed:', e);
  }

  // Wire controls safely
  const posSelect = document.getElementById('posSelect');
  if(posSelect) posSelect.onchange = renderBar;
  const teamSelect = document.getElementById('teamSelect');
  if(teamSelect) teamSelect.onchange = renderDonut;
  const posScatter = document.getElementById('posScatter');
  if(posScatter) posScatter.onchange = renderScatter;
  const playerInput = document.getElementById('playerInput');
  if(playerInput) playerInput.onchange = renderLine;

  // First render
  renderBar();
  renderDonut();
  renderHot();
  renderScatter();
  renderLine();
  renderHeatmap();
  showStatus();
}

function currentLatestKey(){ return window._latestKey; }
function getWeeklyRow(){ const k=currentLatestKey(); return (WEEKLY && WEEKLY[k]) ? WEEKLY[k] : {}; }

// ---------- Top10 Bar ----------
function renderBar(){
  try{
    const pos = (document.getElementById('posSelect')?.value)||'RB';
    const row = getWeeklyRow();
    const arr = Object.entries(row)
      .map(([pid,v])=>({pid, ...v, name:(PLAYERS[pid]?.name)||pid}))
      .filter(x=> (x.pos||'').toUpperCase()===pos.toUpperCase())
      .sort((a,b)=> b.points-a.points)
      .slice(0,10);

    const ctx = ensure(document.getElementById('barTop10')).getContext('2d');
    barChart && barChart.destroy();
    barChart = new Chart(ctx, {
      type:'bar',
      data:{ 
        labels: arr.map(x=>x.name), 
        datasets:[{ label:`${pos} · last week points`, data: arr.map(x=>x.points) }]
      },
      options:{ responsive:true, plugins:{ legend:{display:false}, tooltip:{callbacks:{
        afterLabel:(ctx)=>{
          const x = arr[ctx.dataIndex];
          return `  ${x.team} vs ${x.opp}`;
        }}}}
    });
  }catch(e){ console.error('renderBar error', e); }
}

// ---------- Team Share Donut ----------
function renderDonut(){
  try{
    const team = (document.getElementById('teamSelect')?.value)||'';
    const row = getWeeklyRow();
    const vals = {QB:0,RB:0,WR:0,TE:0,K:0,DST:0};
    Object.values(row).forEach(v=>{
      if(team && v.team!==team) return;
      const p=(v.pos||'').toUpperCase();
      if(p in vals) vals[p]+= Number(v.points||0);
    });
    const labels = Object.keys(vals);
    const data = labels.map(k=> vals[k]);

    const ctx = ensure(document.getElementById('donutTeamShare')).getContext('2d');
    donutChart && donutChart.destroy();
    donutChart = new Chart(ctx,{
      type:'doughnut',
      data:{ labels, datasets:[{ data }]},
      options:{ plugins:{ legend:{ position:'bottom' } } }
    });
  }catch(e){ console.error('renderDonut error', e); }
}

// ---------- Hot Hand list ----------
function renderHot(){
  try{
    const row = getWeeklyRow();
    const l4row = (L4 && L4[currentLatestKey()]) ? L4[currentLatestKey()] : {};
    const arr = Object.entries(row).map(([pid,v])=>{
      const l4 = Number(l4row?.[pid]||0);
      return {pid, name: (PLAYERS[pid]?.name)||pid, ...v, l4, diff: Number(v.points)-l4};
    }).filter(x=> ['QB','RB','WR','TE'].includes((x.pos||'').toUpperCase()))
      .sort((a,b)=> b.diff - a.diff)
      .slice(0,12);

    const el = ensure(document.getElementById('hotList'));
    el.innerHTML = arr.map(x=>{
      const cls = x.diff>=0 ? 'style="color:#10b981"' : 'style="color:#f87171"';
      return `<div>${x.name} <span class="pill">${x.pos}</span> — Week: <b>${fmt(x.points)}</b> · L4: ${fmt(x.l4)} · <b ${cls}>${x.diff>=0?'+':''}${fmt(x.diff)}</b></div>`;
    }).join('') || '<div class="help">No data for this week.</div>';
  }catch(e){ console.error('renderHot error', e); }
}

// ---------- Consistency Scatter ----------
function renderScatter(){
  try{
    const posSel = (document.getElementById('posScatter')?.value)||'RB';
    const keys = WEEKLY ? sortKeys(Object.keys(WEEKLY)).filter(k=> parseKey(k).season===parseKey(currentLatestKey()).season && parseKey(k).week<=parseKey(currentLatestKey()).week) : [];
    const pointsByPlayer = new Map();
    keys.forEach(k=>{
      const row=WEEKLY[k]||{};
      Object.entries(row).forEach(([pid,v])=>{
        if((v.pos||'').toUpperCase()!==posSel.toUpperCase()) return;
        if(!pointsByPlayer.has(pid)) pointsByPlayer.set(pid, []);
        pointsByPlayer.get(pid).push(Number(v.points||0));
      });
    });
    const rows = [];
    for(const [pid, arr] of pointsByPlayer){
      if(arr.length<3) continue;
      const avg = arr.reduce((a,b)=>a+b,0)/arr.length;
      const sd = Math.sqrt(arr.map(x=>(x-avg)**2).reduce((a,b)=>a+b,0)/arr.length);
      rows.push({x:avg, y:sd, pid, name:(PLAYERS[pid]?.name)||pid});
    }
    const data = rows.sort((a,b)=> b.x-a.x).slice(0,60);

    const ctx = ensure(document.getElementById('scatterCons')).getContext('2d');
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
  }catch(e){ console.error('renderScatter error', e); }
}

// ---------- Player Trend ----------
function findPlayerIdByName(name){
  name = (name||'').toLowerCase().trim();
  if(!name) return null;
  for(const [pid,p] of Object.entries(PLAYERS)){ if((p.name||'').toLowerCase()===name) return pid; }
  for(const [pid,p] of Object.entries(PLAYERS)){ if((p.name||'').toLowerCase().includes(name)) return pid; }
  return null;
}
function renderLine(){
  try{
    const name = document.getElementById('playerInput')?.value || '';
    const pid = findPlayerIdByName(name);
    const ctx = ensure(document.getElementById('linePlayer')).getContext('2d');
    lineChart && lineChart.destroy();

    if(!pid){
      lineChart = new Chart(ctx,{type:'line', data:{labels:[],datasets:[]}, options:{plugins:{legend:{display:false}}}});
      return;
    }
    const keys = WEEKLY ? sortKeys(Object.keys(WEEKLY)) : [];
    const series = [];
    keys.forEach(k=>{
      const v = WEEKLY[k]?.[pid];
      if(v) series.push({k, pts:Number(v.points||0)});
    });
    const last8 = series.slice(-8);
    const labels = last8.map(s=> s.k);
    const vals = last8.map(s=> s.pts);
    const roll4 = vals.map((_,i,arr)=>{
      const start = Math.max(0, i-3);
      const seg = arr.slice(start, i+1);
      return seg.reduce((a,b)=>a+b,0)/seg.length;
    });

    lineChart = new Chart(ctx,{
      type:'line',
      data:{ labels, datasets:[
        { label:'Game points', data:vals },
        { label:'4‑game avg', data:roll4 }
      ]},
      options:{ plugins:{ legend:{ position:'bottom' }}}
    });
  }catch(e){ console.error('renderLine error', e); }
}

// ---------- Mini Heatmap ----------
function renderHeatmap(){
  try{
    const container = ensure(document.getElementById('heatmap'));
    container.innerHTML = '';
    const latestRow = getWeeklyRow();
    const top12 = Object.entries(latestRow).sort((a,b)=> b[1].points - a[1].points).slice(0,12);

    const keys = WEEKLY ? sortKeys(Object.keys(WEEKLY)).slice(-6) : [];
    const byPlayer = new Map();
    top12.forEach(([pid])=>{
      const vals=[];
      keys.forEach(k=>{ const v=WEEKLY[k]?.[pid]; vals.push(Number(v?.points||0)); });
      byPlayer.set(pid, vals);
    });

    function color(v){ if(v<=8) return '#1f2937'; if(v<=16) return '#0ea5e9'; return '#10b981'; }

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

    if(!top12.length){
      container.innerHTML = '<div class="help">No data to display.</div>';
    }
  }catch(e){ console.error('renderHeatmap error', e); }
}

// Start!
init();

// also surface unexpected JS errors visibly
window.addEventListener('error', (e)=>{
  const el = document.getElementById('lastUpdated');
  el.textContent = `JS error: ${e.message}`;
});
