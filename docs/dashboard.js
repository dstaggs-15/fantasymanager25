document.addEventListener('DOMContentLoaded', async () => {
    
    try {
        // Load all data files needed for the dashboard
        const [vorpRes, consistencyRes] = await Promise.all([
            fetch('data/analysis/vorp_analysis.json'),
            fetch('data/analysis/consistency_report.json')
        ]);

        if (!vorpRes.ok || !consistencyRes.ok) throw new Error('Failed to load one or more data files.');

        const vorpData = await vorpRes.json();
        const consistencyData = await consistencyRes.json();
        
        // Render all components
        renderVorpChart(vorpData.players.slice(0, 20));
        renderConsistencyChart(consistencyData.players, 'RB');
        generateConsensus(vorpData.players, consistencyData.players);

    } catch(error) {
        console.error("Dashboard failed to load:", error);
        document.getElementById('consensus-list').innerHTML = `<li>Failed to load dashboard data.</li>`;
    }
});

function generateConsensus(vorp, consistency) {
    const consensusList = document.getElementById('consensus-list');
    let consensusHTML = '';

    // Find the most valuable player overall
    const topVorpPlayer = vorp[0];
    consensusHTML += `<li><strong>Top Overall Value:</strong> ${topVorpPlayer.player_display_name} (${topVorpPlayer.position}) stands out as the most valuable player according to VORP.</li>`;

    // Find the most consistent RB
    const topConsistentRB = consistency
        .filter(p => p.position === 'RB' && p.games_played > 8)
        .sort((a,b) => b.consistency_pct - a.consistency_pct)[0];
    consensusHTML += `<li><strong>Safest RB Floor:</strong> ${topConsistentRB.player_display_name} is the most consistent RB, scoring above a baseline in ${topConsistentRB.consistency_pct}% of his games.</li>`;

    // Find a boom/bust WR
    const boomBustWR = consistency
        .filter(p => p.position === 'WR' && p.games_played > 8)
        .sort((a,b) => b.std_dev_ppg - a.std_dev_ppg)[0];
    consensusHTML += `<li><strong>Boom/Bust Candidate:</strong> ${boomBustWR.player_display_name} (WR) shows the highest volatility, making him a high-risk, high-reward weekly play.</li>`;

    consensusList.innerHTML = consensusHTML;
}

function renderVorpChart(players) {
    const ctx = document.getElementById('vorpChart').getContext('2d');
    // Chart rendering logic (same as before)
    new Chart(ctx, { type: 'bar', data: { labels: players.map(p => p.player_display_name), datasets: [{ label: 'VORP Score', data: players.map(p => p.vorp), backgroundColor: 'rgba(3, 218, 198, 0.6)' }] }, options: { indexAxis: 'y', scales: { x: { ticks: { color: '#e0e0e0' } }, y: { ticks: { color: '#e0e0e0' } } }, plugins: { legend: { display: false } } } });
}

function renderConsistencyChart(players, position) {
    const filteredPlayers = players.filter(p => p.position === position && p.games_played > 8);
    const ctx = document.getElementById('consistencyChart').getContext('2d');
    new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: `${position} Consistency`,
                data: filteredPlayers.map(p => ({ x: p.consistency_pct, y: p.mean_ppg, player: p.player_display_name })),
                backgroundColor: 'rgba(3, 218, 198, 0.7)'
            }]
        },
        options: {
            scales: {
                x: { type: 'linear', position: 'bottom', title: { display: true, text: 'Consistency %', color: '#e0e0e0'}, ticks: { color: '#e0e0e0'} },
                y: { title: { display: true, text: 'Mean PPG', color: '#e0e0e0'}, ticks: { color: '#e0e0e0'} }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const player = context.raw.player;
                            return `${player}: ${context.raw.x.toFixed(1)}% consistent, ${context.raw.y.toFixed(1)} PPG`;
                        }
                    }
                }
            }
        }
    });
}
