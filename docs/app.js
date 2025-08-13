fetch('data/espn_mStandings.json')
  .then(response => response.json())
  .then(json => {
    const teams = json.standings.entries.map(entry => {
      return {
        teamName: entry.team.displayName,
        wins: entry.stats.find(s => s.name === 'wins').value,
        losses: entry.stats.find(s => s.name === 'losses').value,
        pointsFor: entry.stats.find(s => s.name === 'pointsFor').value,
        pointsAgainst: entry.stats.find(s => s.name === 'pointsAgainst').value
      };
    });

    renderStandingsTable(teams);
  });
