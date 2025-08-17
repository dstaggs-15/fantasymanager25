#!/usr/bin/env python3
import argparse, os, sys, json
from util import auth_headers, fetch_json, write_json

BASE = "https://fantasy.espn.com/apis/v3/games/ffl/seasons/{season}/segments/0/leagues/{league}?view=mRoster"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--league", required=True)
    ap.add_argument("--season", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    swid = os.getenv("SWID")
    s2 = os.getenv("ESPN_S2")
    if not swid or not s2:
        print("SWID/ESPN_S2 missing from env", file=sys.stderr)
        sys.exit(2)

    hdrs = auth_headers(swid, s2)
    url = BASE.format(season=args.season, league=args.league)
    data = fetch_json(url, headers=hdrs)
    write_json(args.out, data)
    print(f"Wrote {args.out} ✔")

if __name__ == "__main__":
    main()
