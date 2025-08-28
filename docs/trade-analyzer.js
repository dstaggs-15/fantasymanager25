document.addEventListener('DOMContentLoaded', async () => {
    // --- TEAM COLORS MAP ---
    const TEAM_COLORS = {
        'ARI': { bg: '#97233F', text: '#FFFFFF' }, 'ATL': { bg: '#A71930', text: '#FFFFFF' }, 'BAL': { bg: '#241773', text: '#FFFFFF' },
        'BUF': { bg: '#00338D', text: '#FFFFFF' }, 'CAR': { bg: '#0085CA', text: '#000000' }, 'CHI': { bg: '#0B162A', text: '#E64100' },
        'CIN': { bg: '#FB4F14', text: '#000000' }, 'CLE': { bg: '#311D00', text: '#FF3C00' }, 'DAL': { bg: '#041E42', text: '#FFFFFF' },
        'DEN': { bg: '#FB4F14', text: '#002244' }, 'DET': { bg: '#0076B6', text: '#FFFFFF' }, 'GB': { bg: '#203731', text: '#FFB612' },
        'HOU': { bg: '#03202F', text: '#A71930' }, 'IND': { bg: '#002C5F', text: '#FFFFFF' }, 'JAC': { bg: '#006778', text: '#FFFFFF' }, 'JAX': { bg: '#006778', text: '#FFFFFF' },
        'KC': { bg: '#E31837', text: '#FFB81C' }, 'LV': { bg: '#000000', text: '#A5ACAF' }, 'LAC': { bg: '#0080C6', text: '#FFC20E' },
        'LAR': { bg: '#003594', text: '#FFD100' }, 'MIA': { bg: '#008E97', text: '#F26A24' }, 'MIN': { bg: '#4F2683', text: '#FFC62F' },
        'NE': { bg: '#002244', text: '#C60C30' }, 'NO': { bg: '#D3BC8D', text: '#101820' }, 'NYG': { bg: '#0B2265', text: '#A71930' },
        'NYJ': { bg: '#125740', text: '#FFFFFF' }, 'PHI': { bg: '#004C54', text: '#A5ACAF' }, 'PIT': { bg: '#101820', text: '#FFB612' },
        'SF': { bg: '#AA0000', text: '#B3995D' }, 'SEA': { bg: '#002244', text: '#69BE28' }, 'TB': { bg: '#D50A0A', text: '#343434' },
        'TEN': { bg: '#0C2340', text: '#4B92DB' }, 'WAS': { bg: '#5A1414', text: '#FFB612' }, 'DEFAULT': { bg: '#333333', text: '#FFFFFF'}
    };
    
    // --- GLOBAL STATE & DOM REFERENCES ---
    let MASTER_PLAYER_DATA = [];
    let trade = { a: [], b: [] };
    let tradeChart = null;
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
    const statsContainer = document.getElementById('player-stats-container');

    // --- DATA INITIALIZATION ---
    async function initialize() {
        try {
            const [vorpRes, startScoreRes] = await Promise.all([
                fetch('./data/reports/vorp_report.json'),
                fetch('./data/reports/start_scores.json')
            ]);
            const vorpData = await vorpRes.json();
            const startScoreData = await startScoreRes.json();

            // Create a map of start score data for efficient lookup
            const startScoreMap = new Map(startScoreData.map(p => [p.player_display_name, p]));

            // Build the master list, ensuring VORP is correctly included
            MASTER_PLAYER_DATA = vorpData.map(player => {
                const ssData = startScoreMap.get(player.player_display_name);
                return {
                    name: player.player_display_name,
                    pos: player.position,
                    team: player.recent_team,
                    vorp: parseFloat(player.vorp || 0), // Directly use VORP from the report
                    start_score: parseFloat(ssData?.start_score || 0),
                    stats: ssData?.stats || {}
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
            document.querySelector('.container').innerHTML = '<h1>Error</h1><p>Could not load necessary data files. Please ensure the workflow has run successfully.</p>';
        }
    }

    // --- CORE LOGIC (addPlayer, removePlayer, etc.) ---
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
        
        const totalVorp = results.a.vorp + results.b.vorp;
        const totalStartScore = results.a.start_score + results.b.start_score;

        const scoreA = (totalVorp > 0 ? (results.a.vorp / totalVorp) * 100 * 0.7 : 35) + 
                       (totalStartScore > 0 ? (results.a.start_score / totalStartScore) * 100 * 0.3 : 15);
        const scoreB = (totalVorp > 0 ? (results.b.vorp / totalVorp) * 100 * 0.7 : 35) + 
                       (totalStartScore > 0 ? (results.b.start_score / totalStartScore) * 100 * 0.3 : 15);

        vorpAEl.textContent = results.a.vorp.toFixed(2);
        vorpBEl.textContent = results.b.vorp.toFixed(2);
        startScoreAEl.textContent = results.a.start_score.toFixed(1);
        startScoreBEl.textContent = results.b.start_score.toFixed(1);
        gradeAEl.textContent = (totalVorp > 0 || totalStartScore > 0) ? getTradeGrade(scoreA) : '-';
        gradeBEl.textContent = (totalVorp > 0 || totalStartScore > 0) ? getTradeGrade(scoreB) : '-';
        
        updateChart(results);
        renderStatsTable();
    }

    function renderPlayerChips() {
        playersContainerA.innerHTML = '';
        playersContainerB.innerHTML = '';
        trade.a.forEach(p => {
            const colors = TEAM_COLORS[p.team] || TEAM_COLORS['DEFAULT'];
            playersContainerA.innerHTML += `<div class="player-chip" style="background-color: ${colors.bg}; color: ${colors.text}; border-color: ${colors.bg === '#000000' ? 'var(--color-border)' : colors.bg};"><span>${p.name} (${p.pos})</span><button style="color: ${colors.text};" data-side="a" data-name="${p.name}">&times;</button></div>`;
        });
        trade.b.forEach(p => {
             const colors = TEAM_COLORS[p.team] || TEAM_COLORS['DEFAULT'];
            playersContainerB.innerHTML += `<div class="player-chip" style="background-color: ${colors.bg}; color: ${colors.text}; border-color: ${colors.bg === '#000000' ? 'var(--color-border)' : colors.bg};"><span>${p.name} (${p.pos})</span><button style="color: ${colors.text};" data-side="b" data-name="${p.name}">&times;</button></div>`;
        });
    }

    function renderStatsTable() {
        statsContainer.innerHTML = '';
        const allPlayersInTrade = [...trade.a, ...trade.b];
        if (allPlayersInTrade.length === 0) return;

        let tableHTML = `<table class="player-stats-table"><thead><tr><th>Player</th><th>VORP</th><th>Start Score</th>`;
        const statKeys = new Set();
        allPlayersInTrade.forEach(p => {
            if (p.stats) Object.keys(p.stats).forEach(key => statKeys.add(key));
        });
        
        statKeys.forEach(key => tableHTML += `<th>${key}</th>`);
        tableHTML += `</tr></thead><tbody>`;

        allPlayersInTrade.forEach(p => {
            tableHTML += `<tr><td>${p.name}</td><td>${p.vorp.toFixed(2)}</td><td>${p.start_score.toFixed(1)}</td>`;
            statKeys.forEach(key => tableHTML += `<td>${p.stats[key] || '-'}</td>`);
            tableHTML += `</tr>`;
        });

        tableHTML += `</tbody></table>`;
        statsContainer.innerHTML = tableHTML;
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
    document.body.addEventListener('click', (e) => { if (e.target.matches('button[data-side]')) { removePlayer(e.target.dataset.side, e.target.dataset.name); } });

    // --- INITIALIZE ---
    initialize();
    updateUI();
});
