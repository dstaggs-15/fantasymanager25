document.addEventListener('DOMContentLoaded', async () => {
    const reportTitle = document.getElementById('report-title');
    const tableContainer = document.getElementById('vorp-table');
    const player1Search = document.getElementById('player1-search');
    const player2Search = document.getElementById('player2-search');
    const playerDatalist = document.getElementById('player-list');
    const comparisonResults = document.getElementById('comparison-results');

    let allPlayers = []; // Store all player data for comparisons

    try {
        const response = await fetch('data/analysis/vorp_analysis.json');
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();

        allPlayers = data.players; // Save player data
        reportTitle.textContent = `VORP Rankings Based on ${data.season} PPG`;

        renderMainTable(allPlayers);
        populateDatalist(allPlayers);

    } catch (error) {
        reportTitle.textContent = 'Failed to load VORP report.';
        console.error('Error fetching data:', error);
    }

    // Add event listeners to the search boxes
    player1Search.addEventListener('change', updateComparison);
    player2Search.addEventListener('change', updateComparison);

    function renderMainTable(players) {
        const headers = ['Rank', 'Player', 'Position', 'PPG', 'VORP'];
        let tableHTML = '<thead><tr>';
        headers.forEach(h => tableHTML += `<th>${h}</th>`);
        tableHTML += '</tr></thead>';

        tableHTML += '<tbody>';
        players.forEach((player, index) => {
            tableHTML += `
                <tr>
                    <td>${index + 1}</td>
                    <td>${player.player_display_name}</td>
                    <td>${player.position}</td>
                    <td>${player.ppg}</td>
                    <td>${player.vorp}</td>
                </tr>
            `;
        });
        tableHTML += '</tbody>';
        tableContainer.innerHTML = tableHTML;
    }

    function populateDatalist(players) {
        players.forEach(player => {
            const option = document.createElement('option');
            option.value = player.player_display_name;
            playerDatalist.appendChild(option);
        });
    }

    function updateComparison() {
        const name1 = player1Search.value;
        const name2 = player2Search.value;

        const player1 = allPlayers.find(p => p.player_display_name === name1);
        const player2 = allPlayers.find(p => p.player_display_name === name2);
        
        // Clear previous results
        comparisonResults.innerHTML = '';
        
        if (player1 && player2) {
            let comparisonHTML = `
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Stat</th>
                            <th>${player1.player_display_name}</th>
                            <th>${player2.player_display_name}</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td>Position</td><td>${player1.position}</td><td>${player2.position}</td></tr>
                        <tr><td>PPG</td><td>${player1.ppg}</td><td>${player2.ppg}</td></tr>
                        <tr><td>VORP</td><td>${player1.vorp}</td><td>${player2.vorp}</td></tr>
                    </tbody>
                </table>
            </div>
            `;
            comparisonResults.innerHTML = comparisonHTML;
        }
    }
});
