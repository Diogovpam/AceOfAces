from pydantic import BaseModel

from src.entities.entities import Factions


class CreateGameRequest(BaseModel):
    game_id: str = "game1"
    player_name: str = "Diogo"
    faction: Factions


class JoinGameRequest(BaseModel):
    game_id: str = "game1"
    player_name: str = "Duda"


class SubmitMoveRequest(BaseModel):
    game_id: str = "game1"
    faction: Factions
    move_index: int
