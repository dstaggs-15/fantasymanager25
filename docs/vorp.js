document.addEventListener('DOMContentLoaded', () => {
    const tableBody = document.getElementById('vorp-table-body');
    const headers = document.querySelectorAll('th[data-sort]');
    let playerData = [];
    let currentSort = {
        column: 'vorp',
        ascending: false // Default sort is VORP, descending
    };

    /**
     * Fetches player data from the JSON report.
     */
    async function fetchData() {
        try {
            const response = await fetch('./docs/data/reports/vorp_analyzer_report.json');
            if (!response.ok) {
                throw new Error(`Network response was not ok: ${response.statusText}`);
            }
            playerData = await response.json();
            renderTable(); // Initial render
        } catch (error) {
            console.error('Error fetching VORP data:', error);
            tableBody.innerHTML = `<tr><td colspan="6">Error loading player data.</td></tr>`;
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

            // Handle case where data might be missing
            if (valA == null) return 1;
            if (valB == null) return -1;

            // Handle numeric vs. string sorting
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
        // Sort the data before rendering
        sortData();
        
        // Clear existing table rows
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

        // Update header styles to show current sort indicator
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
                // If clicking the same column, just reverse the direction
                currentSort.ascending = !currentSort.ascending;
            } else {
                // If clicking a new column, set it as the sort column
                currentSort.column = sortColumn;
                // Default to descending for numeric stats, ascending for text
                currentSort.ascending = ['player_name', 'position', 'team'].includes(sortColumn);
            }
            // Re-render the table with the new sort order
            renderTable();
        });
    });

    // Initial data load when the page is ready
    fetchData();
});
