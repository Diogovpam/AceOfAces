from fastapi import FastAPI, HTTPException
from typing import Dict, Optional
import uvicorn

from src.entities.request_models import CreateGameRequest, JoinGameRequest, StartGameRequest, SubmitMoveRequest
from src.state_manager import GameStateManager
from src.entities.entities import PlayerInfo, Factions

app = FastAPI()
games: Dict[str, GameStateManager] = {}
player_moves: Dict[str, Dict[str, Optional[tuple]]] = {}


@app.post("/create-game")
def create_game(request: CreateGameRequest):
    if request.game_id in games:
        raise HTTPException(status_code=400, detail="Game already exists")

    if request.faction.lower() not in ['allies', 'german']:
        raise HTTPException(status_code=400, detail="Invalid faction")

    player_info = PlayerInfo(player_name=request.player_name, faction=Factions[request.faction.upper()])
    games[request.game_id] = GameStateManager(player_info)
    player_moves[request.game_id] = {request.player_name: None}

    return {"message": "Game created", "game_id": request.game_id}


@app.get("/list-games")
def list_games():
    return [game_id for game_id in games.keys() if len(player_moves[game_id]) < 2]


@app.post("/join-game")
def join_game(request: JoinGameRequest):
    if request.game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    game = games[request.game_id]
    if len(player_moves[request.game_id]) >= 2:
        raise HTTPException(status_code=400, detail="Game is already full")

    opposing_faction = Factions.get_opposing_faction(game.player.faction)
    player_moves[request.game_id][request.player_name] = None

    return {"message": "Player joined", "faction": opposing_faction.value}


@app.post("/start-game")
def start_game(request: StartGameRequest):
    if request.game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    if len(player_moves[request.game_id]) < 2:
        raise HTTPException(status_code=400, detail="Waiting for another player to join")

    return {"message": "Game started", "starting_page": 170}


@app.post("/submit-move")
def submit_move(request: SubmitMoveRequest):
    if request.game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")

    if request.player_name not in player_moves[request.game_id]:
        raise HTTPException(status_code=403, detail="Player not part of this game")

    player_moves[request.game_id][request.player_name] = (request.move_index, request.mid_page)

    if all(v is not None for v in player_moves[request.game_id].values()):
        return process_turn(request.game_id)

    return {"message": "Move submitted, waiting for opponent"}


def process_turn(game_id: str):
    game = games[game_id]
    p1, p2 = list(player_moves[game_id].keys())

    p1_move, p1_mid = player_moves[game_id][p1]
    p2_move, p2_mid = player_moves[game_id][p2]

    result_page = game.player_page_manager.find_result(mid_page_num=p2_mid, movement_index=p1_move)
    game.current_player_page = game.player_page_manager.load_page(page_num=result_page)
    game.current_opponent_page = game.opponent_page_manager.load_page(page_num=result_page)

    player_moves[game_id] = {p1: None, p2: None}

    return {"message": "Turn resolved", "new_page": result_page}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
