async function loadData() {
    try {
        const response = await fetch('data/latest.json');
        const data = await response.json();

        document.getElementById('lastUpdated').innerText =
            `Last updated (UTC): ${data.last_updated}`;

        const tbody = document.querySelector('#standingsTable tbody');
        tbody.innerHTML = '';

        data.standings.forEach(team => {
            const row = `<tr>
                <td>${team.name}</td>
                <td>${team.wins}</td>
                <td>${team.losses}</td>
                <td>${team.points_for}</td>
                <td>${team.points_against}</td>
            </tr>`;
            tbody.innerHTML += row;
        });
    } catch (error) {
        document.getElementById('lastUpdated').innerText =
            'Error loading data';
        console.error(error);
    }
}

loadData();
