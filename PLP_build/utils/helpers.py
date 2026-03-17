import streamlit as st


def page_style():

    st.markdown("""
    <style>

    .stApp{
    background:linear-gradient(90deg,#eef2ff,#f8fafc);
    }

    [data-testid="stSidebar"]{
    background:#1e293b;
    color:white;
    }

    </style>
    """,unsafe_allow_html=True)