from .fetch_espn_standings import fetch_espn_standings
from .fetch_espn_matchups import fetch_espn_matchups
from .fetch_espn_rosters import fetch_espn_rosters
from .fetch_espn_teams import fetch_espn_teams
from .fetch_espn_settings import fetch_espn_settings

if __name__ == "__main__":
    LEAGUE_ID = 508419792
    SEASON = 2025

    print("Fetching ESPN standings...")
    fetch_espn_standings(LEAGUE_ID, SEASON)

    print("Fetching ESPN matchups...")
    fetch_espn_matchups(LEAGUE_ID, SEASON)

    print("Fetching ESPN rosters...")
    fetch_espn_rosters(LEAGUE_ID, SEASON)

    print("Fetching ESPN teams...")
    fetch_espn_teams(LEAGUE_ID, SEASON)

    print("Fetching ESPN settings...")
    fetch_espn_settings(LEAGUE_ID, SEASON)

    print("✅ All ESPN data fetched successfully!")
