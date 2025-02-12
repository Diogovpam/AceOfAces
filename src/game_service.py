from typing import Dict, Optional, List
from fastapi import HTTPException
from src.entities.request_models import CreateGameRequest, JoinGameRequest, StartGameRequest, SubmitMoveRequest
from src.state_manager import GameStateManager
from src.entities.entities import PlayerInfo, Factions


class GameManager:

    def __init__(self):
        self.games: Dict[str, List[GameStateManager, Optional[GameStateManager]]] = {}
        self.player_moves: Dict[str, List[int]]

    def create_game(self, request: CreateGameRequest):
        if request.game_id in self.games:
            raise HTTPException(status_code=400, detail="Game already exists")

        player_info = PlayerInfo(player_name=request.player_name, faction=Factions[request.faction.upper()])
        self.games.update({
            request.game_id: [GameStateManager(player_info)]
        })

        return {"message": "Game created", "game_id": request.game_id}

    def list_available_games(self):
        return [game_id for game_id in self.games.keys() if len(self.games[game_id]) == 1]

    def join_game(self, request: JoinGameRequest):
        if request.game_id not in self.games:
            raise HTTPException(status_code=404, detail="Game not found")

        game = self.games[request.game_id]
        if len(game) > 1:
            raise HTTPException(status_code=400, detail="Game is already full")

        opposing_faction = Factions.get_opposing_faction(game[0].player.faction)
        game.append(
            GameStateManager(
                player_info=PlayerInfo(
                    player_name=request.player_name,
                    faction=opposing_faction
                )
            )
        )

        return {"message": f"{request.player_name} joined", "faction": opposing_faction.value}

    def submit_move(self, request: SubmitMoveRequest):
        pass
