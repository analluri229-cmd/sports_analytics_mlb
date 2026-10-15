from library_imports import *
PLAYER_ID, PLAYER_NAME = choose_player()

data = statcast('2023-04-23', '2023-04-23')

plot_strike_zone(data.loc[data["batter"] == PLAYER_ID], title = f"{PLAYER_NAME}'s Three True Outcome Day", colorby='pitcher', annotation="description")