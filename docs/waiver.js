document.addEventListener('DOMContentLoaded', async () => {
    const reportTitle = document.getElementById('report-title');
    const reportContainer = document.getElementById('waiver-report');

    try {
        // THE FIX: Corrected path to the data file
        const response = await fetch('data/analysis/waiver_wire_report.json');
        if (!response.ok) throw new Error(`File not found (status: ${response.status})`);
        const data = await response.json();

        reportTitle.textContent = `Top Performers for Season: ${data.season}, Week: ${data.week}`;

        for (const [pos, players] of Object.entries(data.positions)) {
            const section = document.createElement('div');
            section.className = 'report-card';
            const title = document.createElement('h3');
            title.textContent = `Top ${pos}s`;
            section.appendChild(title);

            const table = document.createElement('table');
            table.innerHTML = `<thead><tr><th>Player</th><th>Team</th><th>Points</th></tr></thead>`;
            const tbody = document.createElement('tbody');
            
            for (const player of players) {
                const tr = document.createElement('tr');
                tr.innerHTML = `<td>${player.player_display_name}</td><td>${player.recent_team}</td><td>${player.fantasy_points_custom}</td>`;
                tbody.appendChild(tr);
            }
            
            table.appendChild(tbody);
            section.appendChild(table);
            reportContainer.appendChild(section);
        }

    } catch (error) {
        reportTitle.textContent = 'Failed to load waiver wire report.';
        console.error('Error fetching or parsing data:', error);
    }
});
