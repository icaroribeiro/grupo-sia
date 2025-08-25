import streamlit as st
from src.components.business_logic import get_welcome_message
from src.components.display_components import display_header

st.set_page_config(
    page_title="Home Page",
    page_icon="🏠",
    layout="centered",
)

display_header("Welcome to Our App!")

st.write(get_welcome_message())

user_name = st.text_input("What's your name?")
if user_name:
    st.write(f"Hello, {user_name}!")

st.markdown("---")
st.info("Navigate using the sidebar to explore more features.")
