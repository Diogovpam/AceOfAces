import streamlit as st

st.title("Playing Page")

st.write("Welcome to the game! This page will be implemented later.")

# Button to return to start screen
if st.button("Back to Start Screen"):
    st.switch_page("lobby.py")  # Ensure this file is correctly named
