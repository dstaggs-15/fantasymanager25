document.addEventListener('DOMContentLoaded', async () => {
    const deepDiveContainer = document.getElementById('deep-dive-container');
    
    try {
        // Load all necessary data files in parallel
        const [matchupRes, vorpRes, fullDataRes] = await Promise.all([
            fetch('data/analysis/matchup_report.json'),
            fetch('data/analysis/vorp_analysis.json'),
            fetch('data/analysis/nfl_data.csv').then(res => {
                if (!res.ok) throw new Error(`CSV file not found: ${res.status}`);
                return res.text();
            })
        ]);

        if (!matchupRes.ok || !vorpRes.ok) {
            throw new Error('Failed to load analysis reports. Please ensure the main workflow has run successfully.');
        }

        const matchupData = await matchupRes.json();
        const vorpData = await vorpRes.json();
        
        Papa.parse(fullDataRes, {
            header: true,
            dynamicTyping: true,
            complete: (results) => {
                const fullDataset = results.data;
                const allPlayers = vorpData.players;
                const allMatchups = matchupData.matchups.reduce((obj, item) => {
                    obj[item.player] = item;
                    return obj;
                }, {});

                initializePage(allPlayers, allMatchups, fullDataset);
                console.log("All data loaded and ready for analysis.");
            }
        });

    } catch (error) {
        if(deepDiveContainer) deepDiveContainer.innerHTML = `<div class="report-card"><p style="color: #F44336;">${error.message}</p></div>`;
        console.error('Error loading data:', error);
    }
});

function initializePage(allPlayers, allMatchups, fullDataset) {
    const searchInput = document.getElementById('player-search');
    const playerDatalist = document.getElementById('player-list');
    
    // Populate the search box datalist
    allPlayers.sort((a, b) => a.player_display_name.localeCompare(b.player_display_name));
    allPlayers.forEach(player => {
        const option = document.createElement('option');
        option.value = player.player_display_name;
        playerDatalist.appendChild(option);
    });

    searchInput.addEventListener('input', () => {
        const playerName = searchInput.value;
        const playerVorp = allPlayers.find(p => p.player_display_name === playerName);
        const playerMatchup = allMatchups[playerName];
        
        if (playerVorp && playerMatchup) {
            renderPlayerDeepDive(playerVorp, playerMatchup, fullDataset);
        } else {
            document.getElementById('deep-dive-container').innerHTML = '';
        }
    });
}


function renderPlayerDeepDive(player, matchup, fullDataset) {
    // ... (this function is unchanged)
}
