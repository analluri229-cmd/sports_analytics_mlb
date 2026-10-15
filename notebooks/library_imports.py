"""Shared setup for the notebooks/ scripts: imports, output folder, player and season lookup.

At the top of a script in this folder:

    from library_imports import *
    PLAYER_ID, PLAYER_NAME = choose_player()
    START, END = choose_season()
"""
import requests
from datetime import date
from difflib import get_close_matches
from pathlib import Path
import sys
import unicodedata
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pybaseball as pyb
from pybaseball import cache, statcast
from pybaseball.plotting import plot_strike_zone
from scipy.stats import gaussian_kde
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize, PowerNorm

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
warnings.filterwarnings("ignore")
cache.enable()


ROOT = Path(__file__).resolve().parent.parent   # sports_analytics_mlb/
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

MIN_YEAR   = 2015   # Statcast batted-ball data starts in 2015
MAX_SHOWN  = 15     # most search results listed at once
SCALE      = 2.5    # Statcast hit-coordinate units -> feet


def _plain(s):
    # "Acuña" -> "acuna", so searches don't need accents
    return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower().strip()


def search_players(query):
    """Return Statcast-era players matching a last name, 'first last', 'last, first', or MLBAM id."""
    reg = pyb.chadwick_register()
    reg = reg[reg["key_mlbam"] > 0]
    q = query.strip().lstrip("\ufeff")                # stray byte-order mark from some terminals

    if q.isdigit():                                   # MLBAM id: any era
        return reg[reg["key_mlbam"] == int(q)]

    reg = reg[reg["mlb_played_last"] >= MIN_YEAR].copy()
    reg["full"] = (reg["name_first"].map(_plain) + " " + reg["name_last"].map(_plain))
    reg["last"] = reg["name_last"].map(_plain)

    # every word you typed has to appear in "first last" (order and commas don't matter)
    words = _plain(q).replace(",", " ").split()
    hits = reg[reg["full"].apply(lambda full: all(w in full for w in words))]

    if hits.empty:                                    # typo fallback: closest spellings
        close = get_close_matches(_plain(q), list(reg["full"]) + list(reg["last"]),
                                  n = 5, cutoff = .7)
        hits = reg[reg["full"].isin(close) | reg["last"].isin(close)]

    return hits.sort_values(["mlb_played_last", "mlb_played_first"], ascending = False)


def _label(row):
    first, last = row["mlb_played_first"], row["mlb_played_last"]
    years = f"{first:.0f}-{last:.0f}" if pd.notna(first) else "no MLB games"
    return f"{row['name_first']} {row['name_last']}  ({years})  id={row['key_mlbam']}"


def choose_player():
    """Ask for a search in the terminal, list matches as [1], [2], ..., return (mlbam_id, name).

    You can also pass the search on the command line: python heatmap_rates.py judge
    """
    query = " ".join(sys.argv[1:])
    while True:
        if not query:
            query = input("\nSearch player (last name, first last, or MLBAM id): ")
        res = search_players(query) if query.strip() else pd.DataFrame()
        query = ""                                    # only use the command line once

        if res.empty:
            print("  No matches -- try again.")
            continue

        rows = res.head(MAX_SHOWN).to_dict("records")
        if len(rows) == 1:
            pick = 1
            print(f"  Found {_label(rows[0])}")
        else:
            for i, row in enumerate(rows, 1):
                print(f"  [{i}] {_label(row)}")
            if len(res) > MAX_SHOWN:
                print(f"  ...showing {MAX_SHOWN} of {len(res)}; add a first name to narrow it down")
            pick = None
            while pick is None:
                choice = input(f"Pick 1-{len(rows)} (Enter to search again): ").strip().strip("[]")
                if not choice:
                    break
                if choice.isdigit() and 1 <= int(choice) <= len(rows):
                    pick = int(choice)
                else:
                    print(f"  '{choice}' isn't 1-{len(rows)}")
            if pick is None:
                continue

        row = rows[pick - 1]
        name = f"{row['name_first']} {row['name_last']}"
        print(f"  -> {name} (id {row['key_mlbam']})\n")
        return int(row["key_mlbam"]), name


def slug(name):
    """'Ronald Acuña' -> 'ronald_acuna', for output file names."""
    return _plain(name).replace(" ", "_").replace(".", "")

def fix_name(s):
    # Baseball-Reference names come back as literal UTF-8 byte escapes
    # (e.g. "Acu\xc3\xb1a") or as UTF-8 misread as Latin-1 (e.g. "AcuÃ±a")
    try:
        if "\\x" in s:
            s = s.encode("latin-1").decode("unicode_escape")
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s

def choose_season():
    """Ask for a season year, return (START, END) as 'YYYY-MM-DD' strings."""
    this_year = date.today().year
    year = input(f"Season ({MIN_YEAR}-{this_year}): ").strip()
    while not (year.isdigit() and MIN_YEAR <= int(year) <= this_year):
        year = input(f"  Enter a year from {MIN_YEAR} to {this_year}: ").strip()

    start = f"{year}-03-01"
    end = min(f"{year}-11-30", date.today().isoformat())   # never ask for the future
    return start, end

def load_pitches(player_id, player_name, start, end):
    """One batter's Statcast pitches, regular season only. Stops the script if there are none."""
    df = pyb.statcast_batter(start, end, player_id)
    df = df[df["game_type"] == "R"]
    if df.empty:
        raise SystemExit(f"No regular-season data for {player_name} from {start} to {end}.")
    return df


def batted_balls(df, min_count = 50):
    """Balls in play with field coordinates in feet (x: - is left field, y: out from home)."""
    bip = df[df["type"] == "X"]                              # every batted-ball event
    bb  = bip.dropna(subset = ["hc_x", "hc_y"]).copy()       # the ones we can plot
    bb["x"] = (bb["hc_x"] - 125.42) * SCALE
    bb["y"] = (198.27 - bb["hc_y"]) * SCALE
    if len(bb) < min_count:
        raise SystemExit(f"Only {len(bb)} batted balls -- too few to chart (need {min_count}).")
    return bb
def season_dates(year):
    """Exact MLB regular-season (start, end) for a year, from MLB's public Stats API."""
    url = f"https://statsapi.mlb.com/api/v1/seasons/{year}"
    s = requests.get(url, params = {"sportId": 1}, timeout = 10).json()["seasons"][0]
    return s["regularSeasonStartDate"], min(s["regularSeasonEndDate"], date.today().isoformat())
