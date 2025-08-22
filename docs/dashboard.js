document.addEventListener('DOMContentLoaded', async () => {
    // --- Global variables to hold our data ---
    let allPlayersData = [];
    let matchupData = {};
    let teamData = {};
    let chartInstances = {}; // To manage and destroy old charts

    // --- Main Data Loading Function ---
    async function loadData() {
        try {
            console.log("Starting to fetch all data...");
            const [vorpRes, matchupRes, teamRes] = await Promise.all([
                fetch('data/analysis/vorp_analysis.json'),
                fetch('data/analysis/matchup_report.json'),
                fetch('data/analysis/team_rankings.json')
            ]);

            if (!vorpRes.ok) throw new Error(`Failed to load VORP data (status: ${vorpRes.status})`);
            if (!matchupRes.ok) throw new Error(`Failed to load Matchup data (status: ${matchupRes.status})`);
            if (!teamRes.ok) throw new Error(`Failed to load Team data (status: ${teamRes.status})`);

            const vorpData = await vorpRes.json();
            matchupData = await matchupRes.json();
            teamData = await teamRes.json();
            allPlayersData = vorpData.players;

            console.log("All data fetched successfully.");
            return true; // Indicate success

        } catch (error) {
            console.error("Dashboard failed to load:", error);
            const comparisonResults = document.getElementById('comparison-results');
            if (comparisonResults) comparisonResults.innerHTML = `<div class="report-card"><p style="color: #F44336;">Error: Could not load necessary data files. Please ensure all analysis workflows have run successfully.</p></div>`;
            return false; // Indicate failure
        }
    }

    // --- Player Comparison Tool ---
    function initializeComparisonTool(players) {
        const player1Search = document.getElementById('player1-search');
        const player2Search = document.getElementById('player2-search');
        const comparisonResults = document.getElementById('comparison-results');
        const playerDatalist = document.getElementById('player-list');

        if (!player1Search || !playerDatalist) {
            console.error("Comparison tool HTML elements not found!");
            return;
        }

        // Populate the search box dropdown with player names
        players.sort((a, b) => a.player_display_name.localeCompare(b.player_display_name));
        let datalistHTML = '';
        players.forEach(p => {
            datalistHTML += `<option value="${p.player_display_name}"></option>`;
        });
        playerDatalist.innerHTML = datalistHTML;

        // This function runs whenever you select a player
        function updateComparison() {
            const name1 = player1Search.value;
            const name2 = player2Search.value;
            const player1 = players.find(p => p.player_display_name === name1);
            const player2 = players.find(p => p.player_display_name === name2);
            
            comparisonResults.innerHTML = ''; // Clear previous results
            if (player1 && player2) {
                // Create the containers for the table and charts
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
            { label: 'Fantasy PPG', key: 'pp
