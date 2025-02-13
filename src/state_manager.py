from typing import Optional, Tuple

from src.entities.entities import PlayerInfo, STATUS_TEMPLATE, FireType, Factions
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
        return f"{self.name} ({self.faction.value}) - Health: {self.health}"


class GameStateManager:

    def __init__(self, player_info: PlayerInfo):
        """ Initializes the game state, tracking both players. """
        self.player = PlayerState(**player_info.model_dump())
        self.opponent = PlayerState(
            player_name="Opponent",
            faction=Factions.get_opposing_faction(self.player.faction)
        )

        self.current_player_page = self.player.page_manager.load_page()
        self.current_opponent_page = self.opponent.page_manager.load_page()

        self.null_move: Tuple[Optional[int], Optional[int]] = (None, None)

        self.moves = {self.player.faction: self.null_move, self.opponent.faction: self.null_move}

    def submit_move(self, faction: Factions, move_index: int):
        """ Stores a submitted move and processes turn if both players have submitted. """
        tailing_player, tailed_player, tailed_page = self.determine_tailing()

        if tailing_player:
            if faction == tailing_player.faction:
                # Tailing player can only submit after the tailed player
                if self.moves[tailed_player.faction] == self.null_move:
                    return {"message": "Waiting for the tailed player to move first"}

                # Get the direction of the tailed player's move
                tailed_move_index, _ = self.moves[tailed_player.faction]
                tailed_direction = tailed_page.moves[tailed_move_index].direction.value

                return {
                    "message": "Tailed player has moved. You must now choose your move.",
                    "tailed_direction": tailed_direction
                }

        if self.player.faction == faction:
            mid_page = self.current_player_page.moves[move_index].next_page
        else:
            mid_page = self.current_opponent_page.moves[move_index].next_page

        self.moves[faction] = (move_index, mid_page)

        if self.null_move not in self.moves.values():
            return self.process_turn()
        return {"message": "Move received, waiting for opponent"}

    def determine_tailing(self):
        player_is_tailing = self.current_player_page.tail
        opponent_is_tailing = self.current_opponent_page.tail

        # Identify the tailing and tailed players
        if player_is_tailing:
            tailing_player = self.player
            tailed_player = self.opponent
            tailed_page = self.current_opponent_page
        elif opponent_is_tailing:
            tailing_player = self.opponent
            tailed_player = self.player
            tailed_page = self.current_player_page
        else:
            tailing_player = None
            tailed_player = None
            tailed_page = None

        return tailing_player, tailed_player, tailed_page

    def process_turn(self):
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
        self.moves = {player_faction: (None, None), opponent_faction: (None, None)}

        # If result page is 223, enter the special state
        if result_page == 223:
            self.current_player_page = self.player.page_manager.load_page()
            self.current_opponent_page = self.opponent.page_manager.load_page()
            return {"message": "Players lost each other! Choose to chase or flee."}

        # Update player states
        self.current_player_page = self.player.page_manager.load_page(result_page)
        self.current_opponent_page = self.opponent.page_manager.load_page(result_page)

        return {"message": "Turn resolved", "new_page": result_page}

    def get_status(self):
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

    def play(self, player_movement_index: int, opp_mid_page: int) -> bool:

        if opp_mid_page == 223:

            opp_move_index = self.get_index_from_opp_mid_page(opp_mid_page)

            result_page_num = self.opponent_page_manager.find_result(
                mid_page_num=self.current_player_page.moves[player_movement_index].next_page,
                movement_index=opp_move_index
            )

        else:

            result_page_num = self.player_page_manager.find_result(
                mid_page_num=opp_mid_page,
                movement_index=player_movement_index
            )

        if result_page_num == 223:
            self.current_player_page = self.player_page_manager.load_page()
            self.current_opponent_page = self.opponent_page_manager.load_page()

            return True

        else:

            self.current_player_page = self.player_page_manager.load_page(
                page_num=result_page_num
            )

            self.current_opponent_page = self.opponent_page_manager.load_page(
                page_num=result_page_num
            )

        self.resolve_current_page(player_movement_index)

        return False

    def resolve_current_page(self, movement_index: int):
        executed_move = self.current_player_page.moves[movement_index]
        print(f"You execute a {executed_move.name.value}")
        print(executed_move.description.value)
        self.get_status()
        pass

    def get_index_from_opp_mid_page(self, mid_turn_page_num: int):
        for move in self.current_opponent_page.moves:
            return move.index if move.next_page == mid_turn_page_num else None
