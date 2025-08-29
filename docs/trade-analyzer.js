document.addEventListener('DOMContentLoaded', async () => {
    // --- TEAM COLORS MAP (for styling player chips) ---
    const TEAM_COLORS = {
        'ARI': { bg: '#97233F', text: '#FFFFFF' }, 'ATL': { bg: '#A71930', text: '#FFFFFF' }, 'BAL': { bg: '#241773', text: '#FFFFFF' },
        'BUF': { bg: '#00338D', text: '#FFFFFF' }, 'CAR': { bg: '#0085CA', text: '#000000' }, 'CHI': { bg: '#0B162A', text: '#E64100' },
        'CIN': { bg: '#FB4F14', text: '#000000' }, 'CLE': { bg: '#311D00', text: '#FF3C00' }, 'DAL': { bg: '#041E42', text: '#FFFFFF' },
        'DEN': { bg: '#FB4F14', text: '#002244' }, 'DET': { bg: '#0076B6', text: '#FFFFFF' }, 'GB': { bg: '#203731', text: '#FFB612' },
        'HOU': { bg: '#03202F', text: '#A71930' }, 'IND': { bg: '#002C5F', text: '#FFFFFF' }, 'JAX': { bg: '#006778', text: '#FFFFFF' },
        'KC': { bg: '#E31837', text: '#FFB81C' }, 'LV': { bg: '#000000', text: '#A5ACAF' }, 'LAC': { bg: '#0080C6', text: '#FFC20E' },
        'LAR': { bg: '#003594', text: '#FFD100' }, 'MIA': { bg: '#008E97', text: '#F26A24' }, 'MIN': { bg: '#4F2683', text: '#FFC62F' },
        'NE': { bg: '#002244', text: '#C60C30' }, 'NO': { bg: '#D3BC8D', text: '#101820' }, 'NYG': { bg: '#0B2265', text: '#A71930' },
        'NYJ': { bg: '#125740', text: '#FFFFFF' }, 'PHI': { bg: '#004C54', text: '#A5ACAF' }, 'PIT': { bg: '#101820', text: '#FFB612' },
        'SF': { bg: '#AA0000', text: '#B3995D' }, 'SEA': { bg: '#002244', text: '#69BE28' }, 'TB': { bg: '#D50A0A', text: '#343434' },
        'TEN': { bg: '#0C2340', text: '#4B92DB' }, 'WAS': { bg: '#5A1414', text: '#FFB612' }, 'DEFAULT': { bg: '#333333', text: '#FFFFFF'}
    };
    
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
    
    async function initialize() {
        try {
            // --- FIX: Fetch the correct report filename ---
            const response = await fetch('./data/reports/trade_value_report.json');
            if (!response.ok) throw new Error(`Failed to fetch trade report. Status: ${response.status}`);
            TRADE_DATA = await response.json();
            
            // Populate the datalist for autocomplete search
            const fragment = document.createDocumentFragment();
            TRADE_DATA.forEach(p => {
                const option = document.createElement('option');
                option.value = p.player_name;
                fragment.appendChild(option);
            });
            playerDatalist.appendChild(fragment);
        } catch (error) {
            console.error("Failed to initialize trade analyzer:", error);
            // This is the error message you are seeing
            resultsContainer.innerHTML = '<p style="text-align: center; width: 100%;">Error loading trade data. Please ensure the workflow has run successfully.</p>';
            resultsContainer.style.display = 'block';
        }
    }

    function addPlayer(side, playerName) {
        if (!playerName) return;
        const player = TRADE_DATA.find(p => p.player_name === playerName);
        // Prevent adding duplicates
        if (player && !trade.a.some(p => p.player_name === playerName) && !trade.b.some(p => p.player_name === playerName)) {
            trade[side].push(player);
        }
        updateUI();
    }

    function removePlayer(side, playerName) {
        trade[side] = trade[side].filter(p => p.player_name !== playerName);
        updateUI();
    }
    
    function getTradeGrade(percentage) {
        if (percentage >= 55) return 'A';
        if (percentage > 51) return 'B';
        if (percentage >= 49) return 'C';
        if (percentage >= 45) return 'D';
        return 'F';
    }

    function updateUI() {
        renderPlayerChips();
        const allPlayersInTrade = [...trade.a, ...trade.b];
        if (allPlayersInTrade.length === 0) {
            resultsContainer.style.display = 'none';
            return;
        }
        resultsContainer.style.display = 'flex';

        const totalValueA = trade.a.reduce((sum, p) => sum + p.trade_value, 0);
        const totalValueB = trade.b.reduce((sum, p) => sum + p.trade_value, 0);
        const totalTradeValue = totalValueA + totalValueB;

        // Calculate each team's percentage of the total value
        const percentageA = totalTradeValue > 0 ? (totalValueA / totalTradeValue) * 100 : 50;
        const percentageB = totalTradeValue > 0 ? (totalValueB / totalTradeValue) * 100 : 50;

        gradeAEl.textContent = getTradeGrade(percentageA);
        gradeBEl.textContent = getTradeGrade(percentageB);
    }

    function renderPlayerChips() {
        playersContainerA.innerHTML = '';
        playersContainerB.innerHTML = '';
        trade.a.forEach(p => {
            const colors = TEAM_COLORS[p.team] || TEAM_COLORS['DEFAULT'];
            playersContainerA.innerHTML += `<div class="player-chip" style="background-color: ${colors.bg}; color: ${colors.text};"><span>${p.player_name} (${p.position}) - ${p.trade_value.toFixed(1)}</span><button style="color: ${colors.text};" data-side="a" data-name="${p.player_name}">&times;</button></div>`;
        });
        trade.b.forEach(p => {
            const colors = TEAM_COLORS[p.team] || TEAM_COLORS['DEFAULT'];
            playersContainerB.innerHTML += `<div class="player-chip" style="background-color: ${colors.bg}; color: ${colors.text};"><span>${p.player_name} (${p.position}) - ${p.trade_value.toFixed(1)}</span><button style="color: ${colors.text};" data-side="b" data-name="${p.player_name}">&times;</button></div>`;
        });
    }
    
    // Event Listeners
    addPlayerBtnA.addEventListener('click', () => { addPlayer('a', searchInputA.value); searchInputA.value = ''; });
    addPlayerBtnB.addEventListener('click', () => { addPlayer('b', searchInputB.value); searchInputB.value = ''; });
    // Add player on 'Enter' key press
    searchInputA.addEventListener('keydown', (e) => { if (e.key === 'Enter') { addPlayer('a', searchInputA.value); searchInputA.value = ''; } });
    searchInputB.addEventListener('keydown', (e) => { if (e.key === 'Enter') { addPlayer('b', searchInputB.value); searchInputB.value = ''; } });
    
    document.body.addEventListener('click', (e) => {
        if (e.target.matches('.player-chip button')) {
            removePlayer(e.target.dataset.side, e.target.dataset.name);
        }
    });

    initialize();
});
