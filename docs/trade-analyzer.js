document.addEventListener('DOMContentLoaded', async () => {
    // --- TEAM COLORS and GLOBAL STATE ---
    const TEAM_COLORS = { /* ... same color map as before ... */ };
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

            // Merge data into one master list using player name as the key
            const mergedData = new Map();
            vorpData.forEach(p => mergedData.set(p.player_display_name, { ...p }));
            startScoreData.forEach(p => {
                if (mergedData.has(p.player_display_name)) {
                    Object.assign(mergedData.get(p.player_display_name), p);
                }
            });

            MASTER_PLAYER_DATA = Array.from(mergedData.values()).map(p => ({
                name: p.player_display_name,
                pos: p.position,
                team: p.recent_team || p.team,
                vorp: parseFloat(p.vorp || 0),
                start_score: parseFloat(p.start_score || 0),
                stats: p.stats || {}
            }));
            
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

    // --- CORE LOGIC (addPlayer, removePlayer, calculateResults, getTradeGrade) ---
    // ... (These functions remain the same)

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

    function renderPlayerChips() { /* ... same as before ... */ }

    // --- NEW: Render the detailed stats table ---
    function renderStatsTable() {
        statsContainer.innerHTML = '';
        const allPlayersInTrade = [...trade.a, ...trade.b];
        if (allPlayersInTrade.length === 0) return;

        let tableHTML = `<table class="player-stats-table"><thead><tr><th>Player</th><th>VORP</th><th>Start Score</th>`;
        const statKeys = new Set();
        allPlayersInTrade.forEach(p => Object.keys(p.stats).forEach(key => statKeys.add(key)));
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
    
    // ... (updateChart, event listeners, and initialize call are the same)
});
