# pipeline/utils.py
# Single source of truth for league scoring + helpers used by all analyzers.

from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, Optional, Iterable

import pandas as pd


# -------- Paths --------
ROOT = Path(__file__).resolve().parents[1]   # repo root (…/fantasymanager25)
DATA = ROOT / "docs" / "data" / "analysis"
SCORING_JSON = DATA / "scoring.json"


# -------- Scoring loader --------
def load_scoring(path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load scoring rules from docs/data/analysis/scoring.json
    """
    p = path or SCORING_JSON
    if not p.exists():
        raise FileNotFoundError(
            f"Scoring file not found at {p}. "
            "Create docs/data/analysis/scoring.json first."
        )
    with open(p, "r") as f:
        return json.load(f)


# -------- Safe getters for many possible column names --------
def _g(row: pd.Series, names: Iterable[str], default: float = 0.0) -> float:
    for n in names:
        if n in row and pd.notna(row[n]):
            try:
                return float(row[n])
            except Exception:
                pass
    return default


# Common stat aliases (cover nfl-data-py / nflfastR style names)
ALIAS = {
    # Passing
    "pass_yds": ["passing_yards", "pass_yards", "py", "pass_yds"],
    "pass_tds": ["passing_tds", "pass_tds", "passing_touchdowns"],
    "pass_int": ["interceptions", "interceptions_thrown", "pass_interceptions"],
    "two_pt_pass": ["two_point_pass", "pass_2pt", "two_pt_pass", "passing_2pt_conversions"],

    # Rushing
    "rush_yds": ["rushing_yards", "rush_yards", "ry", "rush_yds"],
    "rush_tds": ["rushing_tds", "rush_tds", "rushing_touchdowns"],
    "two_pt_rush": ["two_point_rush", "rush_2pt", "two_pt_rush", "rushing_2pt_conversions"],
    "rush_fd": ["rushing_first_downs", "rush_first_downs", "first_down_rush"],

    # Receiving
    "rec": ["receptions", "rec", "recs"],
    "rec_yds": ["receiving_yards", "rec_yards", "rey", "rec_yds"],
    "rec_tds": ["receiving_tds", "rec_tds", "receiving_touchdowns"],
    "two_pt_rec": ["two_point_receive", "rec_2pt", "two_pt_rec", "receiving_2pt_conversions"],
    "rec_fd": ["receiving_first_downs", "rec_first_downs", "first_down_rec", "first_down_receiving"],

    # Turnovers
    "fumbles_lost": ["fumbles_lost", "fumlost", "fumbles_lost_offense"],

    # Returns (player-level)
    "kr_td": ["kick_return_tds", "kret_td", "kick_return_td"],
    "pr_td": ["punt_return_tds", "pret_td", "punt_return_td"],
    "int_ret_td": ["int_return_td", "interception_return_td"],
    "fum_ret_td": ["fumble_return_td"],
    "blk_kick_ret_td": ["blocked_kick_return_td", "blocked_punt_fg_return_td"],
    "two_pt_ret": ["two_pt_return", "def_two_pt_return"],  # rare player stat
    "one_pt_safety": ["one_pt_safety", "one_point_safety"],

    # Kicking
    "pat_made": ["pat_made", "xp_made", "extra_points_made"],
    "fg_miss": ["fg_missed", "field_goals_missed"],
    "fg_0_39": ["fgm_0_39", "fg_made_0_39"],
    "fg_40_49": ["fgm_40_49", "fg_made_40_49"],
    "fg_50_59": ["fgm_50_59", "fg_made_50_59"],
    "fg_60_plus": ["fgm_60_plus", "fg_made_60_plus", "fg_made_60_plus_yards"],

    # DST (team defense)
    "dst_sacks": ["def_sacks", "sacks", "team_def_sacks"],
    "dst_int": ["def_interceptions", "interceptions_def", "team_def_interceptions"],
    "dst_fr": ["def_fumbles_recovered", "fumbles_recovered_def", "team_def_fumbles_rec"],
    "dst_safety": ["def_safeties", "safeties", "team_def_safeties"],
    "dst_block": ["def_blocked_kicks", "blocked_kicks", "team_def_blocks"],
    "points_allowed": ["points_allowed", "pa_def", "def_points_allowed"],
    "yards_allowed": ["yards_allowed", "ya_def", "def_yards_allowed"],
    "dst_kr_td": ["def_kick_return_td", "def_kick_return_tds"],
    "dst_pr_td": ["def_punt_return_td", "def_punt_return_tds"],
    "dst_int_ret_td": ["def_int_return_td", "def_interception_td"],
    "dst_fum_ret_td": ["def_fumble_return_td"],
    "dst_blk_kick_ret_td": ["def_blocked_kick_return_td"]
}


# -------- Position detection --------
def detect_pos(row: pd.Series) -> str:
    for k in ("pos", "position", "player_position", "fantasy_position"):
        if k in row and isinstance(row[k], str) and row[k]:
            return row[k].upper()
    return "FLEX"  # assume non-DST/K skill if unknown


# -------- Core calculators --------
def _score_passing(row: pd.Series, s: Dict[str, Any]) -> float:
    p = s["offense"]["passing"]
    yards = _g(row, ALIAS["pass_yds"])
    pts = yards * p["yards_per"]
    pts += _g(row, ALIAS["pass_tds"]) * p["td"]
    pts += _g(row, ALIAS["pass_int"]) * p["int"]
    pts += _g(row, ALIAS["two_pt_pass"]) * p["two_pt"]
    if yards >= 400:
        pts += p.get("bonus_400_plus_yards", 0.0)
    return pts


def _score_rushing(row: pd.Series, s: Dict[str, Any]) -> float:
    r = s["offense"]["rushing"]
    yards = _g(row, ALIAS["rush_yds"])
    pts = yards * r["yards_per"]
    pts += _g(row, ALIAS["rush_tds"]) * r["td"]
    pts += _g(row, ALIAS["two_pt_rush"]) * r["two_pt"]
    pts += _g(row, ALIAS["rush_fd"]) * r["first_down"]
    if 100 <= yards < 200:
        pts += r.get("bonus_100_to_199_yards", 0.0)
    return pts


def _score_receiving(row: pd.Series, s: Dict[str, Any]) -> float:
    rc = s["offense"]["receiving"]
    yards = _g(row, ALIAS["rec_yds"])
    pts = yards * rc["yards_per"]
    pts += _g(row, ALIAS["rec"]) * rc["reception"]
    pts += _g(row, ALIAS["rec_tds"]) * rc["td"]
    pts += _g(row, ALIAS["two_pt_rec"]) * rc["two_pt"]
    pts += _g(row, ALIAS["rec_fd"]) * rc["first_down"]
    if yards >= 200:
        pts += rc.get("bonus_200_plus_yards", 0.0)
    return pts


def _score_turnovers_and_returns(row: pd.Series, s: Dict[str, Any]) -> float:
    o = s["offense"]
    pts = _g(row, ALIAS["fumbles_lost"]) * o["turnovers"]["fumbles_lost"]
    r = o["returns"]
    pts += _g(row, ALIAS["kr_td"]) * r["kick_return_td"]
    pts += _g(row, ALIAS["pr_td"]) * r["punt_return_td"]
    pts += _g(row, ALIAS["int_ret_td"]) * r["int_return_td"]
    pts += _g(row, ALIAS["fum_ret_td"]) * r["fumble_return_td"]
    pts += _g(row, ALIAS["blk_kick_ret_td"]) * r["blocked_kick_return_td"]
    pts += _g(row, ALIAS["two_pt_ret"]) * r["two_pt_return"]
    pts += _g(row, ALIAS["one_pt_safety"]) * r["one_pt_safety"]
    return pts


def _score_kicker(row: pd.Series, s: Dict[str, Any]) -> float:
    k = s["kicking"]
    pts = 0.0
    pts += _g(row, ALIAS["pat_made"]) * k["pat_made"]
    pts += _g(row, ALIAS["fg_miss"]) * k["fg_miss"]
    pts += _g(row, ALIAS["fg_0_39"]) * k["fg_0_39"]
    pts += _g(row, ALIAS["fg_40_49"]) * k["fg_40_49"]
    pts += _g(row, ALIAS["fg_50_59"]) * k["fg_50_59"]
    pts += _g(row, ALIAS["fg_60_plus"]) * k["fg_60_plus"]
    return pts


def _bucket_score(value: float, buckets: list[Dict[str, Any]]) -> float:
    for b in buckets:
        mn = b.get("min", None)
        mx = b.get("max", None)
        if mn is None and value <= mx:
            return float(b["points"])
        if mx is None and value >= mn:
            return float(b["points"])
        if mn is not None and mx is not None and mn <= value <= mx:
            return float(b["points"])
    return 0.0


def _score_dst(row: pd.Series, s: Dict[str, Any]) -> float:
    d = s["dst"]
    pts = 0.0
    pts += _g(row, ALIAS["dst_sacks"]) * d["sack"]
    pts += _g(row, ALIAS["dst_block"]) * d["block"]
    pts += _g(row, ALIAS["dst_int"]) * d["interception"]
    pts += _g(row, ALIAS["dst_fr"]) * d["fumble_recovery"]
    pts += _g(row, ALIAS["dst_safety"]) * d["safety"]

    # Return TDs (team)
    r = d["return_tds"]
    pts += _g(row, ALIAS["dst_kr_td"]) * r["kickoff"]
    pts += _g(row, ALIAS["dst_pr_td"]) * r["punt"]
    pts += _g(row, ALIAS["dst_int_ret_td"]) * r["interception"]
    pts += _g(row, ALIAS["dst_fum_ret_td"]) * r["fumble"]
    pts += _g(row, ALIAS["dst_blk_kick_ret_td"]) * r["blocked_kick"]

    # Points/Yards allowed buckets
    pa = _g(row, ALIAS["points_allowed"])
    ya = _g(row, ALIAS["yards_allowed"])
    pts += _bucket_score(pa, d["points_allowed"])
    pts += _bucket_score(ya, d["yards_allowed"])
    return pts


def calculate_fantasy_points(row: pd.Series, pos: Optional[str] = None,
                              scoring: Optional[Dict[str, Any]] = None) -> float:
    """
    Calculate fantasy points for a single row (single player-week).
    Expects per-game (not season) rows. Works for QB/RB/WR/TE/K/DST.
    """
    s = scoring or load_scoring()
    position = (pos or detect_pos(row)).upper()

    if position == "DST":
        return round(_score_dst(row, s), 2)
    if position == "K":
        return round(_score_kicker(row, s), 2)

    # Skill players (QB/RB/WR/TE)
    pts = 0.0
    pts += _score_passing(row, s)
    pts += _score_rushing(row, s)
    pts += _score_receiving(row, s)
    pts += _score_turnovers_and_returns(row, s)
    return round(pts, 2)


def apply_scoring(df: pd.DataFrame, position_col: str = "pos",
                  scoring: Optional[Dict[str, Any]] = None,
                  out_col: str = "fantasy_points") -> pd.DataFrame:
    """
    Add a fantasy points column to a DataFrame.
    """
    s = scoring or load_scoring()

    def _row_calc(row):
        pos = str(row.get(position_col, "")) if position_col in row else None
        return calculate_fantasy_points(row, pos=pos, scoring=s)

    df = df.copy()
    df[out_col] = df.apply(_row_calc, axis=1)
    return df


# -------- Convenience: quick sanity check --------
if __name__ == "__main__":
    # Minimal smoke test if you run:  python -m pipeline.utils
    sample = pd.Series({
        "pos": "WR",
        "receptions": 7,
        "receiving_yards": 92,
        "receiving_tds": 1,
        "receiving_first_downs": 4
    })
    print("Sample WR points:", calculate_fantasy_points(sample))
