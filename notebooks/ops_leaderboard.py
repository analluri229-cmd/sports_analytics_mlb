from library_imports import *

START, END = choose_season()
YEAR = START[:4]

# Baseball-Reference date ranges include the postseason (Judge 2025: 159 G instead of 152),
# so swap the wide window for the exact regular-season dates
START, END = season_dates(YEAR)

df = pyb.batting_stats_range(START, END)
df["Name"] = df["Name"].map(fix_name)

# Rule 9.22: qualified = 3.1 PA per scheduled team game (502 in a 162-game season, 186 in 2020)
team_games = 60 if YEAR == "2020" else 162
if END >= date.today().isoformat():                  # season still going: count games played so far
    team_games = min(team_games, int(df["G"].max()))
min_pa = round(3.1 * team_games)
df = df[df["PA"] >= min_pa].copy()
top = df.sort_values("OPS", ascending=False).head(10)
print(top)

fig, ax = plt.subplots(figsize=(8.0, 5.4))
names = top["Name"].tolist()[::-1]
vals = top["OPS"].tolist()[::-1]

ax.barh(range(len(names)), vals)
ax.set_yticks(range(len(names)))
ax.set_yticklabels(names, fontsize=10)
ax.set_xlabel("OPS (on-base plus slugging)")
ax.set_title(f"{YEAR} OPS leaders (min {min_pa} PA), pulled with pybaseball", loc="left")

for i, v in enumerate(vals):
    ax.text(v + .004, i, "%.3f" % v, va="center", fontsize=9)
plt.savefig(OUT / f"bar_ops-leaders_{YEAR}.png", dpi=150, bbox_inches="tight")
plt.show()
