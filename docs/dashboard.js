document.addEventListener('DOMContentLoaded', async () => {
    // --- GLOBAL DATA STORE ---
    let PROCESSED_DATA = [];
    let VORP_DATA = [];
    let CHART_INSTANCES = {}; // To store chart objects for updates

    // --- UTILITY FUNCTIONS ---
    const fetchData = async (url) => {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`Failed to fetch ${url}`);
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) return response.json();
        return response.text();
    };

    const parseCsv = (csvText) => new Promise(resolve => {
        Papa.parse(csvText, { header: true, dynamicTyping: true, skipEmptyLines: true, complete: (results) => resolve(results.data) });
    });

    // --- CHART CREATION FUNCTIONS ---

    // 1. Top 10 Players Chart
    const setupTop10Chart = () => {
        const ctx = document.getElementById('top-10-chart').getContext('2d');
        const filter = document.getElementById('top-10-pos-filter');

        const updateChart = () => {
            const latestSeason = Math.max(...PROCESSED_DATA.map(d => d.season));
            const latestWeek = Math.max(...PROCESSED_DATA.filter(d => d.season === latestSeason).map(d => d.week));
            
            const filteredData = PROCESSED_DATA
                .filter(d => d.season === latestSeason && d.week === latestWeek && d.position === filter.value)
                .sort((a, b) => b.fantasy_points - a.fantasy_points)
                .slice(0, 10);

            if (CHART_INSTANCES.top10) CHART_INSTANCES.top10.destroy();
            CHART_INSTANCES.top10 = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: filteredData.map(d => d.player_display_name),
                    datasets: [{
                        label: `Week ${latestWeek} Fantasy Points`,
                        data: filteredData.map(d => d.fantasy_points),
                        backgroundColor: 'rgba(35, 134, 54, 0.6)',
                        borderColor: 'rgba(35, 134, 54, 1)',
                        borderWidth: 1
                    }]
                },
                options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
            });
        };
        filter.addEventListener('change', updateChart);
        updateChart();
    };

    // 2. Team Points Share Chart
    const setupTeamShareChart = () => {
        const ctx = document.getElementById('team-share-chart').getContext('2d');
        const filter = document.getElementById('team-share-filter');

        const teams = [...new Set(PROCESSED_DATA.map(d => d.recent_team))].sort();
        teams.forEach(team => {
            const option = document.createElement('option');
            option.value = team;
            option.textContent = team;
            filter.appendChild(option);
        });

        const updateChart = () => {
            const teamData = PROCESSED_DATA.filter(d => d.recent_team === filter.value);
            const pointsByPos = teamData.reduce((acc, game) => {
                const pos = game.position;
                if (['QB', 'RB', 'WR', 'TE'].includes(pos)) {
                    acc[pos] = (acc[pos] || 0) + game.fantasy_points;
                }
                return acc;
            }, {});

            if (CHART_INSTANCES.teamShare) CHART_INSTANCES.teamShare.destroy();
            CHART_INSTANCES.teamShare = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: Object.keys(pointsByPos),
                    datasets: [{
                        data: Object.values(pointsByPos),
                        // CORRECTED: Higher contrast color palette
                        backgroundColor: ['#1c6b2b', '#238636', '#38a649', '#68d477'],
                        borderColor: '#161B22',
                        borderWidth: 3
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'top' } } }
            });
        };
        filter.addEventListener('change', updateChart);
        filter.value = teams[0];
        updateChart();
    };

    // 3. Consistency vs. Production Chart
    const setupConsistencyChart = () => {
        const ctx = document.getElementById('consistency-chart').getContext('2d');
        const filter = document.getElementById('consistency-pos-filter');

        const updateChart = () => {
            const pos = filter.value;
            const filteredData = (pos === 'ALL') ? VORP_DATA : VORP_DATA.filter(p => p.position === pos);

            if (CHART_INSTANCES.consistency) CHART_INSTANCES.consistency.destroy();
            CHART_INSTANCES.consistency = new Chart(ctx, {
                type: 'scatter',
                data: {
                    datasets: [{
                        label: `${pos} Players`,
                        data: filteredData.map(p => ({ x: p.ppg, y: p.consistency, player: p.player_display_name })),
                        backgroundColor: 'rgba(35, 134, 54, 0.6)'
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false, scales: { x: { title: { display: true, text: 'Production (PPG)' } }, y: { title: { display: true, text: 'Volatility (Std Dev)' } } }, plugins: { legend: { display: false } } }
            });
        };
        filter.addEventListener('change', updateChart);
        updateChart();
    };

    // 4. Player Trend Chart
    const setupPlayerTrendChart = () => {
        const ctx = document.getElementById('player-trend-chart').getContext('2d');
        const searchInput = document.getElementById('player-trend-search');

        const playerNames = [...new Set(VORP_DATA.map(p => p.player_display_name))].sort();
        const playerList = document.getElementById('player-list');
        playerNames.forEach(name => {
            const option = document.createElement('option');
            option.value = name;
            playerList.appendChild(option);
        });

        const updateChart = () => {
            const playerName = searchInput.value;
            const playerData = PROCESSED_DATA
                .filter(d => d.player_display_name === playerName)
                .sort((a, b) => (a.season * 100 + a.week) - (b.season * 100 + b.week))
                .slice(-8);

            if (CHART_INSTANCES.playerTrend) CHART_INSTANCES.playerTrend.destroy();
            if (playerData.length === 0 && playerName.trim() !== '') {
                 // You can optionally add a "no data" message here
                return;
            }

            CHART_INSTANCES.playerTrend = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: playerData.map(d => `S${d.season} W${d.week}`),
                    datasets: [{
                        label: `${playerName} Fantasy Points`,
                        data: playerData.map(d => d.fantasy_points),
                        borderColor: 'rgba(35, 134, 54, 1)',
                        tension: 0.1
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
            });
        };
        searchInput.addEventListener('change', updateChart);
    };

    // --- INITIALIZATION ---
    async function initialize() {
        try {
            const [processedCsv, vorp] = await Promise.all([
                fetchData('./data/processed/weekly_data_processed.csv'),
                fetchData('./data/reports/vorp_report.json')
            ]);
            
            PROCESSED_DATA = await parseCsv(processedCsv);
            VORP_DATA = vorp;
            
            setupTop10Chart();
            setupTeamShareChart();
            setupConsistencyChart();
            setupPlayerTrendChart();

            console.log("Dashboard initialized successfully.");
        } catch (error) {
            console.error("Dashboard initialization failed:", error);
            document.querySelector('.container').innerHTML = '<h1>Error</h1><p>Could not load necessary data files. Please ensure the workflow has run successfully.</p>';
        }
    }

    initialize();
});
