document.addEventListener('DOMContentLoaded', () => {
    const tableBody = document.getElementById('player-table-body');

    /**
     * Takes a start score and returns a recommendation object with text and a CSS class.
     * @param {number} score - The player's start score (0-10).
     * @returns {{text: string, className: string}}
     */
    function getRecommendation(score) {
        if (score >= 8.0) return { text: 'Must Start', className: 'rec-must-start' };
        if (score >= 6.5) return { text: 'Strong Start', className: 'rec-strong-start' };
        if (score >= 5.0) return { text: 'Good Flex', className: 'rec-good-flex' };
        if (score >= 4.0) return { text: 'Risky Flex', className: 'rec-risky-flex' };
        return { text: 'Risky Sit', className: 'rec-sit' };
    }

    async function fetchData() {
        try {
            const response = await fetch('./docs/data/reports/start_score_report.json');
            if (!response.ok) {
                throw new Error(`Network response was not ok: ${response.statusText}`);
            }
            const players = await response.json();
            renderTable(players);
        } catch (error) {
            console.error('Error fetching or parsing data:', error);
            tableBody.innerHTML = `<tr><td colspan="5">Error loading player data.</td></tr>`;
        }
    }

    /**
     * Renders the player data table.
     * @param {Array<Object>} players - The array of player data.
     */
    function renderTable(players) {
        tableBody.innerHTML = ''; // Clear existing table rows
        
        // Sort players by start_score descending before rendering
        players.sort((a, b) => b.start_score - a.start_score);

        players.forEach(player => {
            const recommendation = getRecommendation(player.start_score);
            const row = document.createElement('tr');

            row.innerHTML = `
                <td>${player.player_name}</td>
                <td>${player.position}</td>
                <td>${player.team}</td>
                <td>${(player.start_score || 0).toFixed(2)}</td>
                <td>
                    <span class="recommendation-pill ${recommendation.className}">
                        ${recommendation.text}
                    </span>
                </td>
            `;
            tableBody.appendChild(row);
        });
    }

    // Don't forget to update your start-sit.html to have a 5th column header for "Recommendation"
    // <thead>
    //     <tr>
    //         <th>Player</th>
    //         <th>Position</th>
    //         <th>Team</th>
    //         <th>Start Score</th>
    //         <th>Recommendation</th>  <-- ADD THIS HEADER
    //     </tr>
    // </thead>
    
    fetchData();
});
