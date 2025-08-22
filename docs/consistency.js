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
        tableContainer.innerHTML = '<thead></thead><tbody><tr><td>Failed to load consistency report.</td></tr></tbody>';
        console.error('Error fetching data:', error);
    }
    
    searchInput.addEventListener('keyup', () => {
        const searchTerm = searchInput.value.toLowerCase();
        const filteredPlayers = allPlayers.filter(p => 
            p.player_display_name.toLowerCase().includes(searchTerm)
        );
        renderTable(filteredPlayers);
    });

    // --- NEW: Heat Map Functions ---
    function getMinMax(players, column) {
        const values = players.map(p => p[column]).filter(v => v !== null && !isNaN(v));
        if (values.length === 0) return { min: 0, max: 1 };
        return { min: Math.min(...values), max: Math.max(...values) };
    }

    function getColorForValue(value, min, max, lowerIsBetter = false) {
        if (value === null || isNaN(value)) return '#1E1E1E'; // Default card color
        if (max === min) return '#1E1E1E';

        let percent = (value - min) / (max - min);
        if (lowerIsBetter) {
            percent = 1 - percent; // Invert the scale for things like Std Dev
        }

        // Interpolate from red (0) to yellow (0.5) to green (1.0)
        const hue = (percent * 120).toString(10);
        return `hsl(${hue}, 90%, 30%)`;
    }

    function renderTable(players) {
        // Calculate min/max for each column for the heat map
        const stats = {
            mean_ppg: getMinMax(players, 'mean_ppg'),
            std_dev_ppg: getMinMax(players, 'std_dev_ppg'),
            ceiling_ppg: getMinMax(players, 'ceiling_ppg'),
            floor_ppg: getMinMax(players, 'floor_ppg'),
            consistency_pct: getMinMax(players, 'consistency_pct'),
        };

        const headers = ['Player', 'Pos', 'Games', 'Mean PPG', 'Std Dev', 'Ceiling PPG', 'Floor PPG', 'Consistency %'];
        let tableHTML = '<thead><tr>';
        headers.forEach(h => tableHTML += `<th>${h}</th>`);
        tableHTML += '</tr></thead>';

        tableHTML += '<tbody>';
        players.forEach(player => {
            // Get colors for each cell
            const meanColor = getColorForValue(player.mean_ppg, stats.mean_ppg.min, stats.mean_ppg.max);
            const stdDevColor = getColorForValue(player.std_dev_ppg, stats.std_dev_ppg.min, stats.std_dev_ppg.max, true); // Lower is better
            const ceilingColor = getColorForValue(player.ceiling_ppg, stats.ceiling_ppg.min, stats.ceiling_ppg.max);
            const floorColor = getColorForValue(player.floor_ppg, stats.floor_ppg.min, stats.floor_ppg.max);
            const consistencyColor = getColorForValue(player.consistency_pct, stats.consistency_pct.min, stats.consistency_pct.max);

            tableHTML += `
                <tr>
                    <td>${player.player_display_name}</td>
                    <td>${player.position}</td>
                    <td>${player.games_played}</td>
                    <td class="heat-cell" style="background-color: ${meanColor}">${player.mean_ppg}</td>
                    <td class="heat-cell" style="background-color: ${stdDevColor}">${player.std_dev_ppg}</td>
                    <td class="heat-cell" style="background-color: ${ceilingColor}">${player.ceiling_ppg}</td>
                    <td class="heat-cell" style="background-color: ${floorColor}">${player.floor_ppg}</td>
                    <td class="heat-cell" style="background-color: ${consistencyColor}">${player.consistency_pct}%</td>
                </tr>
            `;
        });
        tableHTML += '</tbody>';
        tableContainer.innerHTML = tableHTML;
    }
});
