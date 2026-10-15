from library_imports import *

PLAYER_ID, PLAYER_NAME = choose_player()
START, END = choose_season()
YEAR = START[:4]

df = load_pitches(PLAYER_ID, PLAYER_NAME, START, END)
bb = batted_balls(df)


if len(bb) < 50:
    raise ValueError("too few batted balls: %d" % len(bb))

# ---- denominators -----------------------------------------------------------
# Statcast is one row per pitch; a PA's result is on its last pitch (`events`).
# Baserunning rows (caught stealing, pickoffs, ...) also fill `events` but are not PAs.
NOT_PA = ("caught_stealing", "pickoff", "stolen_base", "wild_pitch",
          "passed_ball", "other_advance", "truncated_pa")
# PAs that don't count as at-bats
NOT_AB = {"walk", "intent_walk", "hit_by_pitch", "sac_fly", "sac_bunt",
          "sac_fly_double_play", "sac_bunt_double_play", "catcher_interf"}

ends = df.dropna(subset=["events"])
ends = ends[~ends["events"].str.startswith(NOT_PA)]
pa   = ends.drop_duplicates(["game_pk", "at_bat_number"])

# rate key -> (denominator, multiplier, label)
DENOMS = {
    "game": (df["game_pk"].nunique(),              1,   "per game"),
    "pa":   (len(pa),                              100, "per 100 PA"),
    "ab":   (int((~pa["events"].isin(NOT_AB)).sum()), 100, "per 100 AB"),
}
print("G = %d, PA = %d, AB = %d" % tuple(v[0] for v in DENOMS.values()))

# ---- heatmap settings ---------------------------------------------------------
RATE_EVENTS = [
    ("single",                    "Single"),
    ("double",                    "Double"),
    ("triple",                    "Triple"),
    ("home_run",                  "Home run"),
    ("field_out",                 "Field out"),
    ("sac_fly",                   "Sac fly"),
    ("force_out",                 "Force out"),
    ("grounded_into_double_play", "Ground into DP"),
]
PATCH   = 20       # report rates for a PATCH x PATCH ft square of field
MIN_KDE = 5        # fewer events than this -> just show the dots

# evaluation grid covering the whole field (feet)
gx, gy = np.meshgrid(np.linspace(-300, 300, 241), np.linspace(-20, 480, 201))
grid = np.vstack([gx.ravel(), gy.ravel()])

def draw_field(ax):
    # foul lines + a stylized wall: 330 down the lines, 400 to center
    ax.plot([0, -233], [0, 233], color = "black", lw = .8)
    ax.plot([0, 233], [0, 233], color = "black", lw = .8)
    th = np.linspace(np.pi/4, 3*np.pi/4, 200)
    wall = 330 + 70*np.sin(2*(th - np.pi/4))
    ax.plot(wall*np.cos(th), wall*np.sin(th),
            color = "black", lw = .8, ls = "--", alpha = .5)
    ax.set_xlim(-300, 300)
    ax.set_ylim(-20, 480)
    ax.set_aspect("equal")
    ax.axis("off")

def rate_surface(pts, denom, per, bw = None):
    """Expected events in a PATCH x PATCH ft square at each grid point, per `per` denominators.

    gaussian_kde integrates to 1, so kde * n = expected events per sq ft over the
    whole sample. Multiply by the patch area, divide by the denominator, and you
    have the rate. (Averaging per-game maps gives the same thing: the mean of the
    per-game counts is just total / games.)
    """
    if len(pts) < MIN_KDE:
        return None
    try:
        kde = gaussian_kde(np.vstack([pts["x"], pts["y"]]), bw_method = bw)
    except np.linalg.LinAlgError:              # points all in a line -> no 2D density
        return None
    return kde(grid).reshape(gx.shape) * len(pts) * PATCH**2 / denom * per

def plot_rate_heatmaps(bb, rate = "game", bw = None, cmap = "Reds", save = True):
    """One panel per outcome, all on ONE shared color scale, so panels compare by volume."""
    denom, per, per_label = DENOMS[rate]

    surfaces = {ev: rate_surface(bb[bb["events"] == ev], denom, per, bw)
                for ev, _ in RATE_EVENTS}
    vmax = max(z.max() for z in surfaces.values() if z is not None)
    norm = PowerNorm(.5, vmin = 0, vmax = vmax)   # sqrt scale so rare outcomes still show
    levels = vmax * np.linspace(.12, 1, 14)**2    # evenly spaced on that sqrt scale

    fig, axes = plt.subplots(2, 4, figsize = (16, 9), constrained_layout = True)
    for ax, (ev, label) in zip(axes.flat, RATE_EVENTS):
        pts = bb[bb["events"] == ev]
        z = surfaces[ev]
        if z is not None:
            ax.contourf(gx, gy, z, levels = levels, cmap = cmap, norm = norm)
        elif len(pts):
            ax.text(0, 440, "too few for a heatmap", ha = "center",
                    fontsize = 8, color = "gray")
        ax.scatter(pts["x"], pts["y"], s = 5, color = "black", alpha = .3,
                   edgecolors = "none")
        draw_field(ax)
        ax.set_title(f"{label}: {len(pts) / denom * per:.2f} {per_label}",
                     loc = "left", fontsize = 10)
    
    fig.colorbar(ScalarMappable(norm = norm, cmap = cmap), ax = axes,
                 shrink = .6, pad = .02,
                 label = f"Expected events in a {PATCH}x{PATCH} ft patch, {per_label}")
    fig.suptitle(f"{PLAYER_NAME} -- 2025 hot zones {per_label} "
                 f"({denom} {'games' if rate == 'game' else rate.upper()})",
                 x = .02, ha = "left", fontsize = 13)
    if save:
        plt.savefig(OUT / f"heat_{rate}_{slug(PLAYER_NAME)}_{YEAR}.png", dpi = 150, bbox_inches = "tight")
    plt.show()

plot_rate_heatmaps(bb, rate = "game")
plot_rate_heatmaps(bb, rate = "pa")
plot_rate_heatmaps(bb, rate = "ab")
