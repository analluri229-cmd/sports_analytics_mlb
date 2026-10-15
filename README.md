# sports_analytics_mlb

Rebuilding the kinds of views you see on Baseball Savant player pages (leaderboards, spray charts, zone heatmaps, percentile bars, comparisons) from public MLB data, in Python.

**Question:** Who were the best hitters of 2025, how do they get their results, and can I show it with clear charts built only from public data?

**Answer in one sentence:** (write this last, once the charts below exist)

## Status
- [x] Data pull with pybaseball (season batting stats, one hitter's Statcast pitches)
- [x] OPS leaders bar chart (`notebooks/ops_leaderboard.py`)
- [x] Spray chart for one hitter (`notebooks/Spraychart_statcast.py`)
- [ ] Save charts to `outputs/` (use the pattern in "Saving charts")
- [ ] Slash lines, top 10, best 5 per division, best per team
- [ ] Zone heatmaps, percentile bars, comparison charts, distributions
- [ ] Record the pull date and data terms (see Data)
- [ ] Pushed to GitHub

## Data
| Source | Pulled with | Used for |
|---|---|---|
| Baseball-Reference season batting stats | `pybaseball.batting_stats_range(start, end)` | Leaderboards (PA, AB, OPS and the slash line) |
| Baseball Savant Statcast pitch-by-pitch | `pybaseball.statcast_batter(start, end, player_id)` | Spray charts, heatmaps, exit velocity |

- Season used so far: 2025 regular season (2025-03-18 to 2025-09-28 for the leaderboard; 2025-03-27 to 2025-09-28 for the spray chart).
- Pull date: (fill in)
- Terms of use: (link the sites' data-use pages here and credit them)
- Raw pulls are cached by pybaseball (`cache.enable()`) and are not committed. `data/raw/` and `data/baseball/raw/` are git-ignored.

## Decisions log
- **300 plate-appearance minimum.** Keeps September call-ups and bench players with a few games out of the leaderboards. TODO: record how many players this removes.
- **Name fix.** Baseball-Reference names come back with encoding errors (for example Acuña). `fix_name()` repairs them. TODO: move it into `src/` so every script shares it.
- **Spray chart coordinates.** Statcast `hc_x` and `hc_y` are image pixels. The scripts convert them with `x = (hc_x - 125.42) * 2.5` and `y = (198.27 - hc_y) * 2.5`, which puts home plate at (0, 0) with the field in feet. The outfield wall is a stylized curve, not each park's real dimensions.
- **Batted balls only.** The spray chart uses rows where `type == "X"` and drops rows with no coordinates.

## Structure for the visuals
Every chart follows the same shape: one script, one data pull, one saved image. Planned charts, in the order I plan to build them:

| # | Chart | Data and key columns | Notes | Output file |
|---|---|---|---|---|
| 1 | Slash line table (AVG / OBP / SLG, OPS = OBP + SLG) | `batting_stats_range`: BA, OBP, SLG, OPS, AB, PA (confirm names with `df.columns`) | PA minimum applies | `table_slash-lines_2025.png` |
| 2 | Top 10 hitters' slash lines | same, sort by OPS, `head(10)` | | `bar_ops-leaders_2025.png` (done) |
| 3 | Best 5 hitters per division | add a team-to-division lookup (`data/reference/mlb_divisions.csv`, 30 rows), then `groupby("Division")` | Traded players have combined or multiple team rows. Check before grouping | `bar_best5-per-division_2025.png` |
| 4 | Best hitter per team (and chosen teams) | `groupby("Tm")` | Same traded-player check | `bar_best-per-team_2025.png` |
| 5 | Pitching leaders: ERA, WHIP | `pybaseball.pitching_stats` with an innings minimum | Innings cutoff needs its own reasoning | `bar_era-leaders_2025.png` |
| 6 | Spray chart (hits and outs) | `statcast_batter`: `hc_x`, `hc_y`, `events`, `type` | Color by single / double / triple / home run, like Savant | `spray_judge_2025.png` (script exists) |
| 7 | Zone heatmap with strike zone | `plate_x`, `plate_z`, `sz_top`, `sz_bot`, plus one metric (swing rate, exit velocity) | 2D bins, then draw the zone rectangle | `heatmap_judge_swing-rate_2025.png` |
| 8 | Pitcher heatmap and pitch usage % | `statcast_pitcher`: `pitch_type`, `plate_x`, `plate_z` | Usage % is a `value_counts(normalize=True)` | `heatmap_pitcher_location_2025.png` |
| 9 | Percentile rankings (Savant-style bars) | metrics such as exit velocity, barrel %, K %, BB %, `rank(pct=True) * 100` among qualified hitters | One row per metric, color from blue (low) to red (high) | `percentiles_judge_2025.png` |
| 10 | Comparison charts | two players' percentiles side by side | | `compare_judge-vs-ohtani_2025.png` |
| 11 | Fastest players (sprint speed) | Statcast sprint speed leaderboard | | `bar_sprint-speed_2025.png` |
| 12 | Distributions for each stat | `hist` / KDE of each metric among qualified hitters | Mark where a chosen player sits | `dist_<stat>_2025.png` |

**Metrics to cover:** AB, PA, AVG, OBP, SLG, OPS, wOBA, WAR, exit velocity, ERA, WHIP.

## Project layout
```
sports_analytics_mlb/
├── notebooks/        scripts that make one chart each (ops_leaderboard.py, Spraychart_statcast.py)
├── src/              shared helpers (name fix, paths, strike zone drawing). Not written yet
├── data/
│   ├── reference/    small hand-built lookups such as team-to-division (committed)
│   └── baseball/raw/ downloaded data (git-ignored)
├── outputs/          saved charts (committed, embedded below)
├── notes/            decisions.md
└── sql/              reserved for the SQL version of the leaderboards
```

## Saving charts
Each script saves to `outputs/` with a descriptive name, before `plt.show()`:
```python
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

plt.savefig(OUT / "spray_judge_2025.png", dpi=150, bbox_inches="tight")
plt.show()
```
File names follow `chart-type_subject_season.png`, lowercase with underscores.

## Findings
(Add 2 to 3 charts from `outputs/` once saved, each with one sentence saying what it shows.)

## Limitations
- Leaderboards depend on the plate-appearance minimum.
- Spray charts show where a ball landed on the field's coordinates, not the real park dimensions.
- Season-total leaderboards for traded players need care (team labels).
- Statcast fields (exit velocity, location) can be missing for some pitches.

## What I would do next
- Rebuild the leaderboards in SQL and R to show the same results three ways.
- Add a Tableau or Power BI version of the leaderboard and percentile views.

## How to run
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python notebooks/ops_leaderboard.py
python notebooks/Spraychart_statcast.py
```
(`requirements.txt` should list only what the scripts import: pybaseball, pandas, numpy, matplotlib.)

## Credits
Data from Baseball-Reference.com and Baseball Savant (MLB Advanced Media), accessed with the open-source `pybaseball` package.
