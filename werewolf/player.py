import asyncio
from asyncflows import AsyncFlows
import asyncio
from typing import Literal
import os

VILLAGER = "Villager"
WEREWOLF = "Werewolf"
SEER = "Seer"
ROLE_NAMES = [
    VILLAGER,
    WEREWOLF,
    SEER,
]
ROLE_TYPE = Literal[tuple(ROLE_NAMES)]


class Player:
    def __init__(self, name: str, role: str, temperature, debug=True):
        self.name = name
        self.role = role
        self.player_side = VILLAGER if self.role != WEREWOLF else WEREWOLF
        self.alive = True
        self.previous_thoughts = f"I am a {role}."
        self.temperature=temperature
        self.debug=debug

        self._load_flows()
    
    
    def _load_flows(self, base_dir: str | None = None):
        if base_dir is None:
            base_dir = os.path.dirname(os.path.dirname(__file__))

        with open(os.path.join(base_dir, "flows", "self_stream.yaml"), "r") as f:
            self.flow_self_stream = f.read()


    async def speak_with_self_stream(self,
                              history: list[str],
                              round_info: str,
                              player_statuses: dict[str, bool]
    ):

        # Load the flow from the file
        flow = AsyncFlows.from_text(self.flow_self_stream).set_vars(
            temperature=self.temperature,
            player_side=self.player_side,
            history="\n".join(history),
            previous_thoughts=self.previous_thoughts,
            round_info=round_info,
            role=self.role,
            side=WEREWOLF if self.role == WEREWOLF else VILLAGER,
            player=self.name,
            players=player_statuses,
            task="discussing to find werewolves"
        )

        self.previous_thoughts = await flow.run('self_stream')

        # Run the flow
        if self.player_side == WEREWOLF:
            output = await flow.run('speak_werewolf_day')
        else:
            output = await flow.run('speak_villager_day')

        return output

    async def vote_with_self_stream(self,
                            history: list[str],
                            round_info: str,
                            player_statuses: dict[str, bool],
                            other_votes: dict[str] | None = None
    ):
        
        if other_votes is None or len(other_votes) == 0:
            other_votes_str = "You are the first to vote."
        else:
            other_votes_str = " ".join([f"{name} voted for {vote}." for name, vote in other_votes.items()])


        # Load the flow from the file
        flow = AsyncFlows.from_text(self.flow_self_stream).set_vars(
            temperature=self.temperature,
            player_side=self.player_side,
            history="\n".join(history),
            previous_thoughts=self.previous_thoughts,
            round_info=round_info,
            other_votes=other_votes_str,
            role=self.role,
            side=WEREWOLF if self.role == WEREWOLF else VILLAGER,
            player=self.name,
            players=player_statuses,
            task="voting to lynch werewolves"
        )

        self.previous_thoughts = await flow.run('self_stream')

        # Run the flow
        if self.player_side == WEREWOLF:
            output = await flow.run('vote_werewolf_day')
        else:
            output = await flow.run('vote_villager_day')

        return output


    def kill(self):
        self.alive = False


    async def vote_kill_with_self_stream(self,
                                        history: list[str],
                                        round_info: str,
                                        player_statuses: dict[str, bool],
                                        other_votes: dict[str] | None = None
    ):

        if other_votes is None or len(other_votes) == 0:
            other_votes_str = "You are the first to vote."
        else:
            other_votes_str = " ".join([f"{name} voted for {vote}." for name, vote in other_votes.items()])

        # Load the flow from the file
        flow = AsyncFlows.from_text(self.flow_self_stream).set_vars(
            temperature=self.temperature,
            player_side=self.player_side,
            history="\n".join(history),
            previous_thoughts=self.previous_thoughts,
            round_info=round_info,
            other_votes=other_votes_str,
            player=self.name,
            role=self.role,
            side=WEREWOLF if self.role == WEREWOLF else VILLAGER,
            players=player_statuses,
            task="voting to maul villagers"
        )

        self.previous_thoughts = await flow.run('self_stream')

        output = await flow.run('vote_werewolf_night')

        return output


    def __str__(self):
        return f"{self.name}"