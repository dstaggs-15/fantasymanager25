document.addEventListener('DOMContentLoaded', async () => {
    const reportTitle = document.getElementById('report-title');
    const tableContainer = document.getElementById('vorp-table');

    try {
        const response = await fetch('data/analysis/vorp_analysis.json');
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();

        reportTitle.textContent = `VORP Rankings Based on ${data.season} PPG`;

        const headers = ['Rank', 'Player', 'Position', 'PPG', 'VORP'];
        let tableHTML = '<thead><tr>';
        headers.forEach(h => tableHTML += `<th>${h}</th>`);
        tableHTML += '</tr></thead>';

        tableHTML += '<tbody>';
        data.players.forEach((player, index) => {
            tableHTML += `<tr><td>${index + 1}</td><td>${player.player_display_name}</td><td>${player.position}</td><td>${player.ppg}</td><td>${player.vorp}</td></tr>`;
        });
        tableHTML += '</tbody>';
        tableContainer.innerHTML = tableHTML;

    } catch (error) {
        reportTitle.textContent = 'Failed to load VORP report.';
        console.error('Error fetching data:', error);
    }
});
