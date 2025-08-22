document.addEventListener('DOMContentLoaded', async () => {
    // --- Data Loading ---
    let allPlayers = [];
    let matchupData = {};
    let teamData = {};

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
            let comparisonHTML = `
            <div class="table-container">
                <table>
                    <thead><tr><th>Stat</th><th>${player1.player_display_name}</th><th>${player2.player_display_name}</th></tr></thead>
                    <tbody>
                        <tr><td>Position</td><td>${player1.position}</td><td>${player2.position}</td></tr>
                        <tr><td>PPG</td><td>${player1.ppg.toFixed(2)}</td><td>${player2.ppg.toFixed(2)}</td></tr>
                        <tr><td>VORP</td><td>${player1.vorp.toFixed(2)}</td><td>${player2.vorp.toFixed(2)}</td></tr>
                    </tbody>
                </table>
            </div>`;
            comparisonResults.innerHTML = comparisonHTML;
        }
    }
    player1Search.addEventListener('change', updateComparison);
    player2Search.addEventListener('change', updateComparison);
    
    function populateDatalist(players) {
        const playerDatalist = document.getElementById('player-list');
        players.forEach(p => {
            const option = document.createElement('option');
            option.value = p.player_display_name;
            playerDatalist.appendChild(option);
        });
    }

    // --- Chart and List Rendering Functions ---
    function renderTopMatchups(matchups) {
        const container = document.getElementById('top-matchups');
        // Sort by projection difference from baseline PPG
        const sorted = matchups.sort((a,b) => (b.projection - b.player_ppg) - (a.projection - a.player_ppg));
        let listHTML = '<ul>';
        sorted.slice(0, 10).forEach(m => {
            const boost = m.projection - m.player_ppg;
            listHTML += `<li><strong>${m.player}</strong> vs ${m.opponent} <span style="color:${boost > 0 ? '#4CAF50' : '#F44336'};">(${boost.toFixed(2)} pt boost)</span></li>`;
        });
        listHTML += '</ul>';
        container.innerHTML = listHTML;
    }

    function renderDefensiveChart(fpaData) {
        const teams = Object.keys(fpaData);
        const totalPointsAllowed = teams.map(team => {
            return (fpaData[team].RB || 0) + (fpaData[team].WR || 0) + (fpaData[team].TE || 0);
        });
        
        const sortedData = teams.map((team, i) => ({team, points: totalPointsAllowed[i]}))
            .sort((a,b) => b.points - a.points).slice(0, 5); // Top 5 worst defenses

        const ctx = document.getElementById('defensive-chart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: sortedData.map(d => d.team),
                datasets: [{
                    label: 'Avg Fantasy Pts Allowed to RB/WR/TE',
                    data: sortedData.map(d => d.points),
                    backgroundColor: 'rgba(255, 99, 132, 0.6)'
                }]
            },
            options: {
                scales: { x: { ticks: { color: '#e0e0e0' } }, y: { ticks: { color: '#e0e0e0' } } },
                plugins: { legend: { display: false } }
            }
        });
    }
});
