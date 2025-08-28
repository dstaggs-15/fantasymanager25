document.addEventListener('DOMContentLoaded', async () => {
    // --- TEAM COLORS MAP ---
    const TEAM_COLORS = { 'ARI': { bg: '#97233F', text: '#FFFFFF' }, 'ATL': { bg: '#A71930', text: '#FFFFFF' }, 'BAL': { bg: '#241773', text: '#FFFFFF' }, 'BUF': { bg: '#00338D', text: '#FFFFFF' }, 'CAR': { bg: '#0085CA', text: '#000000' }, 'CHI': { bg: '#0B162A', text: '#E64100' }, 'CIN': { bg: '#FB4F14', text: '#000000' }, 'CLE': { bg: '#311D00', text: '#FF3C00' }, 'DAL': { bg: '#041E42', text: '#FFFFFF' }, 'DEN': { bg: '#FB4F14', text: '#002244' }, 'DET': { bg: '#0076B6', text: '#FFFFFF' }, 'GB': { bg: '#203731', text: '#FFB612' }, 'HOU': { bg: '#03202F', text: '#A71930' }, 'IND': { bg: '#002C5F', text: '#FFFFFF' }, 'JAC': { bg: '#006778', text: '#FFFFFF' }, 'JAX': { bg: '#006778', text: '#FFFFFF' }, 'KC': { bg: '#E31837', text: '#FFB81C' }, 'LV': { bg: '#000000', text: '#A5ACAF' }, 'LAC': { bg: '#0080C6', text: '#FFC20E' }, 'LAR': { bg: '#003594', text: '#FFD100' }, 'MIA': { bg: '#008E97', text: '#F26A24' }, 'MIN': { bg: '#4F2683', text: '#FFC62F' }, 'NE': { bg: '#002244', text: '#C60C30' }, 'NO': { bg: '#D3BC8D', text: '#101820' }, 'NYG': { bg: '#0B2265', text: '#A71930' }, 'NYJ': { bg: '#125740', text: '#FFFFFF' }, 'PHI': { bg: '#004C54', text: '#A5ACAF' }, 'PIT': { bg: '#101820', text: '#FFB612' }, 'SF': { bg: '#AA0000', text: '#B3995D' }, 'SEA': { bg: '#002244', text: '#69BE28' }, 'TB': { bg: '#D50A0A', text: '#343434' }, 'TEN': { bg: '#0C2340', text: '#4B92DB' }, 'WAS': { bg: '#5A1414', text: '#FFB612' }, 'DEFAULT': { bg: '#333333', text: '#FFFFFF'} };
    
    let TRADE_DATA = [];
    let trade = { a: [], b: [] };

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
    const resultsContainer = document.getElementById('trade-results-container');
    const breakdownAEl = document.getElementById('breakdown-a');
    const breakdownBEl = document.getElementById('breakdown-b');

    async function initialize() {
        try {
            const response = await fetch('./data/reports/trade_report.json');
            if (!response.ok) throw new Error('Failed to fetch trade report');
            TRADE_DATA = await response.json();
            
            const fragment = document.createDocumentFragment();
            TRADE_DATA.forEach(p => {
                const option = document.createElement('option');
                option.value = p.player_name;
                fragment.appendChild(option);
            });
            playerDatalist.appendChild(fragment);
        } catch (error) {
            console.error("Failed to initialize trade analyzer:", error);
            resultsContainer.innerHTML = 'Error loading trade data. Please run the workflow.';
            resultsContainer.style.display = 'block';
        }
    }

    function addPlayer(side, playerName) {
        if (!playerName) return;
        const player = TRADE_DATA.find(p => p.player_name === playerName);
        if (player && !trade[side].some(p => p.player_name === playerName)) {
            trade[side].push(player);
        }
        updateUI();
    }

    function removePlayer(side, playerName) {
        trade[side] = trade[side].filter(p => p.player_name !== playerName);
        updateUI();
    }
    
    function getTradeGrade(value) {
        const score = value / 10; // Convert 100-scale value to 10-scale for grading
        if (score >= 9.5) return 'A+'; if (score >= 9.0) return 'A'; if (score >= 8.5) return 'A-';
        if (score >= 8.0) return 'B+'; if (score >= 7.5) return 'B'; if (score >= 7.0) return 'B-';
        if (score >= 6.5) return 'C+'; if (score >= 6.0) return 'C'; if (score >= 5.5) return 'C-';
        if (score >= 5.0) return 'D'; return 'F';
    }

    function updateUI() {
        renderPlayerChips();
        const allPlayersInTrade = [...trade.a, ...trade.b];
        if (allPlayersInTrade.length === 0) {
            resultsContainer.style.display = 'none';
            return;
        }
        resultsContainer.style.display = 'block';

        const totalValueA = trade.a.reduce((sum, p) => sum + p.trade_value, 0);
        const totalValueB = trade.b.reduce((sum, p) => sum + p.trade_value, 0);
        const totalTradeValue = totalValueA + totalValueB;

        const gradeScoreA = totalTradeValue > 0 ? (totalValueA / totalTradeValue) * 100 : 50;
        const gradeScoreB = totalTradeValue > 0 ? (totalValueB / totalTradeValue) * 100 : 50;

        gradeAEl.textContent = getTradeGrade(gradeScoreA);
        gradeBEl.textContent = getTradeGrade(gradeScoreB);
        
        renderBreakdown('a', breakdownAEl);
        renderBreakdown('b', breakdownBEl);
    }

    function renderPlayerChips() {
        playersContainerA.innerHTML = '';
        playersContainerB.innerHTML = '';
        trade.a.forEach(p => {
            const colors = TEAM_COLORS[p.team] || TEAM_COLORS['DEFAULT'];
            playersContainerA.innerHTML += `<div class="player-chip" style="background-color: ${colors.bg}; color: ${colors.text};"><span>${p.player_name} (${p.position})</span><button style="color: ${colors.text};" data-side="a" data-name="${p.player_name}">&times;</button></div>`;
        });
        trade.b.forEach(p => {
             const colors = TEAM_COLORS[p.team] || TEAM_COLORS['DEFAULT'];
            playersContainerB.innerHTML += `<div class="player-chip" style="background-color: ${colors.bg}; color: ${colors.text};"><span>${p.player_name} (${p.position})</span><button style="color: ${colors.text};" data-side="b" data-name="${p.player_name}">&times;</button></div>`;
        });
    }

    function renderBreakdown(side, element) {
        const players = trade[side];
        const totalValue = players.reduce((sum, p) => sum + p.trade_value, 0);

        let html = `<h4>Team ${side.toUpperCase()} Receives: ${totalValue.toFixed(1)} Total Value</h4>`;
        if (players.length === 0) {
            element.innerHTML = html;
            return;
        }
        
        const avgBreakdown = {};
        for (const player of players) {
            for (const key in player.breakdown) {
                avgBreakdown[key] = (avgBreakdown[key] || 0) + player.breakdown[key];
            }
        }
        for (const key in avgBreakdown) {
            avgBreakdown[key] /= players.length;
        }

        html += '<table class="breakdown-table">';
        for (const key in avgBreakdown) {
            html += `<tr><td>${key}</td><td>${avgBreakdown[key].toFixed(1)} / 10</td></tr>`;
        }
        html += '</table>';
        element.innerHTML = html;
    }
    
    addPlayerBtnA.addEventListener('click', () => { addPlayer('a', searchInputA.value); searchInputA.value = ''; });
    addPlayerBtnB.addEventListener('click', () => { addPlayer('b', searchInputB.value); searchInputB.value = ''; });
    document.body.addEventListener('click', (e) => { if (e.target.matches('button[data-side]')) { removePlayer(e.target.dataset.side, e.target.dataset.name); } });

    initialize();
});
