document.addEventListener('DOMContentLoaded', async () => {
    const reportTitle = document.getElementById('report-title');
    const tableContainer = document.getElementById('matchup-table');
    const searchInput = document.getElementById('player-search');
    let allMatchups = []; // Store all matchups for filtering

    try {
        const response = await fetch('data/analysis/matchup_report.json');
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();

        reportTitle.textContent = `Matchup Report for Week ${data.week}`;
        allMatchups = data.matchups;
        renderTable(allMatchups);

    } catch (error) {
        reportTitle.textContent = 'Failed to load matchup report.';
        console.error('Error fetching data:', error);
    }
    
    // Event listener for the search bar
    searchInput.addEventListener('keyup', () => {
        const searchTerm = searchInput.value.toLowerCase();
        if (searchTerm) {
            const filteredMatchups = allMatchups.filter(m => 
                m.player.toLowerCase().includes(searchTerm)
            );
            renderTable(filteredMatchups);
        } else {
            renderTable(allMatchups); // Show all if search is empty
        }
    });

    function renderTable(matchups) {
        // THE FIX: Added new columns for more in-depth data
        const headers = ['Player', 'Pos', 'Opp', 'Player PPG', 'Opp PPG Allowed', 'Projection', 'Rating'];
        let tableHTML = '<thead><tr>';
        headers.forEach(h => tableHTML += `<th>${h}</th>`);
        tableHTML += '</tr></thead>';

        tableHTML += '<tbody>';
        matchups.forEach(matchup => {
            const ratingClass = `rating-${matchup.rating.toLowerCase().replace(' ', '')}`;
            tableHTML += `
                <tr class="${ratingClass}">
                    <td>${matchup.player}</td>
                    <td>${matchup.position}</td>
                    <td>${matchup.opponent}</td>
                    <td>${matchup.player_ppg.toFixed(2)}</td>
                    <td>${matchup.ppg_allowed.toFixed(2)}</td>
                    <td><strong>${matchup.projection.toFixed(2)}</strong></td>
                    <td>${matchup.rating}</td>
                </tr>
            `;
        });
        tableHTML += '</tbody>';
        tableContainer.innerHTML = tableHTML;
    }
});
