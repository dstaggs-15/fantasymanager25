document.addEventListener('DOMContentLoaded', async () => {
    const reportTitle = document.getElementById('report-title');
    const tableContainer = document.getElementById('matchup-table');

    try {
        const response = await fetch('data/analysis/matchup_report.json');
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();

        reportTitle.textContent = `Matchup Report for Week ${data.week}`;

        const headers = ['Player', 'Position', 'Opponent', 'Rating', 'Details'];
        let tableHTML = '<thead><tr>';
        headers.forEach(h => tableHTML += `<th>${h}</th>`);
        tableHTML += '</tr></thead>';

        tableHTML += '<tbody>';
        data.matchups.forEach(matchup => {
            tableHTML += `
                <tr class="rating-${matchup.rating.toLowerCase()}">
                    <td>${matchup.player}</td>
                    <td>${matchup.position}</td>
                    <td>${matchup.opponent}</td>
                    <td>${matchup.rating}</td>
                    <td>${matchup.details}</td>
                </tr>
            `;
        });
        tableHTML += '</tbody>';
        tableContainer.innerHTML = tableHTML;

    } catch (error) {
        reportTitle.textContent = 'Failed to load matchup report.';
        console.error('Error fetching data:', error);
    }
});
