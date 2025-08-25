document.addEventListener('DOMContentLoaded', () => {
    // --- DOM ELEMENT REFERENCES ---
    const qbLevelInput = document.getElementById('qb-level');
    const rbLevelInput = document.getElementById('rb-level');
    const wrLevelInput = document.getElementById('wr-level');
    const teLevelInput = document.getElementById('te-level');
    const tableBody = document.getElementById('vorp-table-body');
    
    // --- NEW DOM REFERENCES FOR COMPARISON TOOL ---
    const player1Input = document.getElementById('player1-search');
    const player2Input = document.getElementById('player2-search');
    const compareBtn = document.getElementById('compare-btn');
    const comparisonResultsDiv = document.getElementById('comparison-results');
    const playerDatalist = document.getElementById('player-list');

    // --- GLOBAL VARIABLES ---
    let allPlayers = []; // Raw data from JSON
    let playersWithVorp = []; // Data after VORP calculation

    // --- NEW: FUNCTION TO POPULATE AUTOCOMPLETE ---
    const populateDatalist = () => {
        const fragment = document.createDocumentFragment();
        allPlayers.forEach(player => {
            const option = document.createElement('option');
            option.value = player.player_name;
            fragment.appendChild(option);
        });
        playerDatalist.appendChild(fragment);
    };

    // --- FUNCTION TO CALCULATE AND RENDER VORP ---
    const calculateAndRenderVorp = () => {
        if (allPlayers.length === 0) return;

        const levels = {
            QB: parseInt(qbLevelInput.value) || 0,
            RB: parseInt(rbLevelInput.value) || 0,
            WR: parseInt(wrLevelInput.value) || 0,
            TE: parseInt(teLevelInput.value) || 0,
        };

        const replacementScores = {};
        for (const pos in levels) {
            const posPlayers = allPlayers.filter(p => p.position === pos).sort((a, b) => b.ppg - a.ppg);
            const replacementIndex = levels[pos] - 1;
            replacementScores[pos] = (replacementIndex >= 0 && replacementIndex < posPlayers.length) ? posPlayers[replacementIndex].ppg : 0;
        }
        
        // Calculate VORP and store it in our global variable
        playersWithVorp = allPlayers.map(player => ({
            ...player,
            vorp: (player.ppg - (replacementScores[player.position] || 0)).toFixed(2),
        }));

        playersWithVorp.sort((a, b) => b.vorp - a.vorp);

        // Render the main table
        tableBody.innerHTML = '';
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

    // --- NEW: FUNCTION TO HANDLE PLAYER COMPARISON ---
    const handleComparison = () => {
        const name1 = player1Input.value;
        const name2 = player2Input.value;

        if (!name1 || !name2) {
            comparisonResultsDiv.innerHTML = `<p>Please select two players to compare.</p>`;
            return;
        }

        const player1 = playersWithVorp.find(p => p.player_name === name1);
        const player2 = playersWithVorp.find(p => p.player_name === name2);

        let resultsHTML = '';
        
        if (player1) {
            resultsHTML += `
                <div class="player-card">
                    <h3>${player1.player_name}</h3>
                    <p><strong>Team:</strong> ${player1.team}</p>
                    <p><strong>Position:</strong> ${player1.position}</p>
                    <p><strong>PPG:</strong> ${player1.ppg}</p>
                    <p><strong>VORP:</strong> ${player1.vorp}</p>
                </div>
            `;
        } else {
            resultsHTML += `<div class="player-card"><p>Could not find player: ${name1}</p></div>`;
        }

        if (player2) {
            resultsHTML += `
                <div class="player-card">
                    <h3>${player2.player_name}</h3>
                    <p><strong>Team:</strong> ${player2.team}</p>
                    <p><strong>Position:</strong> ${player2.position}</p>
                    <p><strong>PPG:</strong> ${player2.ppg}</p>
                    <p><strong>VORP:</strong> ${player2.vorp}</p>
                </div>
            `;
        } else {
            resultsHTML += `<div class="player-card"><p>Could not find player: ${name2}</p></div>`;
        }

        comparisonResultsDiv.innerHTML = resultsHTML;
    };

    // --- DATA FETCHING ---
    const fetchData = async () => {
        try {
            const response = await fetch('./data/analysis/player_ppg.json');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            allPlayers = await response.json();
            
            populateDatalist(); // Populate the autocomplete options
            calculateAndRenderVorp(); // Initial calculation and render
            
        } catch (error) {
            console.error('Error fetching player data:', error);
            tableBody.innerHTML = `<tr><td colspan="6">Could not load player data. Make sure you have run the analysis/vorp_calculator.py script.</td></tr>`;
        }
    };

    // --- EVENT LISTENERS ---
    qbLevelInput.addEventListener('change', calculateAndRenderVorp);
    rbLevelInput.addEventListener('change', calculateAndRenderVorp);
    wrLevelInput.addEventListener('change', calculateAndRenderVorp);
    teLevelInput.addEventListener('change', calculateAndRenderVorp);
    compareBtn.addEventListener('click', handleComparison); // Add listener for the compare button

    // --- INITIALIZATION ---
    fetchData();
});
