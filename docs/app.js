async function loadLeagueData() {
    try {
        const response = await fetch('data/latest.json');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const data = await response.json();
        const table = document.querySelector('table tbody');
        table.innerHTML = ''; // Clear old data

        data.forEach(team => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${team.team}</td>
                <td>${team.wins}</td>
                <td>${team.losses}</td>
                <td>${team.pointsFor}</td>
                <td>${team.pointsAgainst}</td>
            `;
            table.appendChild(row);
        });

        document.getElementById('lastUpdate').textContent = `Last updated: ${new Date().toUTCString()}`;

    } catch (error) {
        console.error('Error loading league data:', error);
        document.getElementById('lastUpdate').textContent = 'Error loading data';
    }
}

// Run on page load
document.addEventListener('DOMContentLoaded', loadLeagueData);
