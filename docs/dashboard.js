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
