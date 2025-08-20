document.addEventListener('DOMContentLoaded', async () => {
    const reportTitle = document.getElementById('report-title');
    const tableContainer = document.getElementById('vorp-table');

    try {
        const response = await fetch('data/analysis/vorp_analysis.json');
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();

        reportTitle.textContent = `VORP Rankings Based on ${data.season} PPG`;
        renderMainTable(data.players);
        
        // --- NEW: Render the Chart ---
        renderVorpChart(data.players.slice(0, 20)); // Chart the top 20 players

    } catch (error) {
        reportTitle.textContent = 'Failed to load VORP report.';
        console.error('Error fetching data:', error);
    }

    function renderMainTable(players) {
        // ... (table rendering logic is unchanged)
        const headers = ['Rank', 'Player', 'Position', 'PPG', 'VORP'];
        let tableHTML = '<thead><tr>';
        headers.forEach(h => tableHTML += `<th>${h}</th>`);
        tableHTML += '</tr></thead>';
        tableHTML += '<tbody>';
        players.forEach((player, index) => {
            tableHTML += `<tr><td>${index + 1}</td><td>${player.player_display_name}</td><td>${player.position}</td><td>${player.ppg}</td><td>${player.vorp}</td></tr>`;
        });
        tableHTML += '</tbody>';
        tableContainer.innerHTML = tableHTML;
    }

    function renderVorpChart(players) {
        const ctx = document.getElementById('vorpChart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: players.map(p => p.player_display_name),
                datasets: [{
                    label: 'VORP Score',
                    data: players.map(p => p.vorp),
                    backgroundColor: 'rgba(97, 218, 251, 0.6)',
                    borderColor: 'rgba(97, 218, 251, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                indexAxis: 'y', // Horizontal bar chart
                scales: {
                    x: { ticks: { color: '#e0e0e0' } },
                    y: { ticks: { color: '#e0e0e0' } }
                },
                plugins: {
                    legend: { labels: { color: '#e0e0e0' } }
                }
            }
        });
    }
});
