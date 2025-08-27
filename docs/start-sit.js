document.addEventListener('DOMContentLoaded', async () => {
    // --- DOM REFERENCES ---
    const playerInputs = [
        document.getElementById('player1'),
        document.getElementById('player2'),
        document.getElementById('player3'),
        document.getElementById('player4'),
    ];
    const compareBtn = document.getElementById('compare-btn');
    const resultsContainer = document.getElementById('results-container');
    const playerDatalist = document.getElementById('player-list');
    const weekTitle = document.getElementById('week-title');

    // --- GLOBAL DATA STORE ---
    let VORP_DATA = [];
    let MATCHUP_DATA = {};
    let SCHEDULE_DATA = [];

    // --- DATA FETCHING ---
    async function fetchData(url) {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`Failed to fetch ${url}`);
        // Check content type to decide how to parse
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.indexOf("application/json") !== -1) {
            return response.json();
        }
        return response.text();
    }
    
    // Using PapaParse to handle CSV in the browser. Add this to your main HTML if not already there.
    // We'll add a script tag to the HTML to load this library from a CDN.
    function parseCsv(csvText) {
        return new Promise(resolve => {
            Papa.parse(csvText, {
                header: true,
                skipEmptyLines: true,
                complete: (results) => resolve(results.data),
            });
        });
    }

    // --- INITIALIZATION ---
    async function initialize() {
        try {
            // Fetch all data sources in parallel
            const [vorp, matchups, scheduleCsv] = await Promise.all([
                fetchData('./data/reports/vorp_report.json'),
                fetchData('./data/reports/matchup_report.json'),
                fetchData('./data/raw/schedule_raw.csv')
            ]);
            
            VORP_DATA = vorp;
            MATCHUP_DATA = matchups;
            SCHEDULE_DATA = await parseCsv(scheduleCsv);

            // Populate autocomplete
            const fragment = document.createDocumentFragment();
            VORP_DATA.forEach(player => {
                const option = document.createElement('option');
                option.value = player.player_display_name;
                fragment.appendChild(option);
            });
            playerDatalist.appendChild(fragment);

            console.log("All data loaded and ready.");

        } catch (error) {
            console.error("Initialization failed:", error);
            resultsContainer.innerHTML = `<p>Error loading essential data. The tool may not work correctly.</p>`;
        }
    }

    // --- CORE LOGIC ---
    function analyzeMatchups() {
        resultsContainer.innerHTML = ''; // Clear previous results

        const selectedPlayerNames = playerInputs
            .map(input => input.value)
            .filter(name => name.trim() !== '');

        if (selectedPlayerNames.length === 0) return;

        // Find the current/upcoming week
        const latestSeason = Math.max(...SCHEDULE_DATA.map(g => parseInt(g.season)));
        const gamesPlayed = SCHEDULE_DATA.filter(g => g.result !== null && g.season == latestSeason);
        const currentWeek = gamesPlayed.length > 0 ? Math.max(...gamesPlayed.map(g => parseInt(g.week))) + 1 : 1;
        weekTitle.textContent = `Comparing Players for Week ${currentWeek}`;

        selectedPlayerNames.forEach(playerName => {
            const playerData = VORP_DATA.find(p => p.player_display_name === playerName);
            if (!playerData) {
                renderCard({ name: playerName, error: "Player not found in VORP data." });
                return;
            }

            const playerTeam = playerData.recent_team;
            const upcomingGame = SCHEDULE_DATA.find(g => 
                g.season == latestSeason && 
                g.week == currentWeek && 
                (g.home_team === playerTeam || g.away_team === playerTeam)
            );

            if (!upcomingGame) {
                renderCard({ name: playerName, ppg: playerData.ppg, opponent: "BYE" });
                return;
            }

            const opponent = upcomingGame.home_team === playerTeam ? upcomingGame.away_team : upcomingGame.home_team;
            const matchup = MATCHUP_DATA[playerData.position]?.find(m => m.team === opponent);

            renderCard({
                name: playerName,
                ppg: playerData.ppg,
                team: playerTeam,
                opponent: opponent,
                matchupRank: matchup?.rank,
                pointsAllowed: matchup?.points_allowed
            });
        });
    }

    // --- RENDERING ---
    function renderCard(data) {
        const card = document.createElement('div');
        card.className = 'player-card';

        if (data.error) {
            card.innerHTML = `<h3>${data.name}</h3><p class="matchup-bad">${data.error}</p>`;
            resultsContainer.appendChild(card);
            return;
        }
        
        let matchupHTML = '<p><strong>Matchup:</strong> vs. ' + data.opponent + '</p>';
        if (data.opponent === 'BYE') {
            matchupHTML = `<p class="matchup-avg"><strong>On Bye Week</strong></p>`;
        } else if (data.matchupRank) {
            let rankClass = 'matchup-avg';
            if (data.matchupRank <= 10) rankClass = 'matchup-good'; // Top 10 easiest
            if (data.matchupRank >= 23) rankClass = 'matchup-bad'; // Bottom 10 hardest

            matchupHTML += `<p><strong>Defensive Rank:</strong> 
                <span class="matchup-rank ${rankClass}">
                    ${data.matchupRank} / 32
                </span>
            </p>`;
        } else {
            matchupHTML += `<p>Matchup data not available.</p>`;
        }

        card.innerHTML = `
            <h3>${data.name}</h3>
            <p><strong>Team:</strong> ${data.team}</p>
            <p><strong>PPG:</strong> ${data.ppg}</p>
            <hr style="border-color: var(--color-border); margin: 1rem 0;">
            ${matchupHTML}
        `;
        resultsContainer.appendChild(card);
    }

    // Add PapaParse script to the page
    const papaScript = document.createElement('script');
    papaScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/PapaParse/5.3.2/papaparse.min.js';
    papaScript.onload = initialize; // Initialize everything after the library is loaded
    document.head.appendChild(papaScript);

    compareBtn.addEventListener('click', analyzeMatchups);
});
