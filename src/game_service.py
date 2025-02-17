from typing import Dict
from fastapi import HTTPException
from src.entities.request_models import CreateGameRequest, JoinGameRequest, SubmitMoveRequest, SubmitLostRequest
from src.state_manager import GameStateManager, PlayerState
from src.entities.entities import PlayerInfo, Factions


class GameManager:
    def __init__(self):
        self.games: Dict[str, GameStateManager] = {}

    def create_game(self, request: CreateGameRequest):
        """ Creates a new game with one player. """
        if request.game_id in self.games:
            raise HTTPException(status_code=400, detail="Game already exists")

        player_info = PlayerInfo(player_name=request.player_name, faction=Factions[request.faction.upper()])
        self.games[request.game_id] = GameStateManager(player_info)

        return {"message": "Game created", "game_id": request.game_id}

    def list_available_games(self):
        return [game_id for game_id in self.games.keys() if self.games[game_id].opponent.name == "Opponent"]

    def join_game(self, request: JoinGameRequest):
        """ Allows an opponent to join an existing game. """
        if request.game_id not in self.games:
            raise HTTPException(status_code=404, detail="Game not found")

        game = self.games[request.game_id]

        # Ensure only one opponent joins
        if game.opponent.name != "Opponent":
            raise HTTPException(status_code=400, detail="Game is already full")

        opposing_faction = Factions.get_opposing_faction(game.player.faction)
        game.opponent = PlayerState(player_name=request.player_name, faction=opposing_faction)

        return {"message": f"{request.player_name} joined", "faction": opposing_faction.value}

    def submit_move(self, request: SubmitMoveRequest):
        """ Submits a move for a player and resolves the turn. """
        if request.game_id not in self.games:
            raise HTTPException(status_code=404, detail="Game not found")

        game = self.games[request.game_id]
        message = game.submit_move(request.faction, request.move_index)
        self._end_game(message, request.game_id)
        return message

    def submit_lost_decision(self, request: SubmitLostRequest):
        """ Submits a decision when in lost state"""
        if request.game_id not in self.games:
            raise HTTPException(status_code=404, detail="Game not found")

        game = self.games[request.game_id]
        message = game.submit_lost_state_decision(request.faction, request.decision)
        self._end_game(message, request.game_id)
        return message

    def _end_game(self, message: dict, game_id: str):
        if message.get("game_end"):
            self.games.pop(game_id)
