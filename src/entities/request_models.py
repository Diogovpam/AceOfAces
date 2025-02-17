from pydantic import BaseModel

from src.entities.entities import Factions, FleeDecision


class BaseRequest(BaseModel):
    game_id: str = "game1"


class RequestFaction(BaseRequest):
    faction: Factions


class CreateGameRequest(RequestFaction):
    player_name: str = "Diogo"


class JoinGameRequest(BaseRequest):
    player_name: str = "Duda"


class SubmitMoveRequest(RequestFaction):
    move_index: int


class SubmitLostRequest(RequestFaction):
    decision: FleeDecision
