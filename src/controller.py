from fastapi import FastAPI
import uvicorn
from src.game_service import GameManager
from src.entities.request_models import CreateGameRequest, JoinGameRequest, SubmitMoveRequest

app = FastAPI()
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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
