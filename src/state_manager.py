from src.entities.entities import PlayerInfo, STATUS_TEMPLATE, FireType, Factions
from src.page_manager import PageManager


class PlayerState:

    def __init__(self, player_name: str, faction: Factions, is_human: bool = True):
        self.name = player_name
        self.faction = faction
        self.health = 6.0
        self.is_human = is_human
        self.ai_behavior = None if is_human else "default_ai"

    def take_damage(self, amount: float):
        self.health = max(0.0, self.health - amount)

    def is_alive(self):
        return self.health > 0

    def __repr__(self):
        return f"{self.name} ({self.faction.value}) - Health: {self.health}"


class GameStateManager:

    def __init__(self, player_info: PlayerInfo):
        self.player = PlayerState(**player_info.model_dump())

        opposing_faction = Factions.get_opposing_faction(self.player.faction)

        self.opponent = PlayerState(
            player_name="Opponent",
            faction=opposing_faction
        )

        self.player_page_manager = PageManager(self.player.faction)
        self.opponent_page_manager = PageManager(opposing_faction)

        self.current_player_page = self.player_page_manager.load_page()
        self.current_opponent_page = self.opponent_page_manager.load_page()

        self.get_status()

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
