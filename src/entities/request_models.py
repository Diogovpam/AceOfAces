from pydantic import BaseModel

from src.entities.entities import Factions


class CreateGameRequest(BaseModel):
    game_id: str
    player_name: str
    faction: Factions


class JoinGameRequest(BaseModel):
    game_id: str
    player_name: str


class StartGameRequest(BaseModel):
    game_id: str


class SubmitMoveRequest(BaseModel):
    game_id: str
    faction: Factions
    move_index: int
