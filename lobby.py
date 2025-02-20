import sys
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "")))

import streamlit as st
import requests
from src.entities.entities import Factions

# API base URL
API_URL = "http://localhost:8000"  # Change if necessary

st.title("Ace of Aces - Start Screen")

# Initialize session state for modals
if "show_join_modal" not in st.session_state:
    st.session_state["show_join_modal"] = False
    st.session_state["selected_game"] = None

if "show_create_modal" not in st.session_state:
    st.session_state["show_create_modal"] = False


# Fetch available games
def fetch_games():
    response = requests.get(f"{API_URL}/list-games")
    if response.status_code == 200:
        return response.json()
    return []


# Join game function
def join_game(game_id, player_name):
    response = requests.post(f"{API_URL}/join-game", json={"game_id": game_id, "player_name": player_name})
    if response.status_code == 200:
        st.session_state["game_id"] = game_id
        st.session_state["player_name"] = player_name
        st.session_state["show_join_modal"] = False  # Close modal
        st.switch_page("pages/playing_page.py")  # Redirect to playing page
    else:
        st.error(response.json().get("detail", "Error joining game"))


# Create game function
def create_game(game_id, player_name, faction):
    response = requests.post(
        f"{API_URL}/create-game",
        json={"game_id": game_id, "player_name": player_name, "faction": faction}
    )
    if response.status_code == 200:
        st.session_state["game_id"] = game_id
        st.session_state["player_name"] = player_name
        st.session_state["show_create_modal"] = False  # Close modal
        st.switch_page("pages/playing_page.py")  # Redirect to playing page
    else:
        st.error(response.json().get("detail", "Error creating game"))


# Display available games
st.subheader("Available Games")
games = fetch_games()

if games:
    for game_id in games:
        col1, col2 = st.columns([3, 1])
        col1.write(f"Game ID: {game_id}")
        if col2.button(f"Join Game", key=f"join_{game_id}"):
            st.session_state["show_join_modal"] = True
            st.session_state["selected_game"] = game_id  # Store selected game ID
else:
    st.write("No available games. Create one!")

# Create Game Button
if st.button("Create Game"):
    st.session_state["show_create_modal"] = True  # Open modal

# JOIN GAME MODAL
if st.session_state["show_join_modal"]:
    st.markdown("### Join Game")
    st.write(f"Joining Game ID: {st.session_state['selected_game']}")
    player_name = st.text_input("Enter your name:", key="join_player_name")

    col1, col2 = st.columns([1, 1])
    if col1.button("Confirm"):
        if player_name.strip():
            join_game(st.session_state["selected_game"], player_name)
        else:
            st.error("Name cannot be empty")
    if col2.button("Cancel"):
        st.session_state["show_join_modal"] = False  # Close modal

# CREATE GAME MODAL
if st.session_state["show_create_modal"]:
    st.markdown("### Create a New Game")
    new_game_id = st.text_input("Enter Game ID:", key="create_game_id")
    player_name = st.text_input("Enter your name:", key="create_player_name")
    faction = st.selectbox("Choose your faction:", [v.value for v in Factions], key="faction_choice")

    col1, col2 = st.columns([1, 1])
    if col1.button("Create"):
        if new_game_id.strip() and player_name.strip():
            create_game(new_game_id, player_name, faction)
        else:
            st.error("Game ID and Name cannot be empty")
    if col2.button("Cancel"):
        st.session_state["show_create_modal"] = False  # Close modal
