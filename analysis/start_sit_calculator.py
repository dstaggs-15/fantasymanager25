# analysis/start_sit_calculator.py
# Builds a Start/Sit score (0–100) per player-week with component breakdowns.
# It only needs docs/data/analysis/nfl_data.csv. It will also *optionally* use:
#   - docs/data/analysis/oline_metrics.csv  (team,season,week,oline in [0..1])
#   - docs/data/analysis/vegas_implied.csv  (team,season,week,implied in [0..1])
#
# Outputs:
#   docs/data/analysis/start_sit_report.json
#   docs/data/analysis/start_sit_meta.json  (weights & notes)

from __future__ import annotations
from pathlib import Path
import json
import math
import pandas as pd
import sys

# ensure pipeline.utils is importable
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.utils import apply_scoring, load_scoring  # noqa: E402

DATA = ROOT / "docs" / "data" / "analysis"
SRC  = DATA / "nfl_data.csv"
OUT  = DATA / "start_sit_report.json"
META = DATA / "start_sit_meta.json"

# Optional inputs (if missing, neutral 0.50 values are used)
OLINE = DATA / "oline_metrics.csv"     # columns: team,season,week,oline (0..1)
VEGAS = DATA / "vegas_implied.csv"     # columns: team,season,week,implied (0..1)

WEIGHTS = {
    "RB": {"usage":0.30,"eff":0.10,"oline":0.20,"opp":0.20,"env":0.10,"cons":0.05,"inj":0.05},
    "WR": {"usage":0.35,"eff":0.10,"oline":0.10,"opp":0.20,"env":0.15,"cons":0.05,"inj":0.05},
    "TE": {"usage":0.35,"eff":0.10,"oline":0.10,"opp":0.20,"env":0.15,"cons":0.05,"inj":0.05},
    "QB": {"usage":0.25,"eff":0.20,"oline":0.10,"opp":0.15,"env":0.20,"cons":0.05,"inj":0.05},
}

def minmax(s: pd.Series):
    s = s.astype(float)
    s = s.fillna(s.median() if not math.isnan(s.median()) else 0.0)
    lo, hi = float(s.min()), float(s.max())
    if hi <= lo:
        return pd.Series([0.5]*len(s), index=s.index)
    return (s - lo) / (hi - lo)

def safe_col(df: pd.DataFrame, name: str, default=0.5):
    if name not in df.columns:
        df[name] = default
    return df

def load_optional_csv(path: Path, cols: list[str]) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=cols)
    df = pd.read_csv(path)
    for c in cols:
        if c not in df.columns:
            df[c] = None
    return df[cols].copy()

def build_usage_efficiency(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build usage/efficiency/consistency features from whatever columns exist.
    We assume df is per player-game and has at least: season, week, player_id, pos, team, opp.
    """
    d = df.copy()

    # Try to pick reasonable columns if present.
    snaps = d.get("offense_snaps") if "offense_snaps" in d.columns else d.get("snaps")
    rush_att = d.get("rushing_attempts") or d.get("rush_att")
    targets = d.get("targets") or d.get("receiving_targets")
    air = d.get("air_yards")
    rz_rush = d.get("redzone_rush_att") or d.get("rushing_red_zone_attempts")
    rz_tgt = d.get("redzone_targets") or d.get("receiving_red_zone_targets")

    # Recent form windows (last 5)
    d = d.sort_values(["player_id","season","week"])
    roll_src = d[["player_id","season","week"]].copy()
    def rmean(col):
        if col is None or col.name not in d:
            return pd.Series([None]*len(d))
        return (
            d.groupby(["player_id","season"])[col.name]
             .rolling(5, min_periods=1).mean()
             .reset_index(level=[0,1], drop=True)
        )

    # Fill base cols on d (so .name attr exists)
    if snaps is None: d["snaps"]=None; snaps=d["snaps"]
    if rush_att is None: d["rush_att"]=None; rush_att=d["rush_att"]
    if targets is None: d["targets"]=None; targets=d["targets"]
    if air is None: d["air_yards"]=None; air=d["air_yards"]
    if rz_rush is None: d["rz_rush"]=None; rz_rush=d["rz_rush"]
    if rz_tgt is None: d["rz_tgt"]=None; rz_tgt=d["rz_tgt"]

    # Recent averages
    d["r5_snaps"]   = rmean(snaps)
    d["r5_rush"]    = rmean(rush_att)
    d["r5_tgt"]     = rmean(targets)
    d["r5_air"]     = rmean(air)
    d["r5_rz_rush"] = rmean(rz_rush)
    d["r5_rz_tgt"]  = rmean(rz_tgt)

    # Usage proxies per position
    d["usage_rb"] = (d["r5_snaps"].fillna(0)*0.4
                    + (d["r5_rush"].fillna(0)+d["r5_tgt"].fillna(0))*0.6
                    + d["r5_rz_rush"].fillna(0)*0.2)
    d["usage_wr"] = d["r5_tgt"].fillna(0)*0.7 + d["r5_air"].fillna(0)*0.3 + d["r5_rz_tgt"].fillna(0)*0.2
    d["usage_te"] = d["r5_tgt"].fillna(0)*0.8 + d["r5_rz_tgt"].fillna(0)*0.2
    d["usage_qb"] = (d.get("pass_attempts", pd.Series([None]*len(d))).fillna(
                      d.get("passing_attempts", pd.Series([0]*len(d)))) * 0.7
                    + d.get("designed_qb_rush", pd.Series([0]*len(d))).fillna(0)*0.3)

    # Efficiency proxies (lightweight—works even if advanced cols missing)
    d["eff_rb"] = (d.get("rushing_yards_before_contact", pd.Series([0]*len(d))).fillna(0)*0.6
                   + d.get("rushing_yards_after_contact", pd.Series([0]*len(d))).fillna(0)*0.4)
    d["eff_wr"] = d.get("yards_per_route_run", pd.Series([0]*len(d))).fillna(
                  d.get("yards_per_target", pd.Series([0]*len(d))).fillna(0))
    d["eff_te"] = d["eff_wr"]
    d["eff_qb"] = d.get("epa_per_play", pd.Series([0]*len(d))).fillna(
                  d.get("passer_rating", pd.Series([0]*len(d))).fillna(0))

    # Consistency = invert of stdev/mean on fantasy points (lower stdev/mean = more consistent)
    d = d.sort_values(["player_id","season","week"])
    d["stdev5"] = (d.groupby(["player_id","season"])["fantasy_points"]
                    .rolling(5, min_periods=2).std().reset_index(level=[0,1], drop=True))
    d["mean5"]  = (d.groupby(["player_id","season"])["fantasy_points"]
                    .rolling(5, min_periods=2).mean().reset_index(level=[0,1], drop=True))
    cr = (d["stdev5"] / d["mean5"]).replace([math.inf,-math.inf], 1).fillna(1)
    d["cons_raw"] = cr
    d["cons"] = 1 - minmax(cr)  # higher = steadier

    return d

def build_opp_dvp(df_scored: pd.DataFrame) -> pd.DataFrame:
    """
    Defense vs position: average fantasy points allowed by a defense to each POSITION
    in a rolling recent window (last 6 games in that season). Lower conceded -> tougher.
    """
    d = df_scored.copy()
    d["pos"] = d["pos"].str.upper()
    # group by defense + week to sum fantasy points that position scored *against* that defense that week
    # First: aggregate by (season, week, opp_def, pos)
    grp = (d.groupby(["season","week","opp","pos"])["fantasy_points"]
             .sum().reset_index().rename(columns={"opp":"def_team","fantasy_points":"pos_pts_allowed"}))
    grp = grp.sort_values(["def_team","season","week"])
    grp["dvp_recent"] = (grp.groupby(["def_team","season","pos"])["pos_pts_allowed"]
                           .rolling(6, min_periods=1).mean()
                           .reset_index(level=[0,1,2], drop=True))
    return grp[["season","week","def_team","pos","dvp_recent"]]

def main():
    if not SRC.exists():
        raise FileNotFoundError(f"Missing {SRC}. Run pipeline/get_nfl_data.py first.")

    scoring = load_scoring()
    base = pd.read_csv(SRC)

    # Ensure key columns exist
    for c in ["player_id","player","team","opp","pos","season","week"]:
        if c not in base.columns:
            base[c] = ""

    # Apply scoring if needed
    if "fantasy_points" not in base.columns:
        base = apply_scoring(base, position_col="pos", scoring=scoring)

    # normalize POS
    base["pos"] = base["pos"].astype(str).str.upper()

    # Optional O-line + Vegas
    ol = load_optional_csv(OLINE, ["team","season","week","oline"])
    vg = load_optional_csv(VEGAS, ["team","season","week","implied"])

    # Features
    feats = build_usage_efficiency(base)
    dvp = build_opp_dvp(feats)

    # Merge optional context (neutral defaults)
    feats = feats.merge(ol, on=["team","season","week"], how="left")
    feats = feats.merge(vg, on=["team","season","week"], how="left")
    feats["oline"] = feats["oline"].fillna(0.50)      # neutral if missing
    feats["implied"] = feats["implied"].fillna(0.50)  # neutral if missing

    # Attach defense-vs-position (lower allowed = tougher; convert to "goodness" where higher is better)
    feats = feats.merge(
        dvp.rename(columns={"def_team":"opp","pos":"pos_dvp"}), 
        on=["season","week","opp"], how="left"
    )
    # pick matching pos; when no match, fallback to overall median
    mask = feats["pos"].str.upper() == feats["pos_dvp"].astype(str).str.upper()
    feats.loc[~mask, "dvp_recent"] = None
    # dvp_good = 1 - normalized allowed points (so tougher defenses reduce score)
    feats["dvp_good"] = (1 - minmax(feats["dvp_recent"])) if feats["dvp_recent"].notna().any() else 0.50

    # Component normalization per position per week
    out = {}
    for (season, week), g in feats.groupby(["season","week"]):
        bucket = f"{int(float(season))}-W{int(float(week)):02d}" if str(season).strip() != "" else f"{season}-W{week}"
        out[bucket] = {}

        for pos, gp in g.groupby("pos"):
            pos = pos.upper()
            if pos not in WEIGHTS and pos not in ("RB","WR","TE","QB"):
                continue
            # pick usage/eff columns
            if pos == "RB":
                usage = minmax(gp["usage_rb"])
                eff   = minmax(gp["eff_rb"])
            elif pos in ("WR","TE"):
                usage = minmax(gp["usage_wr" if pos=="WR" else "usage_te"])
                eff   = minmax(gp["eff_wr"])
            else:  # QB
                usage = minmax(gp["usage_qb"])
                eff   = minmax(gp["eff_qb"])

            oline = minmax(gp["oline"])
            opp   = gp["dvp_good"].fillna(0.50)
            env   = minmax(gp["implied"])
            cons  = gp["cons"].fillna(0.50)
            inj   = pd.Series(0.50, index=gp.index)  # placeholder (can wire to injuries later)

            w = WEIGHTS.get(pos, WEIGHTS["WR"])
            score = (
                usage*w["usage"] + eff*w["eff"] + oline*w["oline"] +
                opp*w["opp"] + env*w["env"] + cons*w["cons"] + inj*w["inj"]
            )*100

            for i, row in gp.reset_index(drop=True).iterrows():
                pid = str(row.get("player_id",""))
                if not pid:  # make a synthetic id if missing
                    pid = f'{row.get("player","")}|{row.get("team","")}|{row.get("pos","")}'
                out[bucket][pid] = {
                    "player": str(row.get("player","")),
                    "pos": pos,
                    "team": str(row.get("team","")).upper(),
                    "opp":  str(row.get("opp","")).upper(),
                    "score": round(float(score.iloc[i]), 1),
                    "components": {
                        "usage": float(round(float(usage.iloc[i]),3)),
                        "eff":   float(round(float(eff.iloc[i]),3)),
                        "oline": float(round(float(oline.iloc[i]),3)),
                        "opp":   float(round(float(opp.iloc[i]),3)),
                        "env":   float(round(float(env.iloc[i]),3)),
                        "cons":  float(round(float(cons.iloc[i]),3))
                    }
                }

    DATA.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out, f, indent=2)

    with open(META, "w") as f:
        json.dump({
            "notes": "scores are 0..100; higher is better",
            "weights": WEIGHTS,
            "optional_inputs": {
                "oline_metrics.csv": OLINE.exists(),
                "vegas_implied.csv": VEGAS.exists()
            }
        }, f, indent=2)

    print(f"Wrote {OUT} and {META}")

if __name__ == "__main__":
    main()
