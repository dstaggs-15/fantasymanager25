# analysis/player_points.py
# Builds canonical weekly + rolling-point feeds using league scoring.

from __future__ import annotations
from pathlib import Path
import json
import pandas as pd
import sys

# --- ensure we can import pipeline.utils no matter how this is invoked ---
ROOT = Path(__file__).resolve().parents[1]  # repo root
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.utils import apply_scoring, load_scoring  # noqa: E402

DATA = ROOT / "docs" / "data" / "analysis"
SRC = DATA / "nfl_data.csv"

OUT_WEEKLY = DATA / "player_points_weekly.json"
OUT_L4     = DATA / "player_form_last4.json"
OUT_PLAYERS= DATA / "players.json"  # name/pos/team map for the UI

def _safe_str(x): 
    return "" if pd.isna(x) else str(x)

def main():
    if not SRC.exists():
        raise FileNotFoundError(f"Missing {SRC}. Run pipeline/get_nfl_data.py first.")

    sc = load_scoring()

    # Expecting one row per player-game. If your CSV is different, we can tweak.
    df = pd.read_csv(SRC)

    # Best-effort canonical columns (edit here if your headers differ)
    colmap = {
        "player_id":  "player_id"  if "player_id" in df.columns else None,
        "player":     "player"     if "player" in df.columns else ("player_name" if "player_name" in df.columns else None),
        "team":       "team"       if "team" in df.columns else ("posteam" if "posteam" in df.columns else None),
        "opp":        "opp"        if "opp" in df.columns else ("defteam" if "defteam" in df.columns else None),
        "pos":        "pos"        if "pos" in df.columns else ("position" if "position" in df.columns else None),
        "week":       "week"       if "week" in df.columns else ("game_week" if "game_week" in df.columns else None),
        "season":     "season"     if "season" in df.columns else ("season" if "season" in df.columns else None)
    }
    # Create or copy columns
    for want, have in list(colmap.items()):
        if have is None or have not in df.columns:
            df[want] = ""
        elif want != have:
            df[want] = df[have]

    # Apply league scoring (adds 'fantasy_points')
    df = apply_scoring(df, position_col="pos", scoring=sc)

    # Build players map {player_id: {name, pos, team}}
    # If no stable id, synthesize one from name+team to keep UI working.
    if "player_id" not in df or df["player_id"].eq("").all():
        df["player_id"] = (
            df["player"].fillna("") + "|" + df["team"].fillna("") + "|" + df["pos"].fillna("")
        )

    players = {}
    for _, r in df[["player_id","player","pos","team"]].drop_duplicates().iterrows():
        players[str(r["player_id"])] = {
            "name": _safe_str(r["player"]),
            "pos":  _safe_str(r["pos"]).upper(),
            "team": _safe_str(r["team"]).upper()
        }

    # Weekly table: { "<season>-W<week>": { player_id: {pos,team,opp,points} } }
    weekly = {}
    for (season, wk), g in df.groupby(["season","week"]):
        try:
            bucket = f"{int(float(season))}-W{int(float(wk)):02d}"
        except Exception:
            bucket = f"{season}-W{wk}"
        entries = {}
        for _, r in g.iterrows():
            entries[str(r["player_id"])] = {
                "pos": _safe_str(r["pos"]).upper(),
                "team": _safe_str(r["team"]).upper(),
                "opp": _safe_str(r["opp"]).upper(),
                "points": round(float(r["fantasy_points"]), 2)
            }
        weekly[bucket] = entries

    # Rolling last-4 form: average fantasy points over last 4 weeks (per season)
    df_sorted = df.sort_values(["player_id","season","week"])
    df_sorted["fp_l4"] = (
        df_sorted
        .groupby(["player_id","season"])["fantasy_points"]
        .rolling(4, min_periods=1).mean()
        .reset_index(level=[0,1], drop=True)
    )
    l4 = {}
    for (season, wk), g in df_sorted.groupby(["season","week"]):
        try:
            bucket = f"{int(float(season))}-W{int(float(wk)):02d}"
        except Exception:
            bucket = f"{season}-W{wk}"
        l4[bucket] = {
            str(r["player_id"]): round(float(r["fp_l4"]), 2)
            for _, r in g.iterrows()
        }

    DATA.mkdir(parents=True, exist_ok=True)
    with open(OUT_WEEKLY, "w") as f: json.dump(weekly, f)
    with open(OUT_L4, "w") as f: json.dump(l4, f)
    with open(OUT_PLAYERS, "w") as f: json.dump(players, f)

    print(f"Wrote {OUT_WEEKLY}, {OUT_L4}, {OUT_PLAYERS}")

if __name__ == "__main__":
    main()
