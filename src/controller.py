from fastapi import FastAPI
import uvicorn
from src.game_service import GameManager
from src.entities.request_models import CreateGameRequest, JoinGameRequest, SubmitMoveRequest, SubmitLostRequest

app = FastAPI(
    title="Ace of Aces API"
)
service = GameManager()


@app.post("/create-game")
def create_game(request: CreateGameRequest):
    return service.create_game(request)


@app.get("/list-games")
def list_games():
    return service.list_available_games()


@app.post("/join-game")
def join_game(request: JoinGameRequest):
    return service.join_game(request)


@app.post("/submit-move")
def submit_move(request: SubmitMoveRequest):
    return service.submit_move(request)


@app.post("/submit-lost-decision")
def submit_lost_decision(request: SubmitLostRequest):
    return service.submit_lost_decision(request)


@app.get("/get-current-page")
def get_current_page(game_id: str):
    return service.get_current_page(game_id)


@app.get("/get-player-status")
def get_player_status(game_id: str, player_name: str):
    return service.get_player_status(game_id, player_name)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
