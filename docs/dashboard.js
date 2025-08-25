async function loadJSON(p){ return fetch(p).then(r=>r.json()); }

(async ()=>{
  const weekly = await loadJSON('./data/analysis/player_points_weekly.json');
  const l4     = await loadJSON('./data/analysis/player_form_last4.json');
  const players= await loadJSON('./data/analysis/players.json').catch(()=> ({}));

  // pick latest bucket
  const weeks = Object.keys(weekly).sort();
  const latest = weeks[weeks.length-1] || '';
  document.getElementById('meta').textContent = latest ? `· Data: ${latest}` : '';

  // Build leaders (overall top 12 by points; filter to RB/WR/TE/QB)
  const row = weekly[latest] || {};
  const arr = Object.entries(row)
    .map(([pid, v])=>({pid, ...v, name:(players[pid]?.name)||pid}))
    .filter(x=> ['QB','RB','WR','TE'].includes(x.pos))
    .sort((a,b)=> b.points - a.points)
    .slice(0,12);

  const leaders = document.getElementById('leaders');
  leaders.innerHTML = arr.map(x=>{
    const badge = `<span class="pill">${x.pos}</span><span class="pill">${x.team}</span><span class="pill">@${x.opp}</span>`;
    return `<div>${x.name} ${badge} — <b>${x.points.toFixed(2)}</b> pts</div>`;
  }).join('');

  // Hot hand: biggest positive gap (L4 avg vs latest week)
  const l4row = l4[latest] || {};
  const hotArr = arr
    .map(x => ({...x, l4: Number(l4row[x.pid] ?? 0)}))
    .map(x => ({...x, diff: x.points - x.l4}))
    .sort((a,b)=> (b.diff - a.diff))
    .slice(0,10);

  const hot = document.getElementById('hot');
  hot.innerHTML = hotArr.map(x=>{
    const cls = x.diff>=0 ? 'up':'down';
    const sign = x.diff>=0 ? '+' : '';
    return `<div>${x.name} — Week: <b>${x.points.toFixed(1)}</b> · L4: ${x.l4.toFixed(1)} · <span class="${cls}">${sign}${x.diff.toFixed(1)}</span></div>`;
  }).join('');
})();
