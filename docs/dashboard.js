document.addEventListener('DOMContentLoaded', () => {
    let allPlayers = []; // This will be populated by the VORP data

    // --- Load VORP Data for Player Comparison ---
    fetch('data/analysis/vorp_analysis.json')
        .then(res => {
            if (!res.ok) throw new Error('VORP data file not found.');
            return res.json();
        })
        .then(data => {
            allPlayers = data.players;
            initializeComparisonTool(allPlayers);
        })
        .catch(error => {
            console.error('Failed to load VORP data for comparison tool:', error);
            const comparisonCard = document.querySelector('#comparison-card p');
            if(comparisonCard) comparisonCard.textContent = 'Error: Could not load player data for comparison.';
        });

    // --- Load Matchup Data ---
    fetch('data/analysis/matchup_report.json')
        .then(res => {
            if (!res.ok) throw new Error('Matchup data file not found.');
            return res.json();
        })
        .then(data => renderTopMatchups(data.matchups))
        .catch(error => console.error('Failed to load matchup data:', error));

    // --- Load Team Rankings Data ---
    fetch('data/analysis/team_rankings.json')
        .then(res => {
            if (!res.ok) throw new Error('Team ranking data file not found.');
            return res.json();
        })
        .then(data => renderDefensiveChart(data.fantasy_points_allowed))
        .catch(error => console.error('Failed to load team ranking data:', error));


    // --- All Functions ---
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
            
            comparisonResults.innerHTML = '';
            if (player1 && player2) {
                // ... (Rendering logic from previous version)
                let comparisonHTML = `<div class="table-container" style="margin-top: 2rem;"><table>...</table></div>`; // Your table rendering here
                comparisonResults.innerHTML = comparisonHTML;
            }
        }
        player1Search.addEventListener('input', updateComparison);
        player2Search.addEventListener('input', updateComparison);
    }
    
    function renderTopMatchups(matchups) {
        // ... (function is unchanged)
    }

    function renderDefensiveChart(fpaData) {
        // ... (function is unchanged)
    }
});
