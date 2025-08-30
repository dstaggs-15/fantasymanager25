document.addEventListener('DOMContentLoaded', () => {
    const tableBody = document.getElementById('player-table-body');

    function getRecommendation(score) {
        if (score >= 8.0) return { text: 'Must Start', className: 'rec-must-start' };
        if (score >= 6.5) return { text: 'Strong Start', className: 'rec-strong-start' };
        if (score >= 5.0) return { text: 'Good Flex', className: 'rec-good-flex' };
        if (score >= 4.0) return { text: 'Risky Flex', className: 'rec-risky-flex' };
        return { text: 'Risky Sit', className: 'rec-sit' };
    }

    async function fetchData() {
        try {
            // --- FIX: Removed '/docs' from the file path ---
            const response = await fetch('./data/reports/start_score_report.json');
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

    function renderTable(players) {
        tableBody.innerHTML = '';
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
    
    fetchData();
});
