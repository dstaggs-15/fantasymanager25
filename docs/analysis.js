document.addEventListener('DOMContentLoaded', () => {
    const dataTable = document.getElementById('data-table');
    const statusEl = document.getElementById('status');
    // THE FIX: Corrected path to the data file
    const dataUrl = 'data/analysis/nfl_data_with_weather.csv';

    statusEl.textContent = `Fetching data from ${dataUrl}...`;

    Papa.parse(dataUrl, {
        download: true,
        header: true,
        dynamicTyping: true,
        skipEmptyLines: true,
        complete: function(results) {
            if (results.data && results.data.length > 0) {
                statusEl.textContent = `Successfully loaded ${results.data.length} rows of data.`;
                renderTable(results.data, results.meta.fields);
            } else {
                statusEl.textContent = 'Error: No data found or file is empty.';
                console.error(results.errors);
            }
        },
        error: function(err) {
            statusEl.textContent = `Error loading data file: ${err.message}`;
        }
    });

    function renderTable(data, headers) {
        const thead = dataTable.querySelector('thead');
        const tbody = dataTable.querySelector('tbody');
        thead.innerHTML = '';
        tbody.innerHTML = '';
        const headerRow = document.createElement('tr');
        headers.forEach(header => {
            const th = document.createElement('th');
            th.textContent = header;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        data.forEach(row => {
            const tr = document.createElement('tr');
            headers.forEach(header => {
                const td = document.createElement('td');
                td.textContent = row[header] === null ? 'N/A' : row[header];
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
    }
});
