document.addEventListener('DOMContentLoaded', () => {
    // --- VORP Chart ---
    fetch('data/analysis/vorp_analysis.json')
        .then(response => response.json())
        .then(data => {
            renderVorpChart(data.players.slice(0, 20)); // Chart the top 20 players
        })
        .catch(error => console.error('Error loading VORP data:', error));

    // --- Matchup Chart ---
    fetch('data/analysis/matchup_report.json')
        .then(response => response.json())
        .then(data => {
            document.getElementById('matchup-title').textContent = `Matchup Ratings for Week ${data.week}`;
            renderMatchupChart(data.matchups);
        })
        .catch(error => {
            document.getElementById('matchup-title').textContent = 'Failed to load matchup report.';
            console.error('Error loading matchup data:', error)
        });
});

function renderVorpChart(players) {
    const ctx = document.getElementById('vorpChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: players.map(p => p.player_display_name),
            datasets: [{
                label: 'VORP Score',
                data: players.map(p => p.vorp),
                backgroundColor: 'rgba(97, 218, 251, 0.6)',
                borderColor: 'rgba(97, 218, 251, 1)',
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            scales: { x: { ticks: { color: '#e0e0e0' } }, y: { ticks: { color: '#e0e0e0' } } },
            plugins: { legend: { display: false } }
        }
    });
}

function renderMatchupChart(matchups) {
    const ratingToScore = { "Great": 5, "Good": 4, "Average": 3, "Bad": 2, "Very Bad": 1, "N/A": 0 };
    const ratingToColor = {
        "Great": "rgba(75, 192, 192, 0.6)",
        "Good": "rgba(54, 162, 235, 0.6)",
        "Average": "rgba(255, 206, 86, 0.6)",
        "Bad": "rgba(255, 159, 64, 0.6)",
        "Very Bad": "rgba(255, 99, 132, 0.6)",
        "N/A": "rgba(150, 150, 150, 0.6)"
    };

    const ctx = document.getElementById('matchupChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: matchups.map(m => m.player),
            datasets: [{
                label: 'Matchup Score',
                data: matchups.map(m => ratingToScore[m.rating]),
                backgroundColor: matchups.map(m => ratingToColor[m.rating])
            }]
        },
        options: {
            indexAxis: 'y',
            scales: {
                x: { 
                    ticks: { 
                        color: '#e0e0e0',
                        callback: function(value) {
                            const labels = {5: 'Great', 4: 'Good', 3: 'Average', 2: 'Bad', 1: 'Very Bad'};
                            return labels[value] || '';
                        }
                    } 
                }, 
                y: { ticks: { color: '#e0e0e0' } }
            },
            plugins: { legend: { display: false } }
        }
    });
}
