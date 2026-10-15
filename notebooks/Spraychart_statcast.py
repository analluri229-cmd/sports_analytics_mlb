from library_imports import *

PLAYER_ID, PLAYER_NAME = choose_player()
START, END = choose_season()
YEAR = START[:4]

df = load_pitches(PLAYER_ID, PLAYER_NAME, START, END)
bb = batted_balls(df)

# Statcast `events` code -> (legend label, color, marker, size)
OUTCOMES = {
    "single":                    ("Single",          "#1f77b4", "o", 30),
    "double":                    ("Double",          "#2ca02c", "o", 34),
    "triple":                    ("Triple",          "#9467bd", "o", 38),
    "home_run":                  ("Home run",        "#d62728", "*", 90),
    "field_out":                 ("Field out",       "#9e9e9e", "o", 20),
    "sac_fly":                   ("Sac fly",         "#ff7f0e", "^", 34),
    "force_out":                 ("Force out",       "#8c564b", "s", 26),
    "grounded_into_double_play": ("Ground into DP",  "#000000", "D", 26),
}

bb["outcome"] = bb["events"].where(bb["events"].isin(OUTCOMES), "other")

# 1) Spray chart colored by outcome
fig, ax = plt.subplots(figsize = (8.5, 7.0))

# anything not in the list above (errors, fielder's choice, other DPs, etc.)
other = bb[bb["outcome"] == "other"]
if len(other):
    ax.scatter(other["x"], other["y"], s = 18, alpha = .35, color = "#d0d0d0",
               edgecolors = "none", label = f"Other ({len(other)})")

# draw outs first so hits sit on top
draw_order = ["field_out", "force_out", "grounded_into_double_play", "sac_fly",
              "single", "double", "triple", "home_run"]
for ev in draw_order:
    label, color, marker, size = OUTCOMES[ev]
    pts = bb[bb["outcome"] == ev]
    if pts.empty:
        continue
    ax.scatter(pts["x"], pts["y"], s = size, color = color, marker = marker,
               alpha = .85, edgecolors = "white", linewidths = .4,
               label = f"{label} ({len(pts)})")

# foul lines + a stylized wall: 330 down the lines, 400 to center
ax.plot([0, -233], [0, 233], color = "black", lw = 1)
ax.plot([0, 233], [0, 233], color = "black", lw = 1)
th = np.linspace(np.pi/4, 3*np.pi/4, 200)
wall = 330 + 70*np.sin(2*(th - np.pi/4))
ax.plot(wall*np.cos(th), wall*np.sin(th),
        color = "black", lw = 1, ls = "--", alpha = .5)
ax.set_aspect("equal")
ax.axis("off")
ax.set_title(f"{PLAYER_NAME} -- {YEAR} spray chart by outcome", loc = "left")
ax.legend(loc = "upper left", bbox_to_anchor = (1.0, 1.0),
          frameon = False, fontsize = 9, title = "Outcome")
plt.savefig(OUT / f"spray_{slug(PLAYER_NAME)}_{YEAR}.png", dpi = 150, bbox_inches = "tight")
plt.show()

# 2) pybaseball's built-in spray chart, every game on a neutral park outline
pyb.spraychart(df, "generic", title = f"{PLAYER_NAME}: {YEAR} regular season")
plt.savefig(OUT / f"spray_outcome_{slug(PLAYER_NAME)}_{YEAR}.png", dpi = 150, bbox_inches = "tight")
plt.show()
