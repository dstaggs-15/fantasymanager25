(async function () {
  const $grid = document.getElementById("teams");
  const $stamp = document.getElementById("stamp");

  async function getJSON(url) {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) throw new Error(`GET ${url} → ${res.status}`);
    return res.json();
  }

  function ownerName(membersById, ownerId) {
    const m = membersById[ownerId];
    if (!m) return "Unknown";
    const first = (m.firstName || "").trim();
    const last = (m.lastName || "").trim();
    const display = (m.displayName || "").trim();
    const name = [first, last].filter(Boolean).join(" ").trim();
    return name || display || "Unknown";
  }

  function htm(strings, ...vals) {
    return strings.reduce((acc, s, i) => acc + s + (vals[i] ?? ""), "");
  }

  try {
    const teamJson = await getJSON("data/espn_mTeam.json");
    // We stored it as { fetched_at, data: {... real espn json ...} }
    const data = teamJson.data || teamJson;

    // Stamp
    const fetchedAt = teamJson.fetched_at || new Date().toISOString();
    $stamp.textContent = `fetched: ${fetchedAt}`;

    const members = data.members || [];
    const teams = data.teams || [];
    const divisions = {}; // id -> name (if divisions exist in mSettings we can enrich later)

    // Build quick lookup of members by id
    const membersById = {};
    for (const m of members) {
      if (m.id) membersById[m.id] = m;
    }

    // Sort by team id (stable display)
    teams.sort((a, b) => (a.id || 0) - (b.id || 0));

    // Render cards
    const cards = teams.map(t => {
      const logo = t.logo || "https://g.espncdn.com/lm-static/ffl/images/default_logos/01.svg";
      const nm = (t.name || `Team ${t.id}`).trim();
      const ownerId = (t.primaryOwner || (t.owners && t.owners[0])) || "";
      const own = ownerName(membersById, ownerId);
      const div = (t.divisionId != null) ? `Division ${t.divisionId}` : "No division";
      const waiver = (t.waiverRank != null) ? `Waiver #${t.waiverRank}` : "Waiver —";

      return htm`
        <div class="card">
          <div class="row">
            <img class="logo" src="${logo}" alt="logo">
            <div>
              <div class="teamname">${nm}</div>
              <div class="owner">${own}</div>
            </div>
          </div>
          <div class="meta">
            <div class="chip">${div}</div>
            <div class="chip">${waiver}</div>
            <div class="chip">ID ${t.id}</div>
          </div>
        </div>
      `;
    });

    $grid.innerHTML = cards.join("");

  } catch (err) {
    console.error(err);
    $grid.innerHTML = `<div class="muted">Failed to load teams: ${String(err).slice(0,200)}</div>`;
  }
})();
