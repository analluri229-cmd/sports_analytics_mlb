from library_imports import *

PLAYER_ID, PLAYER_NAME = choose_player()
START, END = choose_season()
YEAR = START[:4]

# 1) The chosen hitter's pitch-by-pitch Statcast data
pitches = pyb.statcast_batter(START, END, PLAYER_ID)
pitches = pitches[pitches["game_type"] == "R"]          # regular season only
zone = pitches.dropna(subset=["plate_x", "plate_z"])
if zone.empty:
    raise SystemExit(f"No {YEAR} pitch data for {PLAYER_NAME} -- pick another player or season.")

# 2) A heatmap of pitch locations
fig, ax = plt.subplots(figsize=(5, 6))
h = ax.hist2d(zone["plate_x"], zone["plate_z"], bins=20)
fig.colorbar(h[3], ax=ax, label="pitches")
ax.set_xlabel("plate_x (feet)"); ax.set_ylabel("plate_z (feet)")
ax.set_title(f"{PLAYER_NAME} -- pitch locations seen, {YEAR}", loc="left")
fig.savefig(OUT / f"heatmap_{slug(PLAYER_NAME)}_pitch-location_{YEAR}.png", dpi=150, bbox_inches="tight")
plt.show()
