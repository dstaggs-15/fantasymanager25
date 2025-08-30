document.addEventListener('DOMContentLoaded', () => {
    const tableBody = document.getElementById('vorp-table-body');
    const headers = document.querySelectorAll('th[data-sort]');
    let playerData = [];
    let currentSort = {
        column: 'vorp',
        ascending: false 
    };

    async function fetchData() {
        try {
            // --- FIX: Removed '/docs' from the file path ---
            const response = await fetch('./data/reports/vorp_analyzer_report.json');
            if (!response.ok) {
                throw new Error(`Network response was not ok: ${response.statusText}`);
            }
            playerData = await response.json();
            renderTable();
        } catch (error) {
            console.error('Error fetching VORP data:', error);
            tableBody.innerHTML = `<tr><td colspan="6">Error loading player data.</td></tr>`;
        }
    }

    function sortData() {
        const { column, ascending } = currentSort;
        playerData.sort((a, b) => {
            let valA = a[column];
            let valB = b[column];

            if (valA == null) return 1;
            if (valB == null) return -1;

            if (typeof valA === 'string') {
                return ascending ? valA.localeCompare(valB) : valB.localeCompare(valA);
            } else {
                return ascending ? valA - valB : valB - valA;
            }
        });
    }

    function renderTable() {
        sortData();
        tableBody.innerHTML = ''; 
        
        playerData.forEach(player => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${player.player_name}</td>
                <td>${player.position}</td>
                <td>${player.team}</td>
                <td>${(player.ppg || 0).toFixed(2)}</td>
                <td>${(player.std_dev || 0).toFixed(2)}</td>
                <td>${(player.vorp || 0).toFixed(2)}</td>
            `;
            tableBody.appendChild(row);
        });

        headers.forEach(header => {
            header.classList.remove('sort-asc', 'sort-desc');
            if (header.dataset.sort === currentSort.column) {
                header.classList.add(currentSort.ascending ? 'sort-asc' : 'sort-desc');
            }
        });
    }

    headers.forEach(header => {
        header.addEventListener('click', () => {
            const sortColumn = header.dataset.sort;
            
            if (currentSort.column === sortColumn) {
                currentSort.ascending = !currentSort.ascending;
            } else {
                currentSort.column = sortColumn;
                currentSort.ascending = ['player_name', 'position', 'team'].includes(sortColumn);
            }
            renderTable();
        });
    });

    fetchData();
});
