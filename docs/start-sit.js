document.addEventListener('DOMContentLoaded', () => {
    let ALL_PLAYER_DATA = [];
    const playerDatalist = document.getElementById('player-list');
    const analyzeBtn = document.getElementById('analyze-btn');
    const searchInputs = document.querySelectorAll('.player-search-input');
    const resultsArea = document.getElementById('results-area');

    async function initialize() {
        try {
            // This is the corrected file path
            const response = await fetch('./data/reports/start_score_report.json');
            if (!response.ok) throw new Error('Failed to load start score data');
            ALL_PLAYER_DATA = await response.json();

            // Populate the datalist for search autocomplete
            const fragment = document.createDocumentFragment();
            ALL_PLAYER_DATA.forEach(p => {
                const option = document.createElement('option');
                option.value = p.player_name;
                fragment.appendChild(option);
            });
            playerDatalist.appendChild(fragment);
        } catch (error) {
            console.error(error);
            resultsArea.innerHTML = `<div class="card error-card"><p>Error loading player data. Please ensure the backend workflow has run successfully.</p></div>`;
        }
    }

    function analyzePlayers() {
        resultsArea.innerHTML = ''; // Clear previous results
        const playerNames = Array.from(searchInputs).map(input => input.value).filter(name => name.trim() !== '');
        
        if (playerNames.length === 0) return;

        const playersToDisplay = playerNames.map(name => ALL_PLAYER_DATA.find(p => p.player_name === name)).filter(Boolean);

        // Sort players by start_score so the best option is first
        playersToDisplay.sort((a, b) => b.start_score - a.start_score);

        playersToDisplay.forEach(player => {
            renderPlayerCard(player);
        });
    }

    function getRecommendation(score) {
        if (score >= 8.0) return { text: 'Must Start', className: 'rec-must-start' };
        if (score >= 6.5) return { text: 'Strong Start', className: 'rec-strong-start' };
        if (score >= 5.0) return { text: 'Good Flex', className: 'rec-good-flex' };
        if (score >= 4.0) return { text: 'Risky Flex', className: 'rec-risky-flex' };
        return { text: 'Risky Sit', className: 'rec-sit' };
    }

    function renderPlayerCard(player) {
        const recommendation = getRecommendation(player.start_score);
        const cardHTML = `
            <div class="player-card">
                <div class="card-header">
                    <div>
                        <span class="player-name">${player.player_name}</span>
                        <span class="player-info">${player.position} - ${player.team}</span>
                    </div>
                    <span class="recommendation-pill ${recommendation.className}">${recommendation.text}</span>
                </div>
                <div class="card-footer">
                    <span>Overall Start Score</span>
                    <span>${player.start_score.toFixed(2)}</span>
                </div>
                <div class="card-body breakdown">
                    <div class="stat-box">
                        <span class="stat-value">${player.talent_score.toFixed(1)}</span>
                        <span class="stat-label">Talent (40%)</span>
                    </div>
                    <div class="stat-box">
                        <span class="stat-value">${player.matchup_score.toFixed(1)}</span>
                        <span class="stat-label">Matchup (30%)</span>
                    </div>
                    <div class="stat-box">
                        <span class="stat-value">${player.oline_score.toFixed(1)}</span>
                        <span class="stat-label">O-Line (15%)</span>
                    </div>
                    <div class="stat-box">
                        <span class="stat-value">${player.efficiency_score.toFixed(1)}</span>
                        <span class="stat-label">Efficiency (15%)</span>
                    </div>
                </div>
            </div>
        `;
        resultsArea.innerHTML += cardHTML;
    }

    analyzeBtn.addEventListener('click', analyzePlayers);
    initialize();
});
