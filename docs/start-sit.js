document.addEventListener('DOMContentLoaded', async () => {
    const playerInputs = [
        document.getElementById('player1'),
        document.getElementById('player2'),
        document.getElementById('player3'),
    ];
    const compareBtn = document.getElementById('compare-btn');
    const resultsContainer = document.getElementById('results-container');
    const playerDatalist = document.getElementById('player-list');
    let START_SCORE_DATA = [];

    async function initialize() {
        try {
            const response = await fetch('./data/reports/start_scores.json');
            if (!response.ok) throw new Error('Failed to fetch Start Score data');
            START_SCORE_DATA = await response.json();
            
            START_SCORE_DATA.sort((a, b) => a.player_display_name.localeCompare(b.player_display_name));
            const fragment = document.createDocumentFragment();
            START_SCORE_DATA.forEach(player => {
                const option = document.createElement('option');
                option.value = player.player_display_name;
                fragment.appendChild(option);
            });
            playerDatalist.appendChild(fragment);
            console.log("Start Score data loaded and ready.");
        } catch (error) {
            console.error("Initialization failed:", error);
            resultsContainer.innerHTML = `<div class="card"><h3 style="color: #dc3545;">Error Loading Data</h3><p>Could not load the 'start_scores.json' report. Please go to the 'Actions' tab on GitHub and run the workflow to generate the latest analysis data.</p></div>`;
        }
    }

    function analyzePlayers() {
        resultsContainer.innerHTML = '';
        const selectedPlayerNames = playerInputs.map(input => input.value).filter(name => name.trim() !== '');
        if (selectedPlayerNames.length === 0) return;
        selectedPlayerNames.forEach(playerName => {
            const playerData = START_SCORE_DATA.find(p => p.player_display_name === playerName);
            renderCard(playerData, playerName);
        });
    }

    function renderCard(playerData, playerName) {
        const card = document.createElement('div');
        card.className = 'player-card';
        if (!playerData) {
            card.innerHTML = `<h3>${playerName}</h3><p style="color: #ffc107;">Player not found in analysis report.</p>`;
            resultsContainer.appendChild(card);
            return;
        }

        // --- NEW: Dynamically build the stats breakdown ---
        let statsHTML = '<ul class="breakdown-list">';
        if (playerData.stats && typeof playerData.stats === 'object') {
            for (const [key, value] of Object.entries(playerData.stats)) {
                statsHTML += `<li><span>${key}</span><strong>${value}</strong></li>`;
            }
        }
        statsHTML += '</ul>';

        let breakdownHTML = '<ul class="breakdown-list">';
        if (typeof playerData.breakdown === 'object') {
            for (const [key, value] of Object.entries(playerData.breakdown)) {
                breakdownHTML += `<li><span>${key}</span><strong>${value} / 10</strong></li>`;
            }
        } else {
            breakdownHTML += `<li>${playerData.breakdown}</li>`;
        }
        breakdownHTML += '</ul>';

        card.innerHTML = `
            <h3>${playerData.player_display_name}<span class="score-display">${playerData.start_score}</span></h3>
            <p style="color: var(--color-text-secondary); margin-bottom: 1rem;">
                ${playerData.position} | ${playerData.team} ${playerData.opponent ? `vs. ${playerData.opponent}` : ''}
            </p>
            <h4 style="margin-top: 1.5rem; margin-bottom: 0.5rem; color: var(--color-text-primary);">Season Averages</h4>
            ${statsHTML}
            <h4 style="margin-top: 1.5rem; margin-bottom: 0.5rem; color: var(--color-text-primary);">Score Breakdown</h4>
            ${breakdownHTML}`;
        resultsContainer.appendChild(card);
    }
    initialize();
    compareBtn.addEventListener('click', analyzePlayers);
});
