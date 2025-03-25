import time

import streamlit as st
import requests
import os
from PIL import Image
from src.entities.move_defaults import DEFAULT_MOVE_LIST

st.set_page_config(initial_sidebar_state="collapsed")

# API and file paths
API_URL = "http://localhost:8000"  # Update if necessary
PAGE_IMG_PATH = "data/page_images/{faction}/{faction}_{page_number}.jpg"
ICON_PATH = "data/icons/moves/m_{index}.jpg"

# Ensure necessary session data exists
if "game_id" not in st.session_state or "player_name" not in st.session_state or "faction" not in st.session_state:
    st.error("Missing player data! Returning to lobby.")
    st.switch_page("lobby.py")


# Fetch current page when entering the playing page
def fetch_current_page():
    response = requests.get(f"{API_URL}/get-current-page", params={"game_id": st.session_state["game_id"]})
    if response.status_code == 200:
        st.session_state["page_number"] = response.json()
    else:
        st.error("Failed to retrieve current page.")


# Fetch player status from API
def fetch_player_status():
    response = requests.get(
        f"{API_URL}/get-player-status",
        params={"game_id": st.session_state["game_id"], "player_name": st.session_state["player_name"]}
    )
    if response.status_code == 200:
        st.session_state["player_status"] = response.json()
    else:
        st.session_state["player_status"] = "Failed to retrieve status."


# Initialize current page & status if not set
if "page_number" not in st.session_state:
    fetch_current_page()
if "player_status" not in st.session_state:
    fetch_player_status()
if "last_message" not in st.session_state:
    st.session_state["last_message"] = ""


# Submit move function (stores last response message)
def submit_move(move_index):
    response = requests.post(
        f"{API_URL}/submit-move",
        json={
            "game_id": st.session_state["game_id"],
            "faction": st.session_state["faction"],
            "move_index": move_index,
        }
    )
    if response.status_code == 200:
        json_data = response.json()
        st.session_state["last_message"] = json_data.get("message", "Move processed.")

        # Save new page number only if it exists
        if "new_page" in json_data:
            st.session_state["page_number"] = json_data["new_page"]

        # Always fetch updated status
        fetch_player_status()

        # Force Streamlit to re-render and display updated page and status
        st.rerun()

    else:
        st.session_state["last_message"] = response.json().get("detail", "Error submitting move.")
        st.error(st.session_state["last_message"])


def submit_lost_decision(decision: str):
    response = requests.post(
        f"{API_URL}/submit-lost-decision",
        json={
            "game_id": st.session_state["game_id"],
            "faction": st.session_state["faction"],
            "decision": decision,
        }
    )
    if response.status_code == 200:
        data = response.json()
        st.session_state["last_message"] = data.get("message", "Decision submitted.")
        fetch_current_page()
        fetch_player_status()
        st.rerun()
    else:
        st.session_state["last_message"] = response.json().get("detail", "Error submitting decision.")
        st.error(st.session_state["last_message"])


# Apply CSS to expand width and fix word wrapping inside buttons
st.markdown(
    """
    <style>
    .block-container {
        max-width: 1300px !important;  /* Increase the width */
    }
    div.stButton > button {
        white-space: normal !important;  /* Allow buttons to wrap properly */
        width: 100% !important;  /* Make buttons expand properly */
        font-size: 10px !important; /* Ensure text is readable */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Layout: Image + Info Box Side by Side
col_img, col_info = st.columns([3, 2])  # 2:1 ratio

with col_img:
    # Load and display the current page image
    page_img_path = PAGE_IMG_PATH.format(faction=st.session_state["faction"], page_number=st.session_state["page_number"])
    if os.path.exists(page_img_path):
        st.image(Image.open(page_img_path), use_container_width=True)
    else:
        st.warning(f"Page image not found: {page_img_path}")

with col_info:
    st.subheader("Player Status")
    st.info(st.session_state["player_status"])
    st.info(st.session_state["last_message"])  # Show the latest status

if st.session_state["page_number"] == 223:
    st.subheader("You are in a lost state!")
    st.write("You must decide whether to chase your opponent or flee the scene.")

    col1, col2 = st.columns(2)
    if col1.button("🚀 Chase"):
        submit_lost_decision("chase")
    if col2.button("🏃‍♂️ Flee"):
        submit_lost_decision("flee")

else:
    st.subheader("Select Your Move")

    # Define button groups
    button_groups = [
        (DEFAULT_MOVE_LIST[0:9], [1] * 9),   # First row (9 buttons, equal width)
        (DEFAULT_MOVE_LIST[9:19], [1] * 10), # Second row (10 buttons, equal width)
        (DEFAULT_MOVE_LIST[19:26], [1] * 7)  # Third row (7 buttons, equal width)
    ]

    # Function to render movement buttons in a row
    def render_move_buttons(move_group, col_widths):
        cols = st.columns(col_widths)  # Dynamic column widths

        for idx, move in enumerate(move_group):
            move_icon_path = ICON_PATH.format(index=move.index)

            # Load the move icon if available
            if os.path.exists(move_icon_path):
                icon_img = Image.open(move_icon_path)
                cols[idx].image(icon_img, width=50)  # Display move icon
            else:
                cols[idx].write("No Icon")

            # Button with proper wrapping
            if cols[idx].button(move.name, help=move.description, key=f"move_{move.index}"):
                submit_move(move.index)


    # Render buttons with dividers
    for i, (group, widths) in enumerate(button_groups):
        render_move_buttons(group, widths)

st.markdown("### Turn Resolution")
if st.button("🔄 Refresh Game State"):
    fetch_current_page()
    fetch_player_status()
    st.rerun()
