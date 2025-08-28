document.addEventListener('DOMContentLoaded', async () => {
    // --- TEAM COLORS ---
    const TEAM_COLORS = {
        'ARI': { bg: '#97233F', text: '#FFFFFF' }, 'ATL': { bg: '#A71930', text: '#FFFFFF' }, 'BAL': { bg: '#241773', text: '#FFFFFF' },
        'BUF': { bg: '#00338D', text: '#FFFFFF' }, 'CAR': { bg: '#0085CA', text: '#000000' }, 'CHI': { bg: '#0B162A', text: '#E64100' },
        'CIN': { bg: '#FB4F14', text: '#000000' }, 'CLE': { bg: '#311D00', text: '#FF3C00' }, 'DAL': { bg: '#041E42', text: '#FFFFFF' },
        'DEN': { bg: '#FB4F14', text: '#002244' }, 'DET': { bg: '#0076B6', text: '#FFFFFF' }, 'GB': { bg: '#203731', text: '#FFB612' },
        'HOU': { bg: '#03202F', text: '#A71930' }, 'IND': { bg: '#002C5F', text: '#FFFFFF' }, 'JAC': 'JAX', 'JAX': { bg: '#006778', text: '#FFFFFF' },
        'KC': { bg: '#E31837', text: '#FFB81C' }, 'LV': { bg: '#000000', text: '#A5ACAF' }, 'LAC': { bg: '#0080C6', text: '#FFC20E' },
        'LAR': { bg: '#003594', text: '#FFD100' }, 'MIA': { bg: '#008E97', text: '#F26A24' }, 'MIN': { bg: '#4F2683', text: '#FFC62F' },
        'NE': { bg: '#002244', text: '#C60C30' }, 'NO': { bg: '#D3BC8D', text: '#101820' }, 'NYG': { bg: '#0B2265', text: '#A71930' },
        'NYJ': { bg: '#125740', text: '#FFFFFF' }, 'PHI': { bg: '#004C54', text: '#A5ACAF' }, 'PIT': { bg: '#101820', text: '#FFB612' },
        'SF': { bg: '#AA0000', text: '#B3995D' }, 'SEA': { bg: '#002244', text: '#69BE28' }, 'TB': { bg: '#D50A0A', text: '#343434' },
        'TEN': { bg: '#0C2340', text: '#4B92DB' }, 'WAS': { bg: '#5A1414', text: '#FFB612' }, 'DEFAULT': { bg: '#333333', text: '#FFFFFF'}
    };
    
    // --- GLOBAL STATE ---
    let MASTER_PLAYER_DATA = [];
    let trade = { a: [], b: [] };
    let playerChart = null;

    // --- DOM REFERENCES ---
    const playerDatalist = document.getElementById('player-list');
    // ... (other DOM refs are the same)
    const playersContainerA = document.getElementById('players-a-container');
    const playersContainerB = document.getElementById('players-b-container');
    const playerCompCtx = document.getElementById('player-comparison-chart').getContext('2d');


    async function initialize() {
        // ... (data fetching is the same)
    }

    // --- CORE FUNCTIONS ---
    // ... (addPlayer, removePlayer, calculateResults, getTradeGrade are the same)

    // --- UI UPDATE FUNCTIONS ---
    function updateUI() {
        renderPlayerChips();
        // ... (rest of the function is the same, calculates and displays grades/scores)
        updatePlayerComparisonChart(); // Add this call
    }

    function renderPlayerChips() {
        playersContainerA.innerHTML = '';
        playersContainerB.innerHTML = '';
        trade.a.forEach(p => {
            const colors = TEAM_COLORS[p.team] || TEAM_COLORS['DEFAULT'];
            playersContainerA.innerHTML += `
                <div class="player-chip" style="background-color: ${colors.bg}; color: ${colors.text}; border-color: ${colors.bg === '#000000' ? 'var(--color-border)' : colors.bg};">
                    <span>${p.name} (${p.pos})</span>
                    <button style="color: ${colors.text};" data-side="a" data-name="${p.name}">&times;</button>
                </div>`;
        });
        trade.b.forEach(p => {
             const colors = TEAM_COLORS[p.team] || TEAM_COLORS['DEFAULT'];
            playersContainerB.innerHTML += `
                <div class="player-chip" style="background-color: ${colors.bg}; color: ${colors.text}; border-color: ${colors.bg === '#000000' ? 'var(--color-border)' : colors.bg};">
                    <span>${p.name} (${p.pos})</span>
                    <button style="color: ${colors.text};" data-side="b" data-name="${p.name}">&times;</button>
                </div>`;
        });
    }

    // --- NEW: Player Comparison Chart ---
    function updatePlayerComparisonChart() {
        if (playerChart) playerChart.destroy();

        const allPlayersInTrade = [...trade.a, ...trade.b];
        if(allPlayersInTrade.length === 0) return;

        playerChart = new Chart(playerCompCtx, {
            type: 'bar',
            data: {
                labels: allPlayersInTrade.map(p => p.name),
                datasets: [
                    {
                        label: 'Season-Long Value (VORP)',
                        data: allPlayersInTrade.map(p => p.vorp),
                        backgroundColor: 'rgba(35, 134, 54, 0.7)',
                    },
                    {
                        label: 'Immediate Impact (Start Score)',
                        data: allPlayersInTrade.map(p => p.start_score),
                        backgroundColor: 'rgba(139, 148, 158, 0.7)',
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: { 
                    x: { ticks: { color: 'white' } },
                    y: { beginAtZero: true, ticks: { color: 'white' } }
                },
                plugins: {
                    legend: { labels: { color: 'white' } }
                }
            }
        });
    }
    
    // ... (Event listeners and initialization call are the same)
});
