(async function () {
  const $tbody   = document.getElementById("tbody");
  const $subtitle= document.getElementById("subtitle");
  const $stamp   = document.getElementById("stamp");
  const $refresh = document.getElementById("refresh");
  if ($refresh) $refresh.addEventListener("click", (e)=>{ e.preventDefault(); location.reload(true); });

  async function getJSON(url) {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) throw new Error(`${url} → ${res.status}`);
    return res.json();
  }

  function safeNum(x) {
    const n = Number(x);
    return Number.isFinite(n) ? n : 0;
  }

  // Extract rows from ESPN mStandings OR mTeam structure
  function buildRowsFromData(data) {
    // Try common layouts
    const teams = data?.teams || data?.standings?.entries || [];
    const rows = [];

    if (Array.isArray(teams) && teams.length && teams[0]?.name) {
      // Likely mStandings or mTeam team objects { name, record: { overall:{wins,losses,pointsFor,pointsAgainst}} }
      for (const t of teams) {
        const ovr = t.record?.overall || t.record?.overallRecord || {};
        rows.push({
          name: t.name || `Team ${t.id ?? ""}`,
          wins: safeNum(ovr.wins ?? ovr.w ?? 0),
          losses: safeNum(ovr.losses ?? ovr.l ?? 0),
          pf: safeNum(ovr.pointsFor ?? ovr.pf ?? 0),
          pa: safeNum(ovr.pointsAgainst ?? ovr.pa ?? 0)
        });
      }
      return rows;
    }

    if (Array.isArray(teams) && teams.length && teams[0]?.team) {
      // Layout like { standings:{ entries:[ {team:{id,location,nickname,abbrev}, stats:...} ] } }
      for (const e of teams) {
        const nm = e.team?.name || [e.team?.location, e.team?.nickname].filter(Boolean).join(" ") || `Team ${e.team?.id ?? ""}`;
        // Some variants have e.stats as array of {name,value} or nested object
        let wins=0, losses=0, pf=0, pa=0;
        if (Array.isArray(e.stats)) {
          for (const s of e.stats) {
            if (!s) continue;
            const key = (s.name || s.statId || "").toString().toLowerCase();
            if (key.includes("wins")) wins = safeNum(s.value);
            else if (key.includes("losses")) losses = safeNum(s.value);
            else if (key.includes("pointsfor") || key === "pf") pf = safeNum(s.value);
            else if (key.includes("pointsagainst") || key === "pa") pa = safeNum(s.value);
          }
        }
        rows.push({ name:nm, wins, losses, pf, pa });
      }
      return rows;
    }

    return rows; // empty
  }

  async function loadStandings() {
    $subtitle.textContent = "Loading standings...";
    let rows = [];
    let fetchedAt = null;

    try {
      // Primary: espn_mStandings.json
      const stRaw = await getJSON("data/espn_mStandings.json");
      const st = stRaw.data || stRaw; // we save {fetched_at, data:{...}}
      fetchedAt = stRaw.fetched_at || stRaw.generated_utc || new Date().toISOString();
      rows = buildRowsFromData(st);
    } catch (e) {
      console.warn("Failed espn_mStandings.json", e);
    }

    // Fallback to mTeam if standings didn’t produce rows
    if (!rows.length) {
      try {
        const tRaw = await getJSON("data/espn_mTeam.json");
        const t = tRaw.data || tRaw;
        fetchedAt = fetchedAt || tRaw.fetched_at || tRaw.generated_utc || new Date().toISOString();
        rows = buildRowsFromData(t);
      } catch (e) {
        console.warn("Failed espn_mTeam.json", e);
      }
    }

    if (!rows.length) {
      $subtitle.textContent = "Error loading ESPN standings. Check Actions/logs.";
      $tbody.innerHTML = "";
      if ($stamp) $stamp.textContent = "";
      return;
    }

    // Sort by wins desc, then PF desc as a tiebreaker
    rows.sort((a,b) => (b.wins - a.wins) || (b.pf - a.pf) );

    // Render
    const tr = rows.map(r => `
      <tr>
        <td>${r.name}</td>
        <td class="right">${r.wins}</td>
        <td class="right">${r.losses}</td>
        <td class="right">${r.pf.toFixed ? r.pf.toFixed(0) : r.pf}</td>
        <td class="right">${r.pa.toFixed ? r.pa.toFixed(0) : r.pa}</td>
      </tr>
    `).join("");

    $tbody.innerHTML = tr;
    $subtitle.textContent = "Live ESPN standings (hourly)";
    if ($stamp) $stamp.textContent = `fetched: ${fetchedAt}`;
  }

  loadStandings();
})();
