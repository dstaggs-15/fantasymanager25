#!/usr/bin/env python3
import argparse, os, sys, math
from util import auth_headers, fetch_json, write_json

# ESPN caps players page size; we page through a few chunks for summary
PLAYERS_URL = "https://fantasy.espn.com/apis/v3/games/ffl/seasons/{season}/players?scoringPeriodId=0&view=players_wl&view=players_sort_eligible"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    swid = os.getenv("SWID")
    s2 = os.getenv("ESPN_S2")
    if not swid or not s2:
        print("SWID/ESPN_S2 missing from env", file=sys.stderr)
        sys.exit(2)

    hdrs = auth_headers(swid, s2)
    # First call for total count
    base = PLAYERS_URL.format(season=args.season) + "&limit=50&offset=0"
    first = fetch_json(base, headers=hdrs)
    items = first if isinstance(first, list) else []
    # Page through a few pages (enough for your UI; adjust if you want full universe)
    for offset in [50, 100, 150, 200, 250, 300]:
        try:
            page = fetch_json(
                PLAYERS_URL.format(season=args.season) + f"&limit=50&offset={offset}",
                headers=hdrs
            )
            if not page: break
            items.extend(page)
        except Exception:
            break

    # Light summary
    summary = []
    for p in items:
        try:
            summary.append({
                "id": p.get("id"),
                "fullName": p.get("fullName"),
                "proTeamId": p.get("proTeamId"),
                "defaultPositionId": p.get("defaultPositionId"),
                "ownership": p.get("ownership", {}),
                "stats": p.get("stats", [])[:2],  # keep small
                "status": p.get("status"),
            })
        except Exception:
            continue

    write_json(args.out, summary)
    print(f"Wrote {args.out} ({len(summary)} players) ✔")

if __name__ == "__main__":
    main()
