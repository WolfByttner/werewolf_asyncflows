import random
from typing import Literal
from player import Player, VILLAGER, WEREWOLF, SEER

from collections import defaultdict

from dotenv import load_dotenv


class Game:
    def __init__(self,
                 num_players: int = 10,
                 num_werewolves: int = 3,
                 num_seers: int = 0,
                 debug=True):

        assert num_players > 0, "Player count too low"
        assert num_players <= 10, "Exceeding max player count"

        load_dotenv()

        # TODO asserts with werewolves and seers

        self.num_players = num_players
        self.num_werewolves = num_werewolves
        self.num_seers = num_seers

        self.player_names = ["Alice", "Bob", "Jim", "Friderik", "Janez", "Doris", "Paella", "Kiki", "Chiko", "Lima", "Romeo", "Juliet"][0:num_players]
        self.system = "System"
        # self.name_type = Literal[tuple(PLAYER_NAMES)]

        self.werewolf_names = random.sample(self.player_names, num_werewolves)
        self.seer_names = []


        self.players = {}
        for player_name in self.player_names:
            # TODO seer
            role = VILLAGER if player_name not in self.werewolf_names else WEREWOLF
            temperature=2.8
            self.players[player_name] = Player(player_name, role, temperature=temperature)
        
        self.debug = debug

        self.history = []

        self.round_number = 0

        self.winner = None

        # UTTERANCES = 5
        # TABLE_CARDS = 2
        # ROLE_COUNTS = {
        #     VILLAGER: 7,
        #     WEREWOLF: 3,
        #     SEER: 2,
        # }
        # ALLOW_SEER_VOTE_SELF = False
        # ALLOW_WEREWOLVES_VOTE_WEREWOLF = False
        # ALLOW_LYNCH_VOTE_SELF = False

        # PLAYER_NAMES = ["Alice", "Bob", "Jim", "Friderik", "Janez", "Doris", "Paella", "Kiki", "Chiko", "Lima", "Romeo", "Juliet"]
        # SYSTEM = "System"
        # NAME_TYPE = Literal[tuple(PLAYER_NAMES)]


    @property
    def round_info(self):
        if self.round_number == 0:
            info = f"The game has just started. "
        else:
            info = f"Round {self.round_number} has started. "
        
        info += f"There are {len(self.players)} players of which are {self.num_werewolves} werewolves."

        return info

    @property
    def player_statuses(self):
        statuses = ", ".join([f"{player.name} is {'alive' if player.alive else 'dead'}" for player in self.players.values()])

        return statuses
    
    @property
    def alive_players(self):
        return [player.name for player in self.players.values() if player.alive]

    @property
    def alive_werewolves(self):
        return [player.name for player in self.players.values() if player.alive and player.role == WEREWOLF]

    async def night_phase(self):
        self.history.append(f"The night phase has started.")

        # The werewolves wake up
        votes_count = defaultdict(int)
        votes = {}
        for name, player in self.players.items():
            if player.role != WEREWOLF:
                continue
            vote = await player.vote_kill_with_self_stream(
                self.history,
                self.round_info,
                self.player_statuses,
                votes
            )
            if vote in self.player_names:
                votes_count[vote] += 1
                votes[name] = vote
        
        if len(votes_count) == 0:
            print("The werewolves could not agree on a target.")
            self.history.append("The werewolves could not agree who to maul.")
        else:
            # Compute top target counts
            top_target_count = max(votes_count.values())

            # Check if there is a tie
            top_targets = [target for target, count in votes_count.items() if count == top_target_count]

            if self.debug:
                print(f"Votes: {votes_count}")
                print(f"Top target count: {top_target_count}")
                print(f"Top targets: {top_targets}")

            if len(top_targets) > 1:
                print("The werewolves could not agree who to maul.")
                self.history.append("The werewolves could not agree who to maul.")

            else:
                target = top_targets[0]
                print(f"The werewolves have decided to maul {target}.")

                # Kill the target
                self.players[target].kill()

                self.history.append(f"{target} was mauled by werewolves.")



    async def discussion_phase(self):
        self.history.append(f"The discussion phase has started.")

        # Each player gets to speak in turn
        for name, player in self.players.items():
            if player.alive:
                speech = await player.speak_with_self_stream(
                    self.history,
                    self.round_info,
                    self.player_statuses,
                )

                print(f"{name}: {speech}")

                self.history.append(f"{name}: {speech}")
    

    async def lynch_phase(self):
        self.history.append(f"The lynch phase has started.")

        # Each player gets to vote in turn
        votes_count = defaultdict(int)
        votes = {}
        for name, player in self.players.items():
            if player.alive:
                vote = await player.vote_with_self_stream(
                    self.history,
                    self.round_info,
                    self.player_statuses,
                    votes
                )

                if vote in self.player_names:
                    votes_count[vote] += 1
                    votes[name] = vote
        
        if len(votes_count) == 0:
            print("No one was lynched.")
        else:
            # Compute top target counts
            top_target_count = max(votes_count.values())

            # Check if there is a tie
            top_targets = [target for target, count in votes_count.items() if count == top_target_count]

            if self.debug:
                print(f"Votes: {votes_count}")
                print(f"Top target count: {top_target_count}")
                print(f"Top targets: {top_targets}")

            if len(top_targets) > 1:
                print("There was a tie.")
            else:
                target = top_targets[0]
                print(f"{target} was voted out.")

                # Kill the target
                self.players[target].kill()

                self.history.append(f"{target} was voted out.")


    async def round(self):
        self.history.append(f"Round {self.round_number} has started. {self.alive_players} players are alive")

        await self.night_phase()
        await self.discussion_phase()
        await self.lynch_phase()
        self.round_number += 1

        if self.alive_werewolves == 0:
            print("The villagers have won.")
            self.winner = VILLAGER
        elif len(self.alive_werewolves) >= len(self.alive_players) / 2:
            print("The werewolves have won.")
            self.winner = WEREWOLF

    async def run(self):
        while self.winner is None:
            await self.round()

        print(f"The game has ended. The {self.winner} have won.")
        self.history.append(f"The game has ended. The {self.winner} have won.")
