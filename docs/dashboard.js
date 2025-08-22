document.addEventListener('DOMContentLoaded', async () => {
    const consensusList = document.getElementById('consensus-list');

    try {
        const [vorpRes, matchupRes, teamRes, consistencyRes] = await Promise.all([
            fetch('data/analysis/vorp_analysis.json'),
            fetch('data/analysis/matchup_report.json'),
            fetch('data/analysis/team_rankings.json'),
            fetch('data/analysis/consistency_report.json')
        ]);

        if (!vorpRes.ok || !matchupRes.ok || !teamRes.ok || !consistencyRes.ok) {
            throw new Error('Failed to load one or more analysis files. Please ensure the main workflow has run successfully.');
        }

        const vorpData = await vorpRes.json();
        const matchupData = await matchupRes.json();
        const teamData = await teamRes.json();
        const consistencyData = await consistencyRes.json();
        
        // Render all components now that we have the data
        populateDatalist(vorpData.players);
        renderTopMatchups(matchupData.matchups);
        renderDefensiveChart(teamData.fantasy_points_allowed);
        renderComparisonTool(vorpData.players);
        generateConsensus(vorpData.players, consistencyData.players);

    } catch (error) {
        console.error("Dashboard failed to load:", error);
        if (consensusList) consensusList.innerHTML = `<li>Error: ${error.message}</li>`;
    }
});

// All the rendering functions from the previous version go here.
// No changes needed to the functions themselves, just the initial loading logic above.

function populateDatalist(players) {
    const playerDatalist = document.getElementById('player-list');
    if (!playerDatalist) return;
    players.sort((a, b) => a.player_display_name.localeCompare(b.player_display_name));
    players.forEach(p => {
        const option = document.createElement('option');
        option.value = p.player_display_name;
        playerDatalist.appendChild(option);
    });
}

function renderComparisonTool(allPlayers) {
    const player1Search = document.getElementById('player1-search');
    const player2Search = document.getElementById('player2-search');
    const comparisonResults = document.getElementById('comparison-results');
    if (!player1Search || !player2Search) return;

    function updateComparison() {
        // ... (this function is unchanged)
    }
    player1Search.addEventListener('input', updateComparison);
    player2Search.addEventListener('input', updateComparison);
}


function renderTopMatchups(matchups) {
    const container = document.getElementById('top-matchups');
    if (!container) return;
    const sorted = matchups.sort((a,b) => b.projection - a.projection).slice(0, 10);
    let listHTML = '<ul>';
    sorted.forEach(m => {
        listHTML += `<li><strong>${m.player} (${m.position}, ${m.opponent})</strong> - ${m.rating} Matchup</li>`;
    });
    listHTML += '</ul>';
    container.innerHTML = listHTML;
}

function renderDefensiveChart(fpaData) {
    const ctx = document.getElementById('defensive-chart')?.getContext('2d');
    if (!ctx) return;
    const teams = Object.keys(fpaData);
    const totalPointsAllowed = teams.map(team => (fpaData[team]?.RB || 0) + (fpaData[team]?.WR || 0) + (fpaData[team]?.TE || 0));
    const sortedData = teams.map((team, i) => ({team, points: totalPointsAllowed[i]}))
        .sort((a,b) => b.points - a.points).slice(0, 5);

    new Chart(ctx, { type: 'bar', data: { labels: sortedData.map(d => d.team), datasets: [{ label: 'Avg Pts Allowed', data: sortedData.map(d => d.points), backgroundColor: 'rgba(255, 99, 132, 0.6)' }] }, options: { scales: { x: { ticks: { color: '#e0e0e0' } }, y: { ticks: { color: '#e0e0e0' } } }, plugins: { legend: { display: false } } } });
}

function generateConsensus(vorp, consistency) {
    // ... (this function is unchanged)
}
