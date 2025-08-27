document.addEventListener('DOMContentLoaded', async () => {
    // --- DOM REFERENCES ---
    const playerInputs = [
        document.getElementById('player1'),
        document.getElementById('player2'),
        document.getElementById('player3'),
    ];
    const compareBtn = document.getElementById('compare-btn');
    const resultsContainer = document.getElementById('results-container');
    const playerDatalist = document.getElementById('player-list');

    // --- GLOBAL DATA STORE ---
    let START_SCORE_DATA = [];

    // --- INITIALIZATION ---
    async function initialize() {
        try {
            const response = await fetch('./data/reports/start_scores.json');
            if (!response.ok) throw new Error('Failed to fetch Start Score data');
            START_SCORE_DATA = await response.json();
            
            // Populate autocomplete
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
            resultsContainer.innerHTML = `<p>Error loading analysis data. Please ensure the workflow has run successfully.</p>`;
        }
    }

    // --- CORE LOGIC ---
    function analyzePlayers() {
        resultsContainer.innerHTML = ''; // Clear previous results

        const selectedPlayerNames = playerInputs
            .map(input => input.value)
            .filter(name => name.trim() !== '');

        if (selectedPlayerNames.length === 0) return;

        selectedPlayerNames.forEach(playerName => {
            const playerData = START_SCORE_DATA.find(p => p.player_display_name === playerName);
            renderCard(playerData, playerName);
        });
    }

    // --- RENDERING ---
    function renderCard(playerData, playerName) {
        const card = document.createElement('div');
        card.className = 'player-card';

        if (!playerData) {
            card.innerHTML = `<h3>${playerName}</h3><p class="matchup-bad">Player not found in analysis data.</p>`;
            resultsContainer.appendChild(card);
            return;
        }

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
            <h3>
                ${playerData.player_display_name}
                <span class="score-display">${playerData.start_score}</span>
            </h3>
            <p style="color: var(--color-text-secondary); margin-bottom: 1rem;">
                ${playerData.position} | ${playerData.team} ${playerData.opponent ? `vs. ${playerData.opponent}` : ''}
            </p>
            ${breakdownHTML}
        `;
        resultsContainer.appendChild(card);
    }

    initialize();
    compareBtn.addEventListener('click', analyzePlayers);
});
