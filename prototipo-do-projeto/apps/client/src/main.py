import streamlit as st
from dotenv import load_dotenv
from src.components import sidebar

load_dotenv()


def main():
    # from src.display_components import display_header # if you have a global header function
    sidebar.show_sidebar()

    # Global page configuration (applies to all pages unless overridden by a specific page)
    st.set_page_config(
        page_title="My Awesome Streamlit App",
        page_icon="✨",
        layout="wide",  # or "centered"
        initial_sidebar_state="expanded",  # or "auto", "collapsed"
    )

    # You can display a global header or introduction here
    # display_header("Welcome to the Ultimate App!")
    st.title("My Awesome Streamlit App")
    st.write("👈 Select a page from the sidebar to begin.")

    # Streamlit automatically handles loading pages from the 'pages' directory.
    # You don't explicitly call them here.


if __name__ == "__main__":
    main()
