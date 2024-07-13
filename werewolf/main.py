from player import Player
from typing import List
from game import Game
import asyncio


from typing import Literal

game = Game(num_players=4, num_werewolves=1)

asyncio.run(game.run())

print("\n\n\n\n\n\n\n\n\n\n\n")

# Print the game history
for event in game.history:
    print(event)