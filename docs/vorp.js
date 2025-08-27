document.addEventListener('DOMContentLoaded', () => {
    // --- DOM ELEMENT REFERENCES ---
    const qbLevelInput = document.getElementById('qb-level');
    const rbLevelInput = document.getElementById('rb-level');
    const wrLevelInput = document.getElementById('wr-level');
    const teLevelInput = document.getElementById('te-level');
    const tableBody = document.getElementById('vorp-table-body');
    
    const player1Input = document.getElementById('player1-search');
    const player2Input = document.getElementById('player2-search');
    const compareBtn = document.getElementById('compare-btn');
    const comparisonResultsDiv = document.getElementById('comparison-results');
    const comparisonContainer = document.getElementById('comparison-results-container');
    const playerDatalist = document.getElementById('player-list');

    // --- GLOBAL VARIABLES ---
    let allPlayers = []; 
    let playersWithVorp = [];

    // --- FUNCTION TO POPULATE AUTOCOMPLETE ---
    const populateDatalist = () => {
        const fragment = document.createDocumentFragment();
        allPlayers.forEach(player => {
            const option = document.createElement('option');
            option.value = player.player_display_name;
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
        
        playersWithVorp = allPlayers.map(player => ({
            ...player,
            vorp: (player.ppg - (replacementScores[player.position] || 0)).toFixed(2),
        }));

        playersWithVorp.sort((a, b) => b.vorp - a.vorp);

        tableBody.innerHTML = '';
        playersWithVorp.forEach((player, index) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${index + 1}</td>
                <td>${player.player_display_name}</td>
                <td>${player.position}</td>
                <td>${player.recent_team}</td>
                <td>${player.ppg}</td>
                <td>${player.consistency}</td>
                <td><strong>${player.vorp}</strong></td>
            `;
            tableBody.appendChild(row);
        });
    };

    // --- FUNCTION TO HANDLE PLAYER COMPARISON ---
    const handleComparison = () => {
        const name1 = player1Input.value;
        const name2 = player2Input.value;

        if (!name1 && !name2) {
            comparisonContainer.style.display = 'none';
            return;
        }
        
        comparisonContainer.style.display = 'block';
        const player1 = playersWithVorp.find(p => p.player_display_name === name1);
        const player2 = playersWithVorp.find(p => p.player_display_name === name2);

        let resultsHTML = '';
        
        const renderPlayerCard = (player) => {
            if (!player) return `<div class="player-card"><p>Player not found.</p></div>`;
            return `
                <div class="player-card">
                    <h3>${player.player_display_name}</h3>
                    <p><strong>Team:</strong> ${player.recent_team} | <strong>Pos:</strong> ${player.position}</p>
                    <p><strong>PPG:</strong> ${player.ppg}</p>
                    <p><strong>VORP:</strong> ${player.vorp}</p>
                    <p><strong>Consistency (Std Dev):</strong> ${player.consistency}</p>
                    <p><strong>Games Played:</strong> ${player.games_played}</p>
                </div>
            `;
        };

        resultsHTML += renderPlayerCard(player1);
        resultsHTML += renderPlayerCard(player2);
        comparisonResultsDiv.innerHTML = resultsHTML;
    };

    // --- DATA FETCHING ---
    const fetchData = async () => {
        try {
            const response = await fetch('./data/reports/vorp_report.json');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            allPlayers = await response.json();
            
            populateDatalist();
            calculateAndRenderVorp();
            
        } catch (error) {
            console.error('Error fetching VORP data:', error);
            tableBody.innerHTML = `<tr><td colspan="7">Could not load VORP report. Check if the file exists and the workflow ran correctly.</td></tr>`;
        }
    };

    // --- EVENT LISTENERS ---
    [qbLevelInput, rbLevelInput, wrLevelInput, teLevelInput].forEach(input => {
        input.addEventListener('change', calculateAndRenderVorp);
    });
    compareBtn.addEventListener('click', handleComparison);

    // --- INITIALIZATION ---
    fetchData();
});
