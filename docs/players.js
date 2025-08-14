let DATA = [];

function byKey(key){
  const desc = key.startsWith("-");
  const k = desc ? key.slice(1) : key;
  return (a,b)=>{
    const av = a[k], bv = b[k];
    if (typeof av === "number" && typeof bv === "number"){
      return desc ? (bv-av) : (av-bv);
    }
    const as = (av ?? "").toString().toLowerCase();
    const bs = (bv ?? "").toString().toLowerCase();
    if (as < bs) return desc ? 1 : -1;
    if (as > bs) return desc ? -1 : 1;
    return 0;
  };
}

function render(){
  const q = document.getElementById('search').value.trim().toLowerCase();
  const pos = document.getElementById('pos').value;
  const sort = document.getElementById('sort').value;

  let rows = DATA.slice(0);
  if (q){
    rows = rows.filter(r =>
      (r.name || "").toLowerCase().includes(q) ||
      (r.team || "").toLowerCase().includes(q)
    );
  }
  if (pos){
    rows = rows.filter(r => r.position === pos);
  }
  rows.sort(byKey(sort));

  document.getElementById('tbody').innerHTML = rows.map(r => `
    <tr>
      <td>${r.name ?? '—'}</td>
      <td>${r.position ?? '—'}</td>
      <td>${r.team ?? '—'}</td>
      <td class="num">${Math.round(Number(r.proj_season ?? 0))}</td>
      <td class="num">${Number(r.recent_avg ?? 0).toFixed(2)}</td>
    </tr>
  `).join('');
}

async function load(){
  try{
    const res = await fetch('data/players_summary.json', {cache:'no-store'});
    if(!res.ok) throw new Error(`HTTP ${res.status}`);
    const j = await res.json();
    DATA = Array.isArray(j.rows) ? j.rows : [];
    render();
  }catch(e){
    document.getElementById('tbody').innerHTML =
      `<tr><td colspan="5">Failed to load player data (${e.message}).</td></tr>`;
  }
}

['search','pos','sort'].forEach(id => {
  document.getElementById(id).addEventListener('input', render);
  document.getElementById(id).addEventListener('change', render);
});

document.addEventListener('DOMContentLoaded', load);
