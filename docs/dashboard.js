document.addEventListener('DOMContentLoaded', async () => {
    // --- Data Loading ---
    let allPlayers = [];
    let matchupData = {};
    let teamData = {};
    let chartInstances = {}; // To manage and destroy old charts

    try {
        const [vorpRes, matchupRes, teamRes] = await Promise.all([
            fetch('data/analysis/vorp_analysis.json'),
            fetch('data/analysis/matchup_report.json'),
            fetch('data/analysis/team_rankings.json')
        ]);
        if (!vorpRes.ok || !matchupRes.ok || !teamRes.ok) throw new Error('Failed to load analysis files.');

        const vorpData = await vorpRes.json();
        matchupData = await matchupRes.json();
        teamData = await teamRes.json();
        allPlayers = vorpData.players;

        // --- Initial Page Renders ---
        populateDatalist(allPlayers);
        renderTopMatchups(matchupData.matchups);
        renderDefensiveChart(teamData.fantasy_points_allowed);

    } catch (error) {
        console.error("Dashboard failed to load:", error);
    }

    // --- Player Comparison Logic ---
    const player1Search = document.getElementById('player1-search');
    const player2Search = document.getElementById('player2-search');
    const comparisonResults = document.getElementById('comparison-results');

    function updateComparison() {
        const name1 = player1Search.value;
        const name2 = player2Search.value;
        const player1 = allPlayers.find(p => p.player_display_name === name1);
        const player2 = allPlayers.find(p => p.player_display_name === name2);
        
        comparisonResults.innerHTML = '';
        if (player1 && player2) {
            // Add containers for the new stats and charts
            comparisonResults.innerHTML = `
                <div class="table-container" style="margin-top: 2rem;">
                    <table id="comparison-table"></table>
                </div>
                <div class="report-grid" style="margin-top: 2rem;">
                    <div class="report-card">
                        <h3>Fantasy Point Composition</h3>
                        <canvas id="composition-chart"></canvas>
                    </div>
                    <div class="report-card">
                        <h3>Raw Stats Comparison</h3>
                        <canvas id="raw-stats-chart"></canvas>
                    </div>
                </div>
            `;
            renderComparisonTable(player1, player2);
            renderCompositionChart(player1, player2);
            renderRawStatsChart(player1, player2);
        }
    }
    player1Search.addEventListener('input', updateComparison);
    player2Search.addEventListener('input', updateComparison);
    
    function populateDatalist(players) {
        const playerDatalist = document.getElementById('player-list');
        players.sort((a, b) => a.player_display_name.localeCompare(b.player_display_name));
        players.forEach(p => {
            const option = document.createElement('option');
            option.value = p.player_display_name;
            playerDatalist.appendChild(option);
        });
    }

    function renderComparisonTable(p1, p2) {
        const table = document.getElementById('comparison-table');
        const statsToCompare = [
            { label: 'Position', key: 'position' },
            { label: 'Fantasy PPG', key: 'ppg' },
            { label: 'VORP', key: 'vorp' },
            { label: 'Pass Yds/Game', key: 'passing_yards_pg' },
            { label: 'Rush Yds/Game', key: 'rushing_yards_pg' },
            { label: 'Rec Yds/Game', key: 'receiving_yards_pg' }
        ];
        let tableHTML = `<thead><tr><th>Stat</th><th>${p1.player_display_name}</th><th>${p2.player_display_name}</th></tr></thead><tbody>`;
        statsToCompare.forEach(stat => {
            const val1 = p1[stat.key] !== undefined ? p1[stat.key].toFixed(2) : 'N/A';
            const val2 = p2[stat.key] !== undefined ? p2[stat.key].toFixed(2) : 'N/A';
            if (parseFloat(val1) > 0 || parseFloat(val2) > 0 || stat.key === 'position') {
                 tableHTML += `<tr><td>${stat.label}</td><td>${val1}</td><td>${val2}</td></tr>`;
            }
        });
        tableHTML += `</tbody>`;
        table.innerHTML = tableHTML;
    }

    function renderCompositionChart(p1, p2) {
        if (chartInstances.composition) chartInstances.composition.destroy();
        const ctx = document.getElementById('composition-chart').getContext('2d');
        
        const getComposition = (player) => [
            player.passing_yards_pg * 0.05,
            player.rushing_yards_pg * 0.1,
            player.receiving_yards_pg * 0.1,
            (player.passing_tds_pg + player.rushing_tds_pg + player.receiving_tds_pg) * 6, // Simplified TD avg
            player.receptions_pg * 1
        ];

        chartInstances.composition = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Pass Yds', 'Rush Yds', 'Rec Yds', 'TDs', 'Receptions'],
                datasets: [
                    { label: p1.player_display_name, data: getComposition(p1) },
                    { label: p2.player_display_name, data: getComposition(p2) }
                ]
            },
            options: { plugins: { legend: { position: 'top', labels: { color: '#e0e0e0' } } } }
        });
    }

    function renderRawStatsChart(p1, p2) {
        if (chartInstances.rawStats) chartInstances.rawStats.destroy();
        const ctx = document.getElementById('raw-stats-chart').getContext('2d');
        const labels = ['Pass Yds', 'Rush Yds', 'Rec Yds'];
        chartInstances.rawStats = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    { label: p1.player_display_name, data: [p1.passing_yards_pg, p1.rushing_yards_pg, p1.receiving_yards_pg], backgroundColor: 'rgba(3, 218, 198, 0.6)' },
                    { label: p2.player_display_name, data: [p2.passing_yards_pg, p2.rushing_yards_pg, p2.receiving_yards_pg], backgroundColor: 'rgba(255, 99, 132, 0.6)' }
                ]
            },
            options: {
                scales: { x: { ticks: { color: '#e0e0e0' } }, y: { ticks: { color: '#e0e0e0' } } },
                plugins: { legend: { labels: { color: '#e0e0e0' } } }
            }
        });
    }

    // --- Other Dashboard Rendering Functions ---
    function renderTopMatchups(matchups) {
        const container = document.getElementById('top-matchups');
        const sorted = matchups.sort((a,b) => b.projection - a.projection).slice(0, 10);
        let listHTML = '<ul>';
        sorted.forEach(m => {
            listHTML += `<li><strong>${m.player} (${m.position}, ${m.opponent})</strong> - ${m.rating} Matchup</li>`;
        });
        listHTML += '</ul>';
        container.innerHTML = listHTML;
    }

    function renderDefensiveChart(fpaData) {
        const teams = Object.keys(fpaData);
        const totalPointsAllowed = teams.map(team => (fpaData[team].RB || 0) + (fpaData[team].WR || 0) + (fpaData[team].TE || 0));
        const sortedData = teams.map((team, i) => ({team, points: totalPointsAllowed[i]}))
            .sort((a,b) => b.points - a.points).slice(0, 5);

        const ctx = document.getElementById('defensive-chart').getContext('2d');
        new Chart(ctx,
