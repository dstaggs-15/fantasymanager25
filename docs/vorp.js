// docs/vorp.js

document.addEventListener('DOMContentLoaded', () => {
    // --- DOM ELEMENT REFERENCES ---
    const qbLevelInput = document.getElementById('qb-level');
    const rbLevelInput = document.getElementById('rb-level');
    const wrLevelInput = document.getElementById('wr-level');
    const teLevelInput = document.getElementById('te-level');
    const tableBody = document.getElementById('vorp-table-body');
    
    // This will store our player data once fetched
    let allPlayers = [];

    // --- FUNCTION TO CALCULATE AND RENDER VORP ---
    const calculateAndRenderVorp = () => {
        if (allPlayers.length === 0) return; // Don't run if data isn't loaded yet

        // 1. Get the current replacement levels from the input boxes
        const levels = {
            QB: parseInt(qbLevelInput.value) || 0,
            RB: parseInt(rbLevelInput.value) || 0,
            WR: parseInt(wrLevelInput.value) || 0,
            TE: parseInt(teLevelInput.value) || 0,
        };

        // 2. Find the replacement PPG score for each position
        const replacementScores = {};
        for (const pos in levels) {
            // Filter players for the current position and sort them by PPG
            const posPlayers = allPlayers.filter(p => p.position === pos).sort((a, b) => b.ppg - a.ppg);
            
            // Find the replacement player at the specified rank (e.g., the 11th QB)
            const replacementIndex = levels[pos] - 1;
            if (replacementIndex >= 0 && replacementIndex < posPlayers.length) {
                replacementScores[pos] = posPlayers[replacementIndex].ppg;
            } else {
                replacementScores[pos] = 0; // Default to 0 if not enough players
            }
        }
        
        // 3. Calculate VORP for every player
        const playersWithVorp = allPlayers.map(player => {
            const replacementPpg = replacementScores[player.position] || 0;
            const vorp = player.ppg - replacementPpg;
            return {
                ...player,
                vorp: vorp.toFixed(2), // Keep 2 decimal places
            };
        });

        // 4. Sort all players by their new VORP score
        playersWithVorp.sort((a, b) => b.vorp - a.vorp);

        // 5. Render the data into the HTML table
        tableBody.innerHTML = ''; // Clear the existing table rows
        playersWithVorp.forEach((player, index) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${index + 1}</td>
                <td>${player.player_name}</td>
                <td>${player.team}</td>
                <td>${player.position}</td>
                <td>${player.ppg}</td>
                <td><strong>${player.vorp}</strong></td>
            `;
            tableBody.appendChild(row);
        });
    };

    // --- DATA FETCHING ---
    const fetchData = async () => {
        try {
            // The path is relative to the HTML file
            const response = await fetch('./data/analysis/player_ppg.json');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            allPlayers = await response.json();
            console.log('Player PPG data loaded successfully.');
            // Initial calculation and render
            calculateAndRenderVorp();
        } catch (error) {
            console.error('Error fetching player data:', error);
            tableBody.innerHTML = `<tr><td colspan="6">Could not load player data. Make sure you have run the analysis/vorp_calculator.py script.</td></tr>`;
        }
    };

    // --- EVENT LISTENERS ---
    // Add listeners to all input boxes to recalculate when their values change
    qbLevelInput.addEventListener('change', calculateAndRenderVorp);
    rbLevelInput.addEventListener('change', calculateAndRenderVorp);
    wrLevelInput.addEventListener('change', calculateAndRenderVorp);
    teLevelInput.addEventListener('change', calculateAndRenderVorp);

    // --- INITIALIZATION ---
    fetchData();
});
