from library_imports import *

PLAYER_ID, PLAYER_NAME = choose_player()
START, END = choose_season()
YEAR = START[:4]

df = load_pitches(PLAYER_ID, PLAYER_NAME, START, END)
bb = batted_balls(df)



# Statcast `events` code -> panel title ("all" = every batted ball)
HEAT_EVENTS = [
    ("all",                       "All batted balls"),
    ("single",                    "Single"),
    ("double",                    "Double"),
    ("triple",                    "Triple"),
    ("home_run",                  "Home run"),
    ("field_out",                 "Field out"),
    ("sac_fly",                   "Sac fly"),
    ("force_out",                 "Force out"),
    ("grounded_into_double_play", "Ground into DP"),
]
MIN_KDE = 5        # fewer events than this -> just show the dots
BW      = None     # KDE smoothing: None = Scott's rule; try 0.25 for tighter hot spots
CMAP    = "Reds"   # one hue, light -> dark = cold -> hot
LEVELS  = np.linspace(0.05, 1, 12)   # skip the faintest 5% so empty field stays white

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

fig, axes = plt.subplots(3, 3, figsize = (12, 12.5), constrained_layout = True)

for ax, (ev, label) in zip(axes.flat, HEAT_EVENTS):
    pts = bb if ev == "all" else bb[bb["events"] == ev]
    n = len(pts)

    if n >= MIN_KDE:
        try:
            kde = gaussian_kde(np.vstack([pts["x"], pts["y"]]), bw_method = BW)
            z = kde(grid).reshape(gx.shape)
            z = z / z.max()                      # 1 = hottest spot for THIS outcome
            ax.contourf(gx, gy, z, levels = LEVELS, cmap = CMAP)
        except np.linalg.LinAlgError:            # points all in a line -> no 2D density
            pass
    elif n > 0:
        ax.text(0, 440, "too few for a heatmap", ha = "center",
                fontsize = 8, color = "gray")

    # the actual batted balls, faint, so you can see what the gradient is built from
    ax.scatter(pts["x"], pts["y"], s = 5, color = "black", alpha = .3,
               edgecolors = "none")
    draw_field(ax)
    ax.set_title(f"{label}  (n={n})", loc = "left", fontsize = 10)

fig.colorbar(ScalarMappable(norm = Normalize(0, 1), cmap = CMAP), ax = axes,
             shrink = .5, pad = .02,
             label = "Relative density (1 = densest spot for that outcome)")
fig.suptitle(f"{PLAYER_NAME} -- 2025 batted-ball hot zones by outcome",
             x = .02, ha = "left", fontsize = 13)
plt.savefig(OUT / f"heat_{slug(PLAYER_NAME)}_{YEAR}.png", dpi = 150, bbox_inches = "tight")
plt.show()

