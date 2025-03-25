import random
from typing import Optional, Tuple

from src.entities.endgame_messages import ENDGAME_MESSAGES
from src.entities.entities import PlayerInfo, STATUS_TEMPLATE, FireType, Factions, FleeDecision, Distance
from src.entities.health_status import PLAYER_HEALTH_DESCRIPTIONS
from src.page_manager import PageManager


class PlayerState:
    def __init__(self, player_name: str, faction: Factions):
        self.name = player_name
        self.faction = faction
        self.health = 6.0
        self.page_manager = PageManager(self.faction)

    def take_damage(self, amount: float):
        self.health = max(0.0, self.health - amount)

    def is_alive(self):
        return self.health > 0

    def __repr__(self):
        # Get the first applicable description
        description = next(desc for hp, desc in PLAYER_HEALTH_DESCRIPTIONS if self.health >= hp)
        return f"{self.name} ({self.faction.value})\n\n{description}"


class GameStateManager:
    null_move: Tuple[Optional[int], Optional[int]] = (None, None)
    null_lost_state: Optional[FleeDecision] = None
    tailing_player = None
    tailed_player = None
    tailed_page = None

    def __init__(self, player_info: PlayerInfo):
        """ Initializes the game state, tracking both players. """
        self.player = PlayerState(**player_info.model_dump())
        self.opponent = PlayerState(
            player_name="Opponent",
            faction=Factions.get_opposing_faction(self.player.faction)
        )

        self.current_player_page = self.player.page_manager.load_page()
        self.current_opponent_page = self.opponent.page_manager.load_page()

        self.moves = {
            self.player.faction: self.null_move,
            self.opponent.faction: self.null_move
        }

        self.lost_state_decisions = {
            self.player.faction: self.null_lost_state,
            self.opponent.faction: self.null_lost_state
        }

    def submit_move(self, faction: Factions, move_index: int):
        """ Stores a submitted move and processes turn if both players have submitted. """
        direction_message = {}

        if self.current_player_page.page_num == 223 or self.current_opponent_page.page_num == 223:
            return {"message": "Players must choose to chase or flee!"}

        if self.tailing_player:
            if faction == self.tailing_player.faction:
                # Tailing player can only submit after the tailed player
                if self.moves[self.tailed_player.faction] == self.null_move:
                    return {"message": "Waiting for the tailed player to move first"}

        if self.player.faction == faction:
            mid_page = self.current_player_page.moves[move_index].next_page
        else:
            mid_page = self.current_opponent_page.moves[move_index].next_page

        self.moves[faction] = (move_index, mid_page)

        if self.tailed_player:

            if faction == self.tailed_player.faction:
                # Get the direction of the tailed player's move
                tailed_move_index, _ = self.moves[self.tailed_player.faction]
                tailed_direction = self.tailed_page.moves[tailed_move_index].direction.value

                direction_message = {
                    "tailed_direction": tailed_direction
                }

        if self.null_move not in self.moves.values():
            return self._process_turn()
        return {"message": "Move received, waiting for opponent", **direction_message}

    def submit_lost_state_decision(self, faction: Factions, decision: FleeDecision):
        if self.current_player_page.page_num != 223 or self.current_opponent_page.page_num != 223:
            return {"message": "You aren't lost! Please submit a movement!"}

        self.lost_state_decisions[faction] = decision

        if None not in self.lost_state_decisions.values():
            return self._resolve_lost_state()

        return {"message": "Decision received, waiting for opponent"}

    def _process_turn(self):
        """ Resolves turn based on both players' moves, handling Page 223 cases. """
        player_faction = self.player.faction
        opponent_faction = self.opponent.faction

        player_move_index, player_mid_page = self.moves[player_faction]
        opponent_move_index, opponent_mid_page = self.moves[opponent_faction]

        # Handle Page 223 case
        if player_mid_page == 223:
            result_page = self.player.page_manager.find_result(opponent_mid_page, player_move_index)
        elif opponent_mid_page == 223:
            result_page = self.opponent.page_manager.find_result(player_mid_page, opponent_move_index)
        else:
            # Normal case: resolve result page using opponent's mid-page
            result_page = self.player.page_manager.find_result(opponent_mid_page, player_move_index)

        # Reset moves for next turn
        self.moves = {player_faction: self.null_move, opponent_faction: self.null_move}

        # If result page is 223, enter the special state
        if result_page == 223:
            self.current_player_page = self.player.page_manager.load_page(result_page)
            self.current_opponent_page = self.opponent.page_manager.load_page(result_page)
            self._determine_tailing()
            self.lost_state_decisions = {player_faction: self.null_lost_state, opponent_faction: self.null_lost_state}
            return {"message": "Players lost each other! Choose to chase or flee.", "new_page": 223}

        # Update player states
        self._resolve_turn(result_page)

        return {"message": "Turn resolved", "new_page": result_page}

    def _resolve_turn(self, result_page):
        self.current_player_page = self.player.page_manager.load_page(result_page)
        self.current_opponent_page = self.opponent.page_manager.load_page(result_page)

        self._deal_damage()

        player_alive = self.player.is_alive()
        opponent_alive = self.opponent.is_alive()

        if not player_alive and not opponent_alive:
            return {"message": "Both pilots go down in flames!", "game_end": True}

        if not player_alive:
            return {"message": self._get_endgame_message(self.opponent.name, self.player.name), "game_end": True}

        if not opponent_alive:
            return {"message": self._get_endgame_message(self.player.name, self.opponent.name), "game_end": True}

        self._determine_tailing()

    def _deal_damage(self):
        damage = Distance.get_damage(self.current_player_page.distance)

        if self.current_player_page.fire == FireType.NONE and self.current_opponent_page.fire == FireType.NONE:
            pass

        if self.current_player_page.fire == FireType.MUTUAL or self.current_opponent_page.fire == FireType.MUTUAL:
            self.player.take_damage(damage)
            self.opponent.take_damage(damage)

        if self.current_player_page.fire == FireType.OUT or self.current_opponent_page.fire == FireType.IN:
            self.opponent.take_damage(damage)

        if self.current_player_page.fire == FireType.IN or self.current_opponent_page.fire == FireType.OUT:
            self.player.take_damage(damage)

    def _determine_tailing(self):
        player_is_tailing = self.current_player_page.tail
        opponent_is_tailing = self.current_opponent_page.tail

        # Identify the tailing and tailed players
        if player_is_tailing:
            self.tailing_player = self.player
            self.tailed_player = self.opponent
            self.tailed_page = self.current_opponent_page
        elif opponent_is_tailing:
            self.tailing_player = self.opponent
            self.tailed_player = self.player
            self.tailed_page = self.current_player_page
        else:
            self.tailing_player = None
            self.tailed_player = None
            self.tailed_page = None

    def _resolve_lost_state(self):
        player_decision = self.lost_state_decisions[self.player.faction]
        opponent_decision = self.lost_state_decisions[self.opponent.faction]

        if player_decision == FleeDecision.FLEE and opponent_decision == FleeDecision.FLEE:
            return {"message": "Both players fled. The game ends in a draw.", "game_end": True}

        if player_decision == FleeDecision.CHASE and opponent_decision == FleeDecision.FLEE:
            return {"message": f"{self.player.name} wins a half-victory as {self.opponent.name} fled.", "game_end": True}

        if player_decision == FleeDecision.FLEE and opponent_decision == FleeDecision.CHASE:
            return {"message": f"{self.opponent.name} wins a half-victory as {self.player.name} fled.", "game_end": True}

        if player_decision == FleeDecision.CHASE and opponent_decision == FleeDecision.CHASE:
            self.current_player_page = self.player.page_manager.load_page()
            self.current_opponent_page = self.opponent.page_manager.load_page()
            return {"message": "Both players chose to chase! The game resets at page 170."}

        return {"message": "Unexpected error in resolving lost state."}

    @staticmethod
    def _get_endgame_message(winner, loser):
        return random.choice(ENDGAME_MESSAGES).format(winner=winner, loser=loser)

    def _get_status(self):
        tail = "" if self.current_player_page.tail else "not"
        out_fire = "" if self.current_player_page.fire in [FireType.OUT, FireType.MUTUAL] else "not"
        in_fire = "" if self.current_player_page.fire in [FireType.IN, FireType.MUTUAL] else "not"
        print(
            STATUS_TEMPLATE % (
                self.current_player_page.page_num,
                self.player.name,
                self.player.health,
                self.current_player_page.distance.value,
                tail,
                out_fire,
                in_fire
            )
        )
