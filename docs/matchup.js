document.addEventListener('DOMContentLoaded', async () => {
    const searchInput = document.getElementById('player-search');
    const playerDatalist = document.getElementById('player-list');
    const deepDiveContainer = document.getElementById('deep-dive-container');
    
    let allPlayers = [];
    let allMatchups = {};
    let fullDataset = [];

    try {
        // Load all necessary data files in parallel
        const [matchupRes, vorpRes, fullDataRes] = await Promise.all([
            fetch('data/analysis/matchup_report.json'),
            fetch('data/analysis/vorp_analysis.json'),
            fetch('data/analysis/nfl_data.csv').then(res => res.text())
        ]);

        if (!matchupRes.ok || !vorpRes.ok) throw new Error('Failed to load analysis reports.');

        const matchupData = await matchupRes.json();
        const vorpData = await vorpRes.json();
        
        // Parse the CSV data
        Papa.parse(fullDataRes, {
            header: true,
            dynamicTyping: true,
            complete: (results) => {
                fullDataset = results.data;
                
                // Create lookup maps for quick access
                allPlayers = vorpData.players;
                allMatchups = matchupData.matchups.reduce((obj, item) => {
                    obj[item.player] = item;
                    return obj;
                }, {});

                populateDatalist(allPlayers);
                console.log("All data loaded and ready for analysis.");
            }
        });

    } catch (error) {
        deepDiveContainer.innerHTML = `<p class="error">Failed to load necessary data files. Please ensure all analysis workflows have run successfully.</p>`;
        console.error('Error loading data:', error);
    }

    searchInput.addEventListener('change', () => {
        const playerName = searchInput.value;
        const playerVorp = allPlayers.find(p => p.player_display_name === playerName);
        const playerMatchup = allMatchups[playerName];
        
        if (playerVorp && playerMatchup) {
            renderPlayerDeepDive(playerVorp, playerMatchup);
        } else {
            deepDiveContainer.innerHTML = '';
        }
    });

    function populateDatalist(players) {
        players.forEach(player => {
            const option = document.createElement('option');
            option.value = player.player_display_name;
            playerDatalist.appendChild(option);
        });
    }

    function renderPlayerDeepDive(player, matchup) {
        // Get the player's weekly scores from last season
        const lastSeasonGames = fullDataset.filter(row => row.player_display_name === player.player_display_name && row.season === 2024);
        
        let deepDiveHTML = `
            <div class="report-card">
                <h2>${player.player_display_name} - ${player.position}</h2>
                <div class="report-grid">
                    <div><h3>Matchup: vs. ${matchup.opponent}</h3><p class="rating-${matchup.rating.toLowerCase().replace(' ', '')}">${matchup.rating} (${matchup.details})</p></div>
                    <div><h3>Projection</h3><p>${matchup.projection.toFixed(2)}</p></div>
                    <div><h3>VORP</h3><p>${player.vorp.toFixed(2)}</p></div>
                    <div><h3>PPG (2024)</h3><p>${player.ppg.toFixed(2)}</p></div>
                </div>
            </div>
            <div class="report-card">
                <h3>2024 Weekly Performance</h3>
                <canvas id="weeklyScoreChart"></canvas>
            </div>
        `;
        deepDiveContainer.innerHTML = deepDiveHTML;

        // Render the weekly performance chart
        const ctx = document.getElementById('weeklyScoreChart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: lastSeasonGames.map(g => `Week ${g.week}`),
                datasets: [{
                    label: 'Fantasy Points',
                    data: lastSeasonGames.map(g => g.fantasy_points_custom),
                    backgroundColor: 'rgba(97, 218, 251, 0.6)'
                }]
            },
            options: {
                 scales: { x: { ticks: { color: '#e0e0e0' } }, y: { ticks: { color: '#e0e0e0' }, beginAtZero: true } },
                 plugins: { legend: { display: false } }
            }
        });
    }
});
