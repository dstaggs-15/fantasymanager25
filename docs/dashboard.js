document.addEventListener('DOMContentLoaded', async () => {
    // --- Data Loading ---
    let allPlayers = [];
    // Other variables from your original dashboard.js can remain if needed

    try {
        const [vorpRes] = await Promise.all([
            fetch('data/analysis/vorp_analysis.json'),
            // Add other fetch calls here if the dashboard needs more data
        ]);
        if (!vorpRes.ok) throw new Error('Failed to load VORP analysis file.');

        const vorpData = await vorpRes.json();
        allPlayers = vorpData.players;

        // --- Initial Page Renders ---
        populateDatalist(allPlayers);
        // Call other chart rendering functions here

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
            const statsToCompare = [
                { label: 'Position', key: 'position' },
                { label: 'Fantasy PPG', key: 'ppg', bold: true },
                { label: 'VORP', key: 'vorp', bold: true },
                { label: 'Pass Yds/Game', key: 'passing_yards_pg' },
                { label: 'Pass TDs/Game', key: 'passing_tds_pg' },
                { label: 'Rush Yds/Game', key: 'rushing_yards_pg' },
                { label: 'Rush TDs/Game', key: 'rushing_tds_pg' },
                { label: 'Receptions/Game', key: 'receptions_pg' },
                { label: 'Rec Yds/Game', key: 'receiving_yards_pg' },
                { label: 'Rec TDs/Game', key: 'receiving_tds_pg' },
            ];

            let comparisonHTML = `
            <div class="table-container">
                <table>
                    <thead><tr>
                        <th>Stat</th>
                        <th>${player1.player_display_name}</th>
                        <th>${player2.player_display_name}</th>
                    </tr></thead>
                    <tbody>`;

            statsToCompare.forEach(stat => {
                const val1 = player1[stat.key] !== undefined ? player1[stat.key] : 'N/A';
                const val2 = player2[stat.key] !== undefined ? player2[stat.key] : 'N/A';
                
                // Only show rows if at least one player has a non-zero value for that stat
                if (val1 !== 'N/A' && val1 !== 0 || val2 !== 'N/A' && val2 !== 0) {
                     comparisonHTML += `
                        <tr>
                            <td>${stat.label}</td>
                            <td class="${val1 > val2 ? 'winner' : ''}">${val1}</td>
                            <td class="${val2 > val1 ? 'winner' : ''}">${val2}</td>
                        </tr>
                    `;
                }
            });
            
            comparisonHTML += '</tbody></table></div>';
            comparisonResults.innerHTML = comparisonHTML;
        }
    }
    // Use the 'input' event for a more responsive feel
    player1Search.addEventListener('input', updateComparison);
    player2Search.addEventListener('input', updateComparison);
    
    function populateDatalist(players) {
        const playerDatalist = document.getElementById('player-list');
        // Sort players alphabetically for the dropdown
        players.sort((a, b) => a.player_display_name.localeCompare(b.player_display_name));
        players.forEach(p => {
            const option = document.createElement('option');
            option.value = p.player_display_name;
            playerDatalist.appendChild(option);
        });
    }
});
