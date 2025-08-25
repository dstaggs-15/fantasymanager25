# analysis/player_points.py
# Builds canonical weekly + rolling-point feeds using league scoring.

from __future__ import annotations
from pathlib import Path
import json
import pandas as pd

from pipeline.utils import apply_scoring, load_scoring

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs" / "data" / "analysis"
SRC = DATA / "nfl_data.csv"

OUT_WEEKLY = DATA / "player_points_weekly.json"
OUT_L4     = DATA / "player_form_last4.json"
OUT_PLAYERS= DATA / "players.json"  # name/pos/team map for the UI

def _safe_str(x): return "" if pd.isna(x) else str(x)

def main():
    if not SRC.exists():
        raise FileNotFoundError(f"Missing {SRC}. Run pipeline/get_nfl_data.py first.")

    sc = load_scoring()

    # Expecting one row per player-game. If your CSV is different, we can tweak.
    df = pd.read_csv(SRC)

    # Best-effort canonical columns (edit here if your headers differ)
    colmap = {
        "player_id":  "player_id"  if "player_id" in df.columns else None,
        "player":     "player"     if "player" in df.columns else "player_name",
        "team":       "team"       if "team" in df.columns else "posteam",
        "opp":        "opp"        if "opp" in df.columns else "defteam",
        "pos":        "pos"        if "pos" in df.columns else "position",
        "week":       "week"       if "week" in df.columns else "game_week",
        "season":     "season"     if "season" in df.columns else "season"
    }
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
        bucket = f"{int(season)}-W{int(wk):02d}"
        entries = {}
        for _, r in g.iterrows():
            entries[str(r["player_id"])] = {
                "pos": _safe_str(r["pos"]).upper(),
                "team": _safe_str(r["team"]).upper(),
                "opp": _safe_str(r["opp"]).upper(),
                "points": round(float(r["fantasy_points"]), 2)
            }
        weekly[bucket] = entries

    # Rolling last-4 form: average fantasy points over last
