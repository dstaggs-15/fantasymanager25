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
        initializeComparisonTool(allPlayers);
        renderTopMatchups(matchupData.matchups);
        renderDefensiveChart(teamData.fantasy_points_allowed);

    } catch (error) {
        console.error("Dashboard failed to load:", error);
    }

    // --- Player Comparison Logic ---
    function initializeComparisonTool(players) {
        const player1Search = document.getElementById('player1-search');
        const player2Search = document.getElementById('player2-search');
        const comparisonResults = document.getElementById('comparison-results');
        const playerDatalist = document.getElementById('player-list');

        // Populate datalist for autocomplete
        players.sort((a, b) => a.player_display_name.localeCompare(b.player_display_name));
        players.forEach(p => {
            const option = document.createElement('option');
            option.value = p.player_display_name;
            playerDatalist.appendChild(option);
        });

        function updateComparison() {
            const name1 = player1Search.value;
            const name2 = player2Search.value;
            const player1 = players.find(p => p.player_display_name === name1);
            const player2 = players.find(p => p.player_display_name === name2);
            
            comparisonResults.innerHTML = ''; // Clear previous results
            if (player1 && player2) {
                // THE FIX: Add the full HTML structure for the table and chart canvases
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
