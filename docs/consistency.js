document.addEventListener('DOMContentLoaded', async () => {
    // --- DOM REFERENCES ---
    const tableBody = document.getElementById('consistency-table-body');
    const searchInput = document.getElementById('player-search');

    // --- GLOBAL DATA STORE ---
    let ALL_PLAYERS_DATA = [];

    // --- FUNCTION TO RENDER THE TABLE ---
    const renderTable = (players) => {
        tableBody.innerHTML = ''; // Clear existing rows

        if (players.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="9">No players found.</td></tr>';
            return;
        }

        const fragment = document.createDocumentFragment();
        players.forEach(player => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${player.player_display_name}</td>
                <td>${player.position}</td>
                <td>${player.recent_team}</td>
                <td>${player.ppg.toFixed(2)}</td>
                <td>${player.std_dev.toFixed(2)}</td>
                <td>${player.avg_ceiling.toFixed(2)}</td>
                <td>${player.avg_floor.toFixed(2)}</td>
                <td>${player.good_games_pct.toFixed(1)}%</td>
                <td>${player.bust_games_pct.toFixed(1)}%</td>
            `;
            fragment.appendChild(row);
        });
        tableBody.appendChild(fragment);
    };

    // --- INITIALIZATION AND DATA FETCHING ---
    async function initialize() {
        try {
            const response = await fetch('./data/reports/consistency_report.json');
            if (!response.ok) throw new Error('Failed to fetch consistency data');
            
            ALL_PLAYERS_DATA = await response.json();
            
            // Initial render of the full table
            renderTable(ALL_PLAYERS_DATA);

        } catch (error) {
            console.error("Initialization failed:", error);
            tableBody.innerHTML = `<tr><td colspan="9">Error loading data. Please ensure the workflow has run successfully.</td></tr>`;
        }
    }

    // --- EVENT LISTENER FOR SEARCH INPUT ---
    searchInput.addEventListener('keyup', () => {
        const searchTerm = searchInput.value.toLowerCase();
        
        if (!searchTerm) {
            renderTable(ALL_PLAYERS_DATA); // If search is empty, show all players
            return;
        }

        const filteredPlayers = ALL_PLAYERS_DATA.filter(player => 
            player.player_display_name.toLowerCase().includes(searchTerm)
        );
        
        renderTable(filteredPlayers);
    });

    initialize();
});
