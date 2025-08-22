document.addEventListener('DOMContentLoaded', async () => {
    const tableContainer = document.getElementById('consistency-table');
    const searchInput = document.getElementById('player-search');
    let allPlayers = [];

    try {
        const response = await fetch('data/analysis/consistency_report.json');
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();
        
        allPlayers = data.players;
        renderTable(allPlayers);

    } catch (error) {
        tableContainer.innerHTML = '<tr><td>Failed to load consistency report.</td></tr>';
        console.error('Error fetching data:', error);
    }
    
    searchInput.addEventListener('keyup', () => {
        const searchTerm = searchInput.value.toLowerCase();
        const filteredPlayers = allPlayers.filter(p => 
            p.player_display_name.toLowerCase().includes(searchTerm)
        );
        renderTable(filteredPlayers);
    });

    function renderTable(players) {
        const headers = ['Player', 'Pos', 'Games', 'Mean PPG', 'Std Dev', 'Ceiling PPG', 'Floor PPG', 'Consistency %'];
        let tableHTML = '<thead><tr>';
        headers.forEach(h => tableHTML += `<th>${h}</th>`);
        tableHTML += '</tr></thead>';

        tableHTML += '<tbody>';
        players.forEach(player => {
            tableHTML += `
                <tr>
                    <td>${player.player_display_name}</td>
                    <td>${player.position}</td>
                    <td>${player.games_played}</td>
                    <td>${player.mean_ppg}</td>
                    <td>${player.std_dev_ppg}</td>
                    <td>${player.ceiling_ppg}</td>
                    <td>${player.floor_ppg}</td>
                    <td>${player.consistency_pct}%</td>
                </tr>
            `;
        });
        tableHTML += '</tbody>';
        tableContainer.innerHTML = tableHTML;
    }
});
