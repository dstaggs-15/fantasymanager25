document.addEventListener('DOMContentLoaded', async () => {
    // --- GLOBAL STATE ---
    let MASTER_PLAYER_DATA = [];
    let trade = { a: [], b: [] };
    let tradeChart = null;

    // --- DOM REFERENCES ---
    const playerDatalist = document.getElementById('player-list');
    const addPlayerBtnA = document.getElementById('add-player-a');
    const addPlayerBtnB = document.getElementById('add-player-b');
    const searchInputA = document.getElementById('player-search-a');
    const searchInputB = document.getElementById('player-search-b');
    const playersContainerA = document.getElementById('players-a-container');
    const playersContainerB = document.getElementById('players-b-container');
    const gradeAEl = document.getElementById('grade-a');
    const gradeBEl = document.getElementById('grade-b');
    const vorpAEl = document.getElementById('vorp-a');
    const vorpBEl = document.getElementById('vorp-b');
    const startScoreAEl = document.getElementById('start-score-a');
    const startScoreBEl = document.getElementById('start-score-b');
    const chartCtx = document.getElementById('trade-chart').getContext('2d');

    // --- DATA INITIALIZATION ---
    async function initialize() {
        try {
            const [vorpRes, startScoreRes] = await Promise.all([
                fetch('./data/reports/vorp_report.json'),
                fetch('./data/reports/start_scores.json')
            ]);
            const vorpData = await vorpRes.json();
            const startScoreData = await startScoreRes.json();

            // Merge data into one master list
            MASTER_PLAYER_DATA = vorpData.map(player => {
                const ssData = startScoreData.find(p => p.player_display_name === player.player_display_name);
                return {
                    name: player.player_display_name,
                    pos: player.position,
                    team: player.recent_team,
                    vorp: parseFloat(player.vorp || 0),
                    start_score: parseFloat(ssData?.start_score || 0)
                };
            });

            // Populate autocomplete
            const fragment = document.createDocumentFragment();
            MASTER_PLAYER_DATA.forEach(p => {
                const option = document.createElement('option');
                option.value = p.name;
                fragment.appendChild(option);
            });
            playerDatalist.appendChild(fragment);

        } catch (error) {
            console.error("Failed to initialize trade analyzer:", error);
        }
    }

    // --- CORE FUNCTIONS ---
    function addPlayer(side, playerName) {
        if (!playerName) return;
        const player = MASTER_PLAYER_DATA.find(p => p.name === playerName);
        if (player && !trade[side].some(p => p.name === playerName)) {
            trade[side].push(player);
        }
        updateUI();
    }

    function removePlayer(side, playerName) {
        trade[side] = trade[side].filter(p => p.name !== playerName);
        updateUI();
    }
    
    function calculateResults() {
        const results = { a: { vorp: 0, start_score: 0 }, b: { vorp: 0, start_score: 0 } };
        for (const side in trade) {
            trade[side].forEach(p => {
                results[side].vorp += p.vorp;
                results[side].start_score += p.start_score;
            });
        }
        return results;
    }
    
    function getTradeGrade(value) {
        if (value >= 90) return 'A+'; if (value >= 85) return 'A'; if (value >= 80) return 'A-';
        if (value >= 75) return 'B+'; if (value >= 70) return 'B'; if (value >= 65) return 'B-';
        if (value >= 60) return 'C+'; if (value >= 55) return 'C'; if (value >= 50) return 'C-';
        if (value >= 40) return 'D'; return 'F';
    }

    // --- UI UPDATE FUNCTIONS ---
    function updateUI() {
        renderPlayerChips();
        const results = calculateResults();
        
        // Calculate total values
        const totalVorp = results.a.vorp + results.b.vorp;
        const totalStartScore = results.a.start_score + results.b.start_score;

        // Calculate weighted scores for grading
        const scoreA = (totalVorp > 0 ? (results.a.vorp / totalVorp) * 100 * 0.7 : 0) + (totalStartScore > 0 ? (results.a.start_score / totalStartScore) * 100 * 0.3 : 0);
        const scoreB = (totalVorp > 0 ? (results.b.vorp / totalVorp) * 100 * 0.7 : 0) + (totalStartScore > 0 ? (results.b.start_score / totalStartScore) * 100 * 0.3 : 0);

        // Update DOM
        vorpAEl.textContent = results.a.vorp.toFixed(2);
        vorpBEl.textContent = results.b.vorp.toFixed(2);
        startScoreAEl.textContent = results.a.start_score.toFixed(1);
        startScoreBEl.textContent = results.b.start_score.toFixed(1);
        gradeAEl.textContent = (totalVorp > 0 || totalStartScore > 0) ? getTradeGrade(scoreA) : '-';
        gradeBEl.textContent = (totalVorp > 0 || totalStartScore > 0) ? getTradeGrade(scoreB) : '-';
        
        updateChart(results);
    }

    function renderPlayerChips() {
        playersContainerA.innerHTML = '';
        playersContainerB.innerHTML = '';
        trade.a.forEach(p => {
            playersContainerA.innerHTML += `<div class="player-chip"><span>${p.name} (${p.pos})</span><button data-side="a" data-name="${p.name}">&times;</button></div>`;
        });
        trade.b.forEach(p => {
            playersContainerB.innerHTML += `<div class="player-chip"><span>${p.name} (${p.pos})</span><button data-side="b" data-name="${p.name}">&times;</button></div>`;
        });
    }

    function updateChart(results) {
        if (tradeChart) tradeChart.destroy();
        tradeChart = new Chart(chartCtx, {
            type: 'bar',
            data: {
                labels: ['Season-Long Value (VORP)', 'Immediate Impact (Start Score)'],
                datasets: [
                    { label: 'Team A Receives', data: [results.a.vorp, results.a.start_score], backgroundColor: 'rgba(35, 134, 54, 0.7)' },
                    { label: 'Team B Receives', data: [results.b.vorp, results.b.start_score], backgroundColor: 'rgba(139, 148, 158, 0.7)' }
                ]
            },
            options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true } } }
        });
    }

    // --- EVENT LISTENERS ---
    addPlayerBtnA.addEventListener('click', () => { addPlayer('a', searchInputA.value); searchInputA.value = ''; });
    addPlayerBtnB.addEventListener('click', () => { addPlayer('b', searchInputB.value); searchInputB.value = ''; });
    
    // Event delegation for remove buttons
    document.body.addEventListener('click', (e) => {
        if (e.target.matches('button[data-side]')) {
            removePlayer(e.target.dataset.side, e.target.dataset.name);
        }
    });

    // --- INITIALIZE ---
    initialize();
    updateUI(); // Initial render
});
