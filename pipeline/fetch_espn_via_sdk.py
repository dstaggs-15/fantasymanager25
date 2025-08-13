#!/usr/bin/env python3
"""
Fetch standings using the espn-api library and write a FLAT file
that the UI can read immediately even if the raw ESPN JSON calls 403.

Output:
  docs/data/espn_mStandings.json   (FLAT: [{teamName,wins,losses,pointsFor,pointsAgainst}])
  docs/data/status.json
  docs/data/espn_manifest.json     (append note about sdk output)
"""
from __future__ import annotations
import os, json, pathlib, datetime

DATA = pathlib.Path(__file__).resolve().parents[1] / "docs" / "data"
DATA.mkdir(parents=True, exist_ok=True)

def utcnow():
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")

def main():
    league_id = os.getenv("LEAGUE_ID")
    season = int(os.getenv("SEASON", "2025"))
    swid = os.getenv("ESPN_SWID")  # optional
    s2 = os.getenv("ESPN_S2")      # optional

    if not league_id:
        write_json(DATA / "status.json", {
            "generated_utc": utcnow(),
            "season": str(season),
            "week": None,
            "notes": "LEAGUE_ID missing; SDK fetch skipped"
        })
        return

    try:
        from espn_api.football import League
        if swid and s2:
            league = League(league_id=int(league_id), year=season, swid=swid, espn_s2=s2)
        else:
            # Public leagues usually work without cookies via the SDK
            league = League(league_id=int(league_id), year=season)

        rows = []
        for t in league.teams:
            rows.append({
                "teamName": t.team_name,
                "wins": int(t.wins),
                "losses": int(t.losses),
                "pointsFor": round(float(t.points_for), 0),
                "pointsAgainst": round(float(t.points_against), 0),
            })

        # sort by wins desc then pointsFor desc
        rows.sort(key=lambda r: (r["wins"], r["pointsFor"]), reverse=True)

        # Write the file using the same filename the UI expects
        write_json(DATA / "espn_mStandings.json", rows)

        # Update status + manifest
        status = {
            "generated_utc": utcnow(),
            "season": str(season),
            "week": None,
            "notes": "ESPN SDK standings OK",
        }
        write_json(DATA / "status.json", status)

        # Append/merge to manifest
        manifest_path = DATA / "espn_manifest.json"
        manifest = {}
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                manifest = {}
        manifest.setdefault("league_id", str(league_id))
        manifest.setdefault("season", str(season))
        manifest["generated_utc"] = utcnow()
        manifest.setdefault("files", [])
        if "espn_mStandings.json" not in manifest["files"]:
            manifest["files"].append("espn_mStandings.json")
        manifest.setdefault("notes", []).append("sdk: standings written")
        write_json(manifest_path, manifest)

        print("✅ SDK standings written to docs/data/espn_mStandings.json")
    except Exception as e:
        # last-resort error marker
        write_json(DATA / "status.json", {
            "generated_utc": utcnow(),
            "season": str(season),
            "week": None,
            "notes": f"SDK fetch failed: {type(e).__name__}: {e}",
        })
        raise

if __name__ == "__main__":
    main()
