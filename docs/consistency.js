document.addEventListener('DOMContentLoaded', () => {
    const tableBody = document.getElementById('consistency-table-body');
    const headers = document.querySelectorAll('th[data-sort]');
    let playerData = [];
    let currentSort = {
        column: 'ppg', // Default sort is PPG
        ascending: false // Default direction is descending
    };

    /**
     * Fetches player data from the JSON report.
     */
    async function fetchData() {
        try {
            const response = await fetch('./docs/data/reports/consistency_report.json');
            if (!response.ok) {
                throw new Error(`Network response was not ok: ${response.statusText}`);
            }
            playerData = await response.json();
            renderTable(); // Initial render
        } catch (error) {
            console.error('Error fetching consistency data:', error);
            tableBody.innerHTML = `<tr><td colspan="9">Error loading player data.</td></tr>`;
        }
    }

    /**
     * Sorts the global playerData array based on the currentSort state.
     */
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

    /**
     * Clears and re-renders the table with the current player data.
     */
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
                <td>${(player.ceiling || 0).toFixed(2)}</td>
                <td>${(player.floor || 0).toFixed(2)}</td>
                <td>${((player.good_pct || 0) * 100).toFixed(1)}%</td>
                <td>${((player.bust_pct || 0) * 100).toFixed(1)}%</td>
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

    // Add click event listeners to all sortable table headers
    headers.forEach(header => {
        header.addEventListener('click', () => {
            const sortColumn = header.dataset.sort;
            
            if (currentSort.column === sortColumn) {
                currentSort.ascending = !currentSort.ascending;
            } else {
                currentSort.column = sortColumn;
                // Default to descending for numeric stats, ascending for text
                const isTextColumn = ['player_name', 'position', 'team'].includes(sortColumn);
                // Std Dev is the only stat where lower is better, so default it to ascending
                const isLowerBetter = sortColumn === 'std_dev';
                currentSort.ascending = isTextColumn || isLowerBetter;
            }
            renderTable();
        });
    });

    // Initial data load
    fetchData();
});
