document.addEventListener('DOMContentLoaded', async () => {
    // --- Global variables to hold our data ---
    let allPlayers = [];
    let matchupData = {};
    let teamData = {};
    let chartInstances = {}; // To manage and destroy old charts

    try {
        // --- Data Loading ---
        // Load all necessary data files in parallel for speed
        const [vorpRes, matchupRes, teamRes] = await Promise.all([
            fetch('data/analysis/vorp_analysis.json'),
            fetch('data/analysis/matchup_report.json'),
            fetch('data/analysis/team_rankings.json')
        ]);
        if (!vorpRes.ok || !matchupRes.ok || !teamRes.ok) throw new Error('Failed to load one or more analysis files.');

        const vorpData = await vorpRes.json();
        matchupData = await matchupRes.json();
        teamData = await teamRes.json();
        allPlayers = vorpData.players;

        // --- Initial Page Renders ---
        // Once all data is loaded, build the page components
        initializeComparisonTool(allPlayers);
        renderTopMatchups(matchupData.matchups);
        renderDefensiveChart(teamData.fantasy_points_allowed);

    } catch (error) {
        console.error("Dashboard failed to load:", error);
        // Display an error on the page if data loading fails
        const comparisonResults = document.getElementById('comparison-results');
        if(comparisonResults) comparisonResults.innerHTML = `<p style="color: #F44336;">Error: Could not load data. Please ensure the main workflow has run successfully.</p>`;
    }

    // --- Player Comparison Tool ---
    function initializeComparisonTool(players) {
        const player1Search = document.getElementById('player1-search');
        const player2Search = document.getElementById('player2-search');
        const comparisonResults = document.getElementById('comparison-results');
        const playerDatalist = document.getElementById('player-list');

        // Populate the search box dropdown with player names
        players.sort((a, b) => a.player_display_name.localeCompare(b.player_display_name));
        players.forEach(p => {
            const option = document.createElement('option');
            option.value = p.player_display_name;
            playerDatalist.appendChild(option);
        });

        // This function runs whenever you select a player
        function updateComparison() {
            const name1 = player1Search.value;
            const name2 = player2Search.value;
            const player1 = players.find(p => p.player_display_name === name1);
            const player2 = players.find(p => p.player_display_name === name2);
            
            comparisonResults.innerHTML = ''; // Clear previous results
            if (player1 && player2) {
                // THE FIX: Create the containers for the table and charts
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
                            <h3>Per-Game Stat Comparison</h3>
                            <canvas id="raw-stats-chart"></canvas>
                        </div>
                    </div>
                `;
                // Call the functions to render the content
                renderComparisonTable(player1, player2);
                renderCompositionChart(player1, player2);
                renderRawStatsChart(player1, player2);
            }
        }
        player1Search.addEventListener('input', updateComparison);
        player2Search.addEventListener('input', updateComparison);
    }
    
    // --- Rendering Functions ---
    function renderComparisonTable(p1, p2) {
        const table = document.getElementById('comparison-table');
        const statsToCompare = [
            { label: 'Position', key: 'position' },
            { label: 'Fantasy PPG', key: 'ppg' }, { label: 'VORP', key: 'vorp' },
            { label: 'Pass Yds/Game', key: 'passing_yards_pg' }, { label: 'Rush Yds/Game', key: 'rushing_yards_pg' },
            { label: 'Rec Yds/Game', key: 'receiving_yards_pg' }
        ];
        let tableHTML = `<thead><tr><th>Stat</th><th>${p1.player_display_name}</th><th>${p2.player_display_name}</th></tr></thead><tbody>`;
        statsToCompare.forEach(stat => {
            const val1 = p1[stat.key] !== undefined ? p1[stat.key].toFixed(2) : 'N/A';
            const val2 = p2[stat.key] !== undefined ? p2[stat.key].toFixed(2) : 'N/A';
            if ((!isNaN(parseFloat(val1)) && parseFloat(val1) !== 0) || (!isNaN(parseFloat(val2)) && parseFloat(val2) !== 0) || stat.key === 'position') {
                tableHTML += `<tr><td>${stat.label}</td><td class="${parseFloat(val1) > parseFloat(val2) ? 'winner' : ''}">${val1}</td><td class="${parseFloat(val2) > parseFloat(val1) ? 'winner' : ''}">${val2}</td></tr>`;
            }
        });
        tableHTML += `</tbody>`;
        table.innerHTML = tableHTML;
    }

    function renderCompositionChart(p1, p2) {
        if (chartInstances.composition) chartInstances.composition.destroy();
        const ctx = document.getElementById('composition-chart').getContext('2d');
        const getComposition = (player) => [
            (player.passing_yards_pg || 0) * 0.05, (player.rushing_yards_pg || 0) * 0.1,
            (player.receiving_yards_pg || 0) * 0.1,
            ((player.passing_tds_pg || 0) * 4) + ((player.rushing_tds_pg || 0) * 6) + ((player.receiving_tds_pg || 0) * 6),
            (player.receptions_pg || 0) * 1
        ];
        chartInstances.composition = new Chart(ctx, { type: 'doughnut', data: { labels: ['from Pass Yds', 'from Rush Yds', 'from Rec Yds', 'from TDs', 'from Receptions'], datasets: [{ label: p1.player_display_name, data: getComposition(p1) }, { label: p2.player_display_name, data: getComposition(p2) }] }, options: { plugins: { legend: { position: 'top', labels: { color: '#e0e0e0' } } } } });
    }

    function renderRawStatsChart(p1, p2) {
        if (chartInstances.rawStats) chartInstances.rawStats.destroy();
        const ctx = document.getElementById('raw-stats-chart').getContext('2d');
        chartInstances.rawStats = new Chart(ctx, { type: 'bar', data: { labels: ['Pass Yds', 'Rush Yds', 'Rec Yds'], datasets: [{ label: p1.player_display_name, data: [p1.passing_yards_pg || 0, p1.rushing_yards_pg || 0, p1.receiving_yards_pg || 0], backgroundColor: 'rgba(3, 218, 198, 0.6)' }, { label: p2.player_display_name, data: [p2.passing_yards_pg || 0, p2.rushing_yards_pg || 0, p2.receiving_yards_pg || 0], backgroundColor: 'rgba(255, 99, 132, 0.6)' }] }, options: { scales: { x: { ticks: { color: '#e0e0e0' } }, y: { ticks: { color: '#e0e0e0' } } }, plugins: { legend: { labels: { color: '#e0e0e0' } } } } });
    }

    function renderTopMatchups(matchups) {
        const container = document.getElementById('top-matchups');
        if (!container) return;
        const sorted = matchups.sort((a,b) => b.projection - a.projection).slice(0, 10);
        let listHTML = '<ul>';
        sorted.forEach(m => { listHTML += `<li><strong>${m.player} (${m.position}, ${m.opponent})</strong> - ${m.rating} Matchup</li>`; });
        listHTML += '</ul>';
        container.innerHTML = listHTML;
    }

    function renderDefensiveChart(fpaData) {
        const ctx = document.getElementById('defensive-chart')?.getContext('2d');
        if (!ctx) return;
        const teams = Object.keys(fpaData);
        const totalPointsAllowed = teams.map(team => (fpaData[team]?.RB || 0) + (fpaData[team]?.WR || 0) + (fpaData[team]?.TE || 0));
        const sortedData = teams.map((team, i) => ({team, points: totalPointsAllowed[i]})).sort((a,b) => b.points - a.points).slice(0, 5);
        new Chart(ctx, { type: 'bar', data: { labels: sortedData.map(d => d.team), datasets: [{ label: 'Avg Pts Allowed', data: sortedData.map(d => d.points), backgroundColor: 'rgba(255, 99, 132, 0.6)' }] }, options: { scales: { x: { ticks: { color: '#e0e0e0' } }, y: { ticks: { color: '#e0e0e0' } } }, plugins: { legend: { display: false } } } });
    }
});
