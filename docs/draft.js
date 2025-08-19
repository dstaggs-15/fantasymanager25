document.addEventListener('DOMContentLoaded', async () => {
    const reportTitle = document.getElementById('report-title');
    const reportContainer = document.getElementById('draft-report');

    try {
        // THE FIX: Corrected path to the data file
        const response = await fetch('data/analysis/draft_tiers_report.json');
        if (!response.ok) throw new Error(`File not found (status: ${response.status})`);
        const data = await response.json();

        reportTitle.textContent = `Draft Tiers Based on ${data.season} PPG`;

        for (const [pos, tiers] of Object.entries(data.positions)) {
            const posSection = document.createElement('div');
            posSection.className = 'report-card';
            const posTitle = document.createElement('h3');
            posTitle.textContent = `${pos} Tiers`;
            posSection.appendChild(posTitle);

            for (const [tierName, players] of Object.entries(tiers)) {
                if (players.length === 0) continue;
                const p = document.createElement('p');
                const playerNames = players.map(p => `${p.player_display_name} (${p.ppg})`).join(', ');
                p.innerHTML = `<strong>${tierName}:</strong> ${playerNames}`;
                posSection.appendChild(p);
            }
            reportContainer.appendChild(posSection);
        }
    } catch (error) {
        reportTitle.textContent = 'Failed to load draft tiers report.';
        console.error('Error fetching or parsing data:', error);
    }
});
