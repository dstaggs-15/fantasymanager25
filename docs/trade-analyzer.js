document.addEventListener('DOMContentLoaded', async () => {
    // --- Official NFL Team Colors ---
    const TEAM_COLORS = {
        'ARI': { bg: '#97233F', text: '#FFFFFF' }, 'ATL': { bg: '#A71930', text: '#000000' }, 'BAL': { bg: '#241773', text: '#9E7C0C' },
        'BUF': { bg: '#00338D', text: '#C60C30' }, 'CAR': { bg: '#0085CA', text: '#101820' }, 'CHI': { bg: '#0B162A', text: '#C83803' },
        'CIN': { bg: '#FB4F14', text: '#000000' }, 'CLE': { bg: '#311D00', text: '#FF3C00' }, 'DAL': { bg: '#041E42', text: '#869397' },
        'DEN': { bg: '#FB4F14', text: '#002244' }, 'DET': { bg: '#0076B6', text: '#B0B7BC' }, 'GB': { bg: '#203731', text: '#FFB612' },
        'HOU': { bg: '#03202F', text: '#A71930' }, 'IND': { bg: '#002C5F', text: '#A2AAAD' }, 'JAX': { bg: '#101820', text: '#006778' },
        'KC': { bg: '#E31837', text: '#FFB81C' }, 'LV': { bg: '#000000', text: '#A5ACAF' }, 'LAC': { bg: '#0080C6', text: '#FFC20E' },
        'LAR': { bg: '#003594', text: '#FFD100' }, 'MIA': { bg: '#008E97', text: '#FC4C02' }, 'MIN': { bg: '#4F2683', text: '#FFC62F' },
        'NE': { bg: '#002244', text: '#C60C30' }, 'NO': { bg: '#D3BC8D', text: '#101820' }, 'NYG': { bg: '#0B2265', text: '#A71930' },
        'NYJ': { bg: '#125740', text: '#FFFFFF' }, 'PHI': { bg: '#004C54', text: '#A5ACAF' }, 'PIT': { bg: '#101820', text: '#FFB612' },
        'SF': { bg: '#AA0000', text: '#B3995D' }, 'SEA': { bg: '#002244', text: '#69BE28' }, 'TB': { bg: '#D50A0A', text: '#343434' },
        'TEN': { bg: '#0C2340', text: '#4B92DB' }, 'WAS': { bg: '#5A1414', text: '#FFB612' }, 'DEFAULT': { bg: '#333333', text: '#FFFFFF'}
    };
    
    let ALL_PLAYER_DATA = [];
    let trade = { a: [], b: [] };

    // DOM References
    const playerDatalist = document.getElementById('player-list');
    const addPlayerBtnA = document.getElementById('add-player-a');
    const addPlayerBtnB = document.getElementById('add-player-b');
    const searchInputA = document.getElementById('player-search-a');
    const searchInputB = document.getElementById('player-search-b');
    const playersContainerA = document.getElementById('players-a-container');
    const playersContainerB = document.getElementById('players-b-container');
    const gradeAEl = document.getElementById('grade-a');
    const gradeBEl = document.getElementById('grade-b');
    const valueAEl = document.getElementById('value-a');
    const valueBEl = document.getElementById('value-b');
    const resultsContainer = document.getElementById('trade-results-container');
    const tradeSummaryBox = document.getElementById('trade-summary-box');

    async function initialize() {
        try {
            const [tradeValueRes, vorpRes, rosRes] = await Promise.all([
                fetch('./docs/data/reports/trade_value_report.json'),
                fetch('./docs/data/reports/vorp_analyzer_report.json'),
                fetch('./docs/data/reports/ros_projections.json')
            ]);
            if (!tradeValueRes.ok || !vorpRes.ok || !rosRes.ok) throw new Error('One or more data files failed to load.');
            
            const tradeValues = await tradeValueRes.json();
            const vorpData = await vorpRes.json();
            const rosData = await rosRes.json();
            
            ALL_PLAYER_DATA = mergeData(tradeValues, vorpData, rosData);
            
            const fragment = document.createDocumentFragment();
            ALL_PLAYER_DATA.forEach(p => {
                const option = document.createElement('option');
                option.value = p.player_name;
                fragment.appendChild(option);
            });
            playerDatalist.appendChild(fragment);
        } catch (error) {
            console.error("Failed to initialize trade analyzer:", error);
            document.querySelector('.container').innerHTML = `<h1>Trade Analyzer</h1><div class="card error-card"><p>Error loading trade data. Please ensure the backend workflow has run successfully and all report files exist in the <code>/docs/data/reports/</code> directory.</p></div>`;
        }
    }

    function mergeData(tradeValues, vorpData, rosData) {
        const playerMap = new Map();
        vorpData.forEach(p => playerMap.set(p.player_id, p));
        rosData.forEach(p => { if (playerMap.has(p.player_id)) playerMap.set(p.player_id, { ...playerMap.get(p.player_id), ...p }); });
        tradeValues.forEach(p => { if (playerMap.has(p.player_id)) playerMap.set(p.player_id, { ...playerMap.get(p.player_id), ...p }); });
        return Array.from(playerMap.values());
    }

    function addPlayer(side, playerName) {
        if (!playerName) return;
        const player = ALL_PLAYER_DATA.find(p => p.player_name === playerName);
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
        if (percentage >= 55) return 'A'; if (percentage > 52) return 'B';
        if (percentage >= 48) return 'C'; if (percentage >= 45) return 'D';
        return 'F';
    }

    function updateUI() {
        renderPlayerCards();
        if ([...trade.a, ...trade.b].length === 0) {
            resultsContainer.style.display = 'none';
            return;
        }
        resultsContainer.style.display = 'block';

        const totalValueA = trade.a.reduce((sum, p) => sum + (p.trade_value || 0), 0);
        const totalValueB = trade.b.reduce((sum, p) => sum + (p.trade_value || 0), 0);
        const totalTradeValue = totalValueA + totalValueB;

        const percentageA = totalTradeValue > 0 ? (totalValueA / totalTradeValue) * 100 : 50;
        const percentageB = totalTradeValue > 0 ? (totalValueB / totalTradeValue) * 100 : 50;

        gradeAEl.textContent = getTradeGrade(percentageA);
        gradeBEl.textContent = getTradeGrade(percentageB);
        
        valueAEl.textContent = `Total Value: ${totalValueA.toFixed(1)}`;
        valueBEl.textContent = `Total Value: ${totalValueB.toFixed(1)}`;

        renderTradeSummary(totalValueA, totalValueB);
    }

    function renderPlayerCards() {
        playersContainerA.innerHTML = '';
        playersContainerB.innerHTML = '';
        ['a', 'b'].forEach(side => {
            const container = side === 'a' ? playersContainerA : playersContainerB;
            trade[side].forEach(p => {
                const colors = TEAM_COLORS[p.team] || TEAM_COLORS['DEFAULT'];
                container.innerHTML += `
                    <div class="player-card">
                        <div class="card-header" style="background-color: ${colors.bg}; color: ${colors.text};">
                            <div>
                                <span class="player-name">${p.player_name}</span>
                                <span class="player-info">${p.position} - ${p.team}</span>
                            </div>
                            <button class="remove-btn" style="color: ${colors.text};" data-side="${side}" data-name="${p.player_name}">&times;</button>
                        </div>
                        <div class="card-body">
                            <div class="stat-box">
                                <span class="stat-value">${(p.ppg || 0).toFixed(2)}</span>
                                <span class="stat-label">PPG</span>
                            </div>
                            <div class="stat-box">
                                <span class="stat-value">${(p.vorp || 0).toFixed(2)}</span>
                                <span class="stat-label">VORP</span>
                            </div>
                            <div class="stat-box">
                                <span class="stat-value">${(p.ros_projection || 0).toFixed(1)}</span>
                                <span class="stat-label">ROS Proj.</span>
                            </div>
                        </div>
                        <div class="card-footer">
                            <span>Trade Value</span>
                            <span>${(p.trade_value || 0).toFixed(1)}</span>
                        </div>
                    </div>
                `;
            });
        });
    }
    
    function renderTradeSummary(valueA, valueB) {
        const difference = valueA - valueB;
        let text = '';
        let className = '';

        if (Math.abs(difference) < 2.0) {
            text = 'This is a fair and balanced trade.';
            className = 'summary-even';
        } else if (difference > 0) {
            text = `Team A wins this trade by +${difference.toFixed(1)} value.`;
            className = 'summary-win';
        } else {
            text = `Team B wins this trade by +${Math.abs(difference).toFixed(1)} value.`;
            className = 'summary-loss';
        }
        tradeSummaryBox.innerHTML = `<div class="trade-summary ${className}">${text}</div>`;
    }

    // Event Listeners
    addPlayerBtnA.addEventListener('click', () => { addPlayer('a', searchInputA.value); searchInputA.value = ''; });
    addPlayerBtnB.addEventListener('click', () => { addPlayer('b', searchInputB.value); searchInputB.value = ''; });
    searchInputA.addEventListener('keydown', (e) => { if (e.key === 'Enter') { addPlayer('a', searchInputA.value); searchInputA.value = ''; } });
    searchInputB.addEventListener('keydown', (e) => { if (e.key === 'Enter') { addPlayer('b', searchInputB.value); searchInputB.value = ''; } });
    
    document.body.addEventListener('click', (e) => {
        if (e.target.matches('.remove-btn')) {
            removePlayer(e.target.dataset.side, e.target.dataset.name);
        }
    });

    initialize();
});
